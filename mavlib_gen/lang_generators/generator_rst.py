################################################################################
# \file generator_rst
#
# ReStructuredText (rst) mavlink message doc generator
#
# Copyright (c) 2024 len0rd
#
# All rights reserved.
# This file is distributed under the terms of the MIT License.
# See the file 'LICENSE' in the root directory of the present
# distribution, or http://opensource.org/licenses/MIT.
################################################################################
from mavlib_gen.lang_generators.generator_base import AbstractLangGenerator
from mavlib_gen.lang_generators.generator_graphviz import GraphvizLangGenerator
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, ClassVar, List
from mavlib_gen.model.mavlink_xml import MavlinkXmlFile
from jinja2 import Environment, PackageLoader, select_autoescape
from schema import Optional, Literal
import logging


@dataclass
class RstLangGenerator(AbstractLangGenerator):
    """
    MavlibGen RST generator

    Attributes
        include_msg_diagrams (bool): When true, generate graphviz diagrams using the Graphviz
            generator and include them in the generated docs
    """

    include_msg_diagrams: bool = False
    generate_sphinx_root: bool = False
    sphinx_project_name: str = "Mavlink Message"

    TEMPLATE_DIR: ClassVar[Path] = Path(__file__).parent.resolve() / "templates" / "rst"

    def lang_name(self) -> str:
        return "rst"

    @classmethod
    def config_schema(cls) -> Dict[any, any]:
        return {
            Optional(
                Literal(
                    "include_msg_diagrams",
                    description="Generate message diagrams and link to them in the docs using the "
                    + "'.. graphviz::' directive. Requires graphviz extension in Sphinx to render",
                )
            ): bool,
            Optional(
                Literal(
                    "generate_sphinx_root",
                    description="Generate conf.py and index.rst so the resulting docs can be "
                    + "generated by Sphinx",
                )
            ): bool,
            Optional(
                Literal(
                    "sphinx_project_name",
                    description="When generate_sphinx_root is true, use this as the project name"
                    + "in the resulting sphinx files",
                )
            ): str,
        }

    @classmethod
    def from_config(cls, conf: Dict[any, any]) -> any:
        return RstLangGenerator(
            include_msg_diagrams=conf.get("include_msg_diagrams", cls.include_msg_diagrams),
            generate_sphinx_root=conf.get("generate_sphinx_root", cls.generate_sphinx_root),
            sphinx_project_name=conf.get("sphinx_project_name", cls.sphinx_project_name),
        )

    def _generate_sphinx_specific(
        self,
        jenv: Environment,
        xml_diagram_dir: str,
        output_dir: Path,
        xmlfiles: List[MavlinkXmlFile],
    ) -> bool:
        """
        Generate sphinx-specific components. Run when @ref generate_sphinx_root is true
        """
        sphinx_conf_temp = jenv.get_template("conf.py.jinja")
        sphinx_homepage = jenv.get_template("index.rst.jinja")

        with open(output_dir / "conf.py", "w") as conf_out:
            conf_out.write(
                sphinx_conf_temp.render(
                    project_name=self.sphinx_project_name, xml_diagram_dir=xml_diagram_dir
                )
            )

        with open(output_dir / "index.rst", "w") as index_out:
            index_out.write(
                sphinx_homepage.render(
                    project_name=self.sphinx_project_name,
                    xml_diagram_dir=xml_diagram_dir,
                    xmlfiles=xmlfiles,
                )
            )
        return True

    def generate(self, validated_xmls: Dict[str, MavlinkXmlFile], output_dir: Path) -> bool:
        # TODO: move boilerplate checks up to ABC
        output_dir = Path(output_dir)
        if validated_xmls is None or len(validated_xmls) == 0 or output_dir is None:
            return False

        output_dir.mkdir(parents=True, exist_ok=True)

        jenv = Environment(
            loader=PackageLoader("mavlib_gen", package_path=self.TEMPLATE_DIR),
            autoescape=select_autoescape(),
            # trim whitespace thats automatically inserted for jinja template blocks
            trim_blocks=True,
            # dont automatically tab-in jinja control blocks
            lstrip_blocks=True,
        )
        dialect_enums_temp = jenv.get_template("dialect_enums.rst.jinja")
        dialect_msgs_temp = jenv.get_template("dialect_msgs.rst.jinja")

        diagram_subdir = "_diagram"
        if self.include_msg_diagrams:
            diagram_dir = output_dir / diagram_subdir
            graphviz_gen = GraphvizLangGenerator(include_label=True)
            if not graphviz_gen.generate(validated_xmls, diagram_dir):
                logging.error("Failed to generate diagrams for RST docs")
                return False

        # TODO: either in the index or somewhere it would be good for the docs to explain
        # MAVLink's header format, and link to their official docs to make this as much of a
        # standalone resource as possible. If it could be distributed to a message consumer/customer
        # as an ICD that would be amazing

        output_dir.mkdir(parents=True, exist_ok=True)

        if self.generate_sphinx_root:
            xml_diagram_dir = diagram_subdir if self.include_msg_diagrams else None
            if not self._generate_sphinx_specific(
                jenv, xml_diagram_dir, output_dir, validated_xmls.values()
            ):
                return False

        for name, dialect in validated_xmls.items():
            name = dialect.name

            # relative path to be used during template generation. Use 'None' in template when
            # disabled
            # TODO: not super maintainable. requires knowledge of how the graphviz generator names
            #   its files
            xml_diagram_dir = (
                f"{diagram_subdir}/{name.lower()}" if self.include_msg_diagrams else None
            )

            enums_out_filename = output_dir / f"{name}_enums.rst"
            msgs_out_filename = output_dir / f"{name}_msgs.rst"

            with open(enums_out_filename, "w") as enums_out:
                enums_out.write(
                    dialect_enums_temp.render(
                        xmlfile=dialect,
                    )
                )

            with open(msgs_out_filename, "w") as msgs_out:
                msgs_out.write(
                    dialect_msgs_temp.render(
                        xmlfile=dialect,
                        include_msg_diagrams=self.include_msg_diagrams,
                        xml_diagram_dir=xml_diagram_dir,
                    )
                )

        return True
