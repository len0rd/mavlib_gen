################################################################################
# \file generator_python
#
# Python mavlink generator
#
# Copyright (c) 2022 len0rd
#
# All rights reserved.
# This file is distributed under the terms of the MIT License.
# See the file 'LICENSE' in the root directory of the present
# distribution, or http://opensource.org/licenses/MIT.
################################################################################
from mavlib_gen.lang_generators.generator_base import AbstractLangGenerator
import os
from jinja2 import Environment, PackageLoader, select_autoescape
from typing import Dict
from ..model.mavlink_xml import MavlinkXmlFile


class PythonLangGenerator(AbstractLangGenerator):
    def __init__(self):
        script_dir = os.path.dirname(__file__)
        self.template_dir = os.path.abspath(os.path.join(script_dir, "templates", "python"))

    def lang_name(self) -> str:
        return "python"

    def generate(self, validated_xmls: Dict[str, MavlinkXmlFile], output_dir: str) -> bool:
        # TODO: move boilerplate checks up to ABC
        if validated_xmls is None or len(validated_xmls) == 0 or output_dir is None:
            return False

        if not os.path.exists(output_dir) or not os.path.isdir(output_dir):
            print("create dir {}".format(output_dir))
            os.mkdir(output_dir)

        jenv = Environment(
            loader=PackageLoader(
                "mavlib_gen", package_path=os.path.join("lang_generators", "templates", "python")
            ),
            autoescape=select_autoescape(),
            # trim whitespace thats automatically inserted for jinja template blocks
            trim_blocks=True,
            # dont automatically tab-in jinja control blocks
            lstrip_blocks=True,
        )
        dialect_msgs_template = jenv.get_template("dialect_msgs.py.jinja")

        for name, dialect in validated_xmls.items():
            dialect_name = dialect.filename
            if dialect_name.endswith(".xml"):
                dialect_name = dialect_name[:-4]

            dialect_name_lower = dialect_name.lower()

            filename = f"{dialect_name_lower}_msgs.py"
            file_path = os.path.join(output_dir, filename)
            with open(file_path, "w") as msgs_file_out:
                msgs_file_out.write(
                    dialect_msgs_template.render(
                        dialect_name=dialect_name_lower, messages=dialect.xml.messages
                    )
                )
