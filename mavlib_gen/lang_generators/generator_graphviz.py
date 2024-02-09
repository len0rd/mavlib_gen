################################################################################
# \file generator_graphviz
#
# Mavlink message graphviz diagram generator
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
from typing import Dict, Tuple, ClassVar, List
from ..model.mavlink_xml import MavlinkXmlFile, MavlinkXmlMessage, MavlinkXmlMessageField
import re
from schema import Optional, Literal
from dataclasses import dataclass


@dataclass
class GraphvizLangGenerator(AbstractLangGenerator):
    """
    MavlibGen Graphiz generator

    Attributes:
        include_framing (bool): Include MAVLink packet framing bytes in the diagram (crc, msgid, len, etc)
        include_label (bool): include a label at the top of a message diagram with the message name
    """

    # max length a field name can be in number of characters per byte/column it occupies
    # in the diagram. this dictates when a newline should be inserted in a field name
    MAX_NAME_LEN_PER_BYTE: ClassVar[int] = 13
    # colors to alternate field backgrounds so they are more easy to distinguish
    # see: https://graphviz.org/doc/info/colors.html for options
    FIELD_COLORS: ClassVar[List[str]] = ["lightgrey", "lightyellow"]
    EXTENSION_FIELD_COLORS: ClassVar[List[str]] = ["darkseagreen1", "darkseagreen"]
    TEMPLATE_DIR: ClassVar[Path] = Path(__file__).parent.resolve() / "templates" / "graphviz"

    include_framing: bool = False
    include_label: bool = True

    def lang_name(self) -> str:
        return "graphviz"

    @classmethod
    def config_schema(cls) -> Dict[any, any]:
        return {
            Optional(
                Literal(
                    "include_framing",
                    description="Set to true for generated message diagrams to"
                    + "include the MAVLink packet header bytes (msgid, len, crc, etc)",
                )
            ): bool,
            Optional(
                Literal(
                    "include_label",
                    description="Set to false to remove the message name label from generated"
                    + "message diagrams",
                )
            ): bool,
        }

    @classmethod
    def from_config(cls, conf: Dict[any, any]) -> any:
        return GraphvizLangGenerator(
            include_framing=conf.get("include_framing", cls.include_framing),
            include_label=conf.get("include_label", cls.include_label),
        )

    def __repr__(self) -> str:
        return f"GraphvizLangGenerator(include_framing: {self.include_framing}, include_label: {self.include_label})"

    def generate_table_rows(self, msg: MavlinkXmlMessage, num_cols: int) -> str:
        """
        Generate the table rows for the given fields. This could be done in Jinja,
        but is complex enough it makes more sense to do here
        """
        # each column represents 1 byte in the diagram
        clmns_available = num_cols
        if self.include_framing:
            out = ""
            clmns_available -= 2
        else:
            out = "<tr>\n"
        color = self.FIELD_COLORS[0]

        def append_field(
            field: MavlinkXmlMessageField, field_color: str, clmns_available: int
        ) -> Tuple[str, int]:
            """
            build the graphviz table string for a single message field. Handles case
            where the message field occupies more than 1 row of the diagram
            """
            field_str = ""
            # handle case where this field wraps from one row to another
            if field.field_len > clmns_available:
                unwritten_len = field.field_len

                # put the field name on the first row
                max_field_name_len_first_line = self.MAX_NAME_LEN_PER_BYTE * clmns_available
                name = field.name
                if len(name) > max_field_name_len_first_line:
                    # handle situation where field name is too long for its first-row cell
                    # allocation (add newlines)
                    name = re.sub(
                        f"(.{{{max_field_name_len_first_line}}})",
                        "\\1<br />",
                        field.name,
                        0,
                        re.DOTALL,
                    )
                field_str += (
                    f'    <td colspan="{clmns_available}"'
                    + f' align="left" bgcolor="{field_color}">{name}</td>\n'
                )

                # start the next row
                unwritten_len -= clmns_available
                field_str += "</tr>\n<tr>\n"
                clmns_available = num_cols

                while unwritten_len > 0:
                    cols_to_span = (
                        clmns_available if clmns_available < unwritten_len else unwritten_len
                    )
                    field_str += (
                        f'    <td colspan="{cols_to_span}" bgcolor="{field_color}">...</td>\n'
                    )
                    clmns_available -= cols_to_span
                    unwritten_len -= cols_to_span
                    if clmns_available == 0:
                        field_str += "</tr>\n<tr>\n"
                        clmns_available = num_cols

            else:
                # this field fits in the current row normally
                name = field.name
                max_field_name_len_per_line = self.MAX_NAME_LEN_PER_BYTE * field.field_len
                if len(name) > max_field_name_len_per_line:
                    # handle situation where field name is too long for its cell
                    # allocation (add newlines)
                    name = re.sub(
                        f"(.{{{max_field_name_len_per_line}}})",
                        "\\1<br />",
                        field.name,
                        0,
                        re.DOTALL,
                    )
                field_str += (
                    f'    <td colspan="{field.field_len}"'
                    + f' align="left" bgcolor="{field_color}">{name}</td>\n'
                )
                clmns_available -= field.field_len

            # start a new row if necessary
            if clmns_available == 0:
                field_str += "</tr>\n<tr>\n"
                clmns_available = num_cols
            return (field_str, clmns_available)

        # first append normal fields (sorted)
        for field in msg.sorted_fields:
            color = self.FIELD_COLORS[0] if color == self.FIELD_COLORS[1] else self.FIELD_COLORS[1]
            field_str, clmns_available = append_field(field, color, clmns_available)
            out += field_str

        # then append extension fields with different colors (if any)
        if len(msg.extension_fields) > 0:
            for field in msg.extension_fields:
                color = (
                    self.EXTENSION_FIELD_COLORS[0]
                    if color == self.EXTENSION_FIELD_COLORS[1]
                    else self.EXTENSION_FIELD_COLORS[1]
                )
                field_str, clmns_available = append_field(field, color, clmns_available)
                out += field_str
        if self.include_framing:
            # if framing bytes are included add crc to the very end
            crc = MavlinkXmlMessageField(
                name="crc", typename="uint16_t", description="CRC of data bytes"
            )
            field_str, clmns_available = append_field(crc, "white", clmns_available)
            out += field_str

        if out.endswith("<tr>\n"):
            # just started a new row but it will be empty which causes an error, remove it
            out = out[:-5]
        else:
            # wrap up the final row
            out += "</tr>"

        return out

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
        msg_diagram_template = jenv.get_template("single_message.dot.jinja")

        # first generate XML file include tree (if there are multiple xmls)
        if len(validated_xmls) > 1:
            include_tree_template = jenv.get_template("xml_include_tree.dot.jinja")
            include_tree_file = output_dir / "xml_include_tree.dot"
            with open(include_tree_file, "w") as inc_tree_out:
                inc_tree_out.write(include_tree_template.render(xmlfiles=validated_xmls.values()))

        for name, dialect in validated_xmls.items():
            if name.endswith(".xml"):
                name = name[:-4]

            if len(dialect.xml.messages) == 0:
                # no messages to generate for this xml file. continue before dir is made
                continue

            dialect_out_dir = output_dir / name.lower()

            dialect_out_dir.mkdir(parents=True, exist_ok=True)

            for msg in dialect.xml.messages:
                msg_filename = dialect_out_dir / f"{msg.name}.dot"
                with open(msg_filename, "w") as msg_file_out:
                    msg_file_out.write(
                        msg_diagram_template.render(
                            field_str=self.generate_table_rows(msg, 8),
                            msg=msg,
                            include_framing=self.include_framing,
                            include_label=self.include_label,
                        )
                    )

        return True
