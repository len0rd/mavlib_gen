################################################################################
# \file generator_emb_cpp
#
# Embedded-friendly C++ mavlink generator
# "Embedded-friendly" as generated files do not use any STL containers and no
# dynamic allocation
#
# Copyright (c) 2024 len0rd
#
# All rights reserved.
# This file is distributed under the terms of the MIT License.
# See the file 'LICENSE' in the root directory of the present
# distribution, or http://opensource.org/licenses/MIT.
################################################################################
from mavlib_gen.lang_generators.generator_base import AbstractLangGenerator
from pathlib import Path
from jinja2 import Environment, PackageLoader, select_autoescape
from typing import Dict
from ..model.mavlink_xml import MavlinkXmlFile, MavlinkXmlMessage, MavlinkXmlMessageField
import shutil


class EmbCppLangGenerator(AbstractLangGenerator):
    def __init__(self, use_dialect_namespaces: bool = True):
        """
        :param use_dialect_namespaces: Put Message/Payload definitions within a namespace
            that has the same name as the mavlink XML file they are contained in
        """
        self.use_dialect_namespaces = use_dialect_namespaces
        script_dir = Path(__file__).parent.resolve()
        self.template_dir = script_dir / "templates" / "emb_cpp"

    def lang_name(self) -> str:
        return "emb_cpp"

    def generate(self, validated_xmls: Dict[str, MavlinkXmlFile], output_dir: Path) -> bool:
        # TODO: move boilerplate checks up to ABC
        if validated_xmls is None or len(validated_xmls) == 0 or output_dir is None:
            return False

        output_dir.mkdir(parents=True, exist_ok=True)

        jenv = Environment(
            loader=PackageLoader("mavlib_gen", package_path=self.template_dir),
            autoescape=select_autoescape(),
            # trim whitespace thats automatically inserted for jinja template blocks
            trim_blocks=True,
            # dont automatically tab-in jinja control blocks
            lstrip_blocks=True,
        )
        msg_template = jenv.get_template("single_message.hpp.jinja")
        enum_template = jenv.get_template("dialect_enums.hpp.jinja")
        msg_list_template = jenv.get_template("dialect_msgs.hpp.jinja")

        for name, dialect in validated_xmls.items():
            dialect_inc_dir = output_dir / "inc" / dialect.get_name("lower_snake")
            dialect_inc_dir.mkdir(parents=True, exist_ok=True)

            # generate message headers
            for msg in dialect.xml.messages:
                msg_header_filename = dialect_inc_dir / f"Message{msg.get_name('UpperCamel')}.hpp"
                with open(msg_header_filename, "w") as msg_hdr:
                    msg_hdr.write(
                        msg_template.render(
                            msg=msg,
                            use_dialect_namespaces=self.use_dialect_namespaces,
                            dialect_name_lower=dialect.name.lower(),
                        )
                    )

            # generate all enums
            enums_filename = dialect_inc_dir / f"{dialect.get_name('UpperCamel')}Enums.hpp"
            with open(enums_filename, "w") as enum_hdr:
                enum_hdr.write(enum_template.render(dialect=dialect))

            # generate dialect message list header
            msg_list_filename = dialect_inc_dir / f"{dialect.get_name('UpperCamel')}Msgs.hpp"
            with open(msg_list_filename, "w") as msg_list_hdr:
                msg_list_hdr.write(msg_list_template.render(dialect=dialect))

            # copy over static source files (non-template files that are part of the library)
            static_sources = [
                "MavlinkTypes.hpp",
            ]
            for src_filename in static_sources:
                src_path = self.template_dir / src_filename
                dest_path = output_dir / "inc" / src_filename
                shutil.copyfile(src_path, dest_path)

        return True
