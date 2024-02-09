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
from pathlib import Path
import shutil
from jinja2 import Environment, PackageLoader, select_autoescape
from typing import Dict, ClassVar
from ..model.mavlink_xml import MavlinkXmlFile, MavlinkXmlMessage, MavlinkXmlMessageField
from schema import Optional, Literal
from dataclasses import dataclass

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


@dataclass
class PythonLangGenerator(AbstractLangGenerator):
    """
    MavlibGen Python generator

    Attributes:
        use_properties (bool): Use python properties in object generation instead of instance
            attributes. This means in generated message objects, fields will have get/set methods
            that can provide greater type enforcement and doc string retrieval compatibility
    """

    TEMPLATE_DIR: ClassVar[Path] = Path(__file__).parent.resolve() / "templates" / "python"

    use_properties: bool = False

    def lang_name(self) -> str:
        return "python"

    @classmethod
    def config_schema(cls) -> Dict[any, any]:
        return {
            Optional(
                Literal(
                    "use_properties",
                    description="Use python properties for all fields for improved documentation",
                )
            ): bool,
        }

    @classmethod
    def from_config(cls, conf: Dict[any, any]) -> any:
        return PythonLangGenerator(use_properties=conf.get("use_properties", cls.use_properties))

    def __repr__(self) -> str:
        return f"PythonLangGenerator(use_properties: {self.use_properties})"

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
        dialect_msgs_template = jenv.get_template("dialect_msgs.py.jinja")

        for name, dialect in validated_xmls.items():
            dialect_name = dialect.filename
            if dialect_name.endswith(".xml"):
                dialect_name = dialect_name[:-4]

            dialect_name_lower = dialect_name.lower()
            dialect_name_upper = dialect_name.upper()

            file_path = output_dir / f"{dialect_name_lower}_msgs.py"
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
        mavlink_types_src = self.TEMPLATE_DIR / file_to_cp
        mavlink_types_dst = output_dir / file_to_cp
        shutil.copyfile(mavlink_types_src, mavlink_types_dst)

        return True
