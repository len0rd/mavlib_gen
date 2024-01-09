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
import os
from jinja2 import Environment, PackageLoader, select_autoescape
from typing import Dict, List, Tuple
from ..model.mavlink_xml import MavlinkXmlFile, MavlinkXmlMessage, MavlinkXmlMessageField
import re


class GraphvizLangGenerator(AbstractLangGenerator):
    # max length a field name can be in number of characters per byte/column it occupies
    # in the diagram. this dictates when a newline should be inserted in a field name
    MAX_NAME_LEN_PER_BYTE = 13
    # colors to alternate field backgrounds so they are more easy to distinguish
    # see: https://graphviz.org/doc/info/colors.html for options
    FIELD_COLORS = ["lightgrey", "lightyellow"]
    EXTENSION_FIELD_COLORS = ["darkseagreen1", "darkseagreen"]

    def __init__(self, include_framing=False, include_label=True):
        """
        :param include_framing: Include MAVLink packet framing bytes in the diagram
            (crc, msgid, len, etc)
        :param include_label: include a label at the top of a message diagram with the
            message name
        """
        self.include_framing = include_framing
        self.include_label = include_label
        script_dir = os.path.dirname(__file__)
        self.template_dir = os.path.abspath(os.path.join(script_dir, "templates", "graphviz"))

    def lang_name(self) -> str:
        return "graphviz"

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
                        f"(.{{{max_field_name_len_per_line}}})",
                        "\\1<br />",
                        field.name,
                        0,
                        re.DOTALL,
                    )
                field_str += f'    <td colspan="{clmns_available}" align="left" bgcolor="{field_color}">{name}</td>\n'

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
                field_str += f'    <td colspan="{field.field_len}" align="left" bgcolor="{field_color}">{name}</td>\n'
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
        # TODO: handle adding CRC
        # if self.include_framing:
        #     field_str, clmns_available = append_field("")

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

        if out.endswith("<tr>\n"):
            # just started a new row but it will be empty which causes an error, remove it
            out = out[:-5]
        else:
            # wrap up the final row
            out += "</tr>"

        return out

    def generate(self, validated_xmls: Dict[str, MavlinkXmlFile], output_dir: str) -> bool:
        # TODO: move boilerplate checks up to ABC
        if validated_xmls is None or len(validated_xmls) == 0 or output_dir is None:
            return False

        if not os.path.exists(output_dir) or not os.path.isdir(output_dir):
            print("create dir {}".format(output_dir))
            os.mkdir(output_dir)

        jenv = Environment(
            loader=PackageLoader("mavlib_gen", package_path=self.template_dir),
            autoescape=select_autoescape(),
            # trim whitespace thats automatically inserted for jinja template blocks
            trim_blocks=True,
            # dont automatically tab-in jinja control blocks
            lstrip_blocks=True,
        )
        msg_diagram_template = jenv.get_template("single_message.dot.jinja")

        for name, dialect in validated_xmls.items():
            if name.endswith(".xml"):
                name = name[:-4]

            dialect_out_dir = os.path.join(output_dir, name.lower())

            if not os.path.exists(dialect_out_dir) or not os.path.isdir(dialect_out_dir):
                os.mkdir(dialect_out_dir)

            for msg in dialect.xml.messages:
                msg_filename = os.path.join(dialect_out_dir, f"{msg.name}.dot")
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
