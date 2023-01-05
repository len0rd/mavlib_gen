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
import shutil
from jinja2 import Environment, PackageLoader, select_autoescape
from typing import Dict
from ..model.mavlink_xml import MavlinkXmlFile, MavlinkXmlMessage, MavlinkXmlMessageField


# map of supported mavlink types -> python struct pack types
TYPE_TO_STRUCT_FORMAT_MAP = {
    "uint64_t": "Q",
    "int64_t": "q",
    "double": "d",
    "uint32_t": "I",
    "int32_t": "i",
    "float": "f",
    "uint16_t": "H",
    "int16_t": "h",
    "uint8_t": "B",
    "int8_t": "b",
    "char": "c",
    "uint8_t_mavlink_version": "B",
    "str": "s",  # custom type set by helper method when dealing with char array
}


def generate_field_pack_str(field: MavlinkXmlMessageField) -> str:
    """Format a single mavlink message field into a python struct.pack field"""
    struct_pack_str = ""
    field_type = field.base_type
    if field.is_array:
        struct_pack_str += f"{field.array_len}"
        if field.base_type == "char":
            field_type = "str"
    struct_pack_str += f"{TYPE_TO_STRUCT_FORMAT_MAP[field_type]}"
    return struct_pack_str


def generate_message_struct_pack_str(message: MavlinkXmlMessage) -> str:
    """
    Format a messages fields into a string that can be used by pythons struct.pack
    and struct.unpack methods
    """
    # TODO: little endian/big endian support
    struct_pack_str = "<" if message.num_fields > 0 else ""
    for field in message.all_fields_sorted:
        struct_pack_str += generate_field_pack_str(field)
    return struct_pack_str


class PythonLangGenerator(AbstractLangGenerator):
    def __init__(self, use_properties: bool = False):
        """
        :param use_properties: Use python properties in object generation instead of instance
            attributes. This means in generated message objects, fields will have get/set methods
            that can provide greater type enforcement and doc string retrieval compatibility
        """
        script_dir = os.path.dirname(__file__)
        self.template_dir = os.path.abspath(os.path.join(script_dir, "templates", "python"))
        self.use_properties = use_properties

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
            dialect_name_upper = dialect_name.upper()

            filename = f"{dialect_name_lower}_msgs.py"
            file_path = os.path.join(output_dir, filename)
            with open(file_path, "w") as msgs_file_out:
                msgs_file_out.write(
                    dialect_msgs_template.render(
                        dialect_name_lower=dialect_name_lower,
                        dialect_name_upper=dialect_name_upper,
                        messages=dialect.xml.messages,
                        use_properties=self.use_properties,
                        generate_message_struct_pack_str=generate_message_struct_pack_str,
                    )
                )

        # copy over types
        file_to_cp = "mavlink_types.py"
        mavlink_types_src = os.path.join(self.template_dir, file_to_cp)
        mavlink_types_dst = os.path.join(output_dir, file_to_cp)
        shutil.copyfile(mavlink_types_src, mavlink_types_dst)

        return True
