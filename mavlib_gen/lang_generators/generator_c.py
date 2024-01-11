################################################################################
# \file generator_c
#
# C mavlink generator
#
# Copyright (c) 2021 len0rd
#
# All rights reserved.
# This file is distributed under the terms of the MIT License.
# See the file 'LICENSE' in the root directory of the present
# distribution, or http://opensource.org/licenses/MIT.
################################################################################
from pathlib import Path
import logging
import re
from .generator_base import AbstractLangGenerator
from typing import Dict, List
from ..model.mavlink_xml import (
    MavlinkXmlFile,
    MavlinkXmlMessage,
    MavlinkXmlMessageField,
    MavlinkXmlEnum,
    MavlinkXmlEnumEntry,
)

log = logging.getLogger(__name__)


class CLangGenerator(AbstractLangGenerator):
    def __init__(self):
        self.template_dir = Path(__file__).parent.resolve() / "templates" / "c"
        self.msg_def_format = self.template_dir / "message_definition.h.in"

    DOC_COMMENT_PREPEND = " * "
    # number of spaces that comprise a standard indent
    STANDARD_INDENT_SIZE = 4
    DOC_COMMENT_PREPEND2 = "/// "
    MSG_DEF_FILENAME_FORMAT = "mavlink_msg_{}.h"

    def lang_name(self) -> str:
        return "c"

    def generate(self, validated_xmls: Dict[str, MavlinkXmlFile], output_dir: Path) -> bool:
        output_dir = Path(output_dir)
        if validated_xmls is None or len(validated_xmls) == 0 or output_dir is None:
            return False

        output_dir.mkdir(parents=True, exist_ok=True)

        for name, dialect_def in validated_xmls.items():
            successfully_generated = self.generate_single_xml(dialect_def, output_dir)
            if not successfully_generated:
                log.error("C lang failed to generate for dialect {}".format(name))
                return False

        return True

    def generate_single_xml(self, dialect: MavlinkXmlFile, outdir: Path) -> bool:
        # place generated files within a subdirectory of outdir. the subdirectory
        # is named based on the xml filename
        dialect_name = dialect.filename
        if dialect_name.endswith(".xml"):
            dialect_name = dialect_name[:-4]

        dialect_name_lower = dialect_name.lower()

        gen_dir = outdir / dialect_name_lower
        print("{} generating in {}".format(dialect.filename, gen_dir))

        gen_dir.mkdir(parents=True, exist_ok=True)

        xml = dialect.xml
        # first generate messages
        if len(xml.messages) > 0:
            with open(self.msg_def_format, "r") as mdef_format_file:
                msg_def_format = mdef_format_file.read()
                for msg_def in xml.messages:
                    if not self.__generate_msg(msg_def, msg_def_format, gen_dir):
                        # generating this message header failed
                        log.error(
                            "Failed to generate C header for message: '{}'. Exiting".format(
                                msg_def.name
                            )
                        )
                        return False

            self.__generate_xml_msg_include(dialect_name_lower, xml.messages, gen_dir)
            self.__generate_enums(xml.enums, gen_dir, dialect_name_lower)

        return True

    def __generate_xml_msg_include(
        self, dialect_name_lower: str, msgs: List[MavlinkXmlMessage], outdir: Path
    ) -> None:
        """
        Generates the dialects message include file. This header is simply
        a collection of include statements for all messages in the dialect
        """
        dialect_msg_include_format = self.template_dir / "dialect_msgs.h.in"

        # generate an include string for each message
        msg_c_includes = []
        for msg_def in msgs:
            msg_c_includes.append(
                '#include "./{msg_filename}'.format(
                    msg_filename=self.MSG_DEF_FILENAME_FORMAT.format(msg_def.name.lower())
                )
            )

        # generate the XMLs message include. This .h includes all messages in this dialect ONLY
        include_string_out = "\n".join([msg_inc for msg_inc in msg_c_includes])
        dialect_msgs_file_out = outdir / "{}_msgs.h".format(dialect_name_lower)

        with open(dialect_msg_include_format, "r") as dialect_msgs_format_file:
            formatter = dialect_msgs_format_file.read()
            with open(dialect_msgs_file_out, "w") as dialect_msgs_out:
                dialect_msgs_out.write(
                    formatter.format(
                        dialect_name_lower=dialect_name_lower,
                        dialect_name_upper=dialect_name_lower.upper(),
                        dialect_msg_includes=include_string_out,
                    )
                )

    def __generate_msg(self, msg_def: MavlinkXmlMessage, formatter: str, outdir: Path) -> bool:
        """
        Generate a single message using 'formatter' as the format string and placing
        the resulting output in 'outdir'
        """
        msg_name_upper = msg_def.name.upper()
        msg_name_lower = msg_def.name.lower()
        msg_id = msg_def.id

        if msg_def.description is not None:
            raw_desc = self.__generic_description_formatter(msg_def.description)
            formatted_msg_desc = self.DOC_COMMENT_PREPEND + raw_desc.replace(
                "\n", "\n" + self.DOC_COMMENT_PREPEND
            )
        else:
            formatted_msg_desc = self.DOC_COMMENT_PREPEND + msg_name_lower + " struct definition"

        mdef_file_out = outdir / self.MSG_DEF_FILENAME_FORMAT.format(msg_name_lower)

        # write out the definition file
        with open(mdef_file_out, "w") as out_file:
            out_file.write(
                formatter.format(
                    msg_name_upper=msg_name_upper,
                    msg_name_lower=msg_name_lower,
                    formatted_msg_desc=formatted_msg_desc,
                    msg_id=msg_id,
                    struct_packed_def_start="",
                    struct_packed_def_end="",
                    fields=self.__generate_msg_field_strings(msg_def),
                    crc_extra=msg_def.crc_extra,
                    msg_len=msg_def.byte_length,
                )
            )

        return True

    def __generate_msg_field_strings(self, msg_def: MavlinkXmlMessage) -> str:
        """generate the struct definition strings for all the fields in the message def"""

        all_fields = ""

        if len(msg_def.sorted_fields) > 0:
            for field in msg_def.sorted_fields:
                all_fields += self.__generate_single_field_string(field) + "\n"
        if msg_def.has_extensions or len(msg_def.extension_fields) > 0:
            all_fields += "    // extension fields:\n"
            for field in msg_def.extension_fields:
                all_fields += self.__generate_single_field_string(field) + "\n"

        return all_fields.rstrip("\n")

    def __generate_single_field_string(self, field: MavlinkXmlMessageField) -> str:
        """generate the definition string for a single message field"""
        MSG_FIELD_FORMATTER = "{field_desc}    {type} {name};"

        field_str = MSG_FIELD_FORMATTER.format(
            field_desc=self.__doc_comment_formatter(field.description, 1),
            type=field.type,
            name=field.name,
        )
        return field_str

    def __doc_comment_formatter(self, raw_desc: str, num_indents: int) -> str:
        """
        Make a doc comment description string with the provided raw value and indented num_indents
        times
        """
        if raw_desc is None:
            return ""
        out = self.__generic_description_formatter(raw_desc)
        # remove extra whitespace that is introduced from the tag value being indented
        out = re.sub(r"\n *", "\n", out)
        if len(out) > 0:
            doc_prepend = (
                " " * (self.STANDARD_INDENT_SIZE * num_indents)
            ) + self.DOC_COMMENT_PREPEND2
            out = doc_prepend + out.replace("\n", "\n" + doc_prepend) + "\n"
        return out

    def __generic_description_formatter(self, raw_desc: str) -> str:
        """
        Perform basic/generic description formatting
        on the provided string. return the formatted string
        """
        raw_desc = raw_desc.strip()
        if raw_desc.endswith("\n"):
            raw_desc = raw_desc[:-1]
        if raw_desc.startswith("\n"):
            raw_desc = raw_desc[1:]
        return raw_desc

    def __generate_enums(
        self, enums: List[MavlinkXmlEnum], outdir: Path, dialect_name_lower: str
    ) -> bool:
        """
        Generate all enums for a single dialect into a header file
        """
        ENUM_FORMATTER = "{doc_string}typedef enum {enum_name}_t {{\n{enum_entries}\n}};\n"
        dialect_enums_format = self.template_dir / "dialect_enums.h.in"
        dialect_enums_file_out = outdir / "{}_enums.h".format(dialect_name_lower)

        all_enums = ""

        for enum in enums:
            entry_strs = ""
            for enum_entry in enum.entries:
                entry_strs += self.__generate_enum_entry(enum_entry)
            enum_str = ENUM_FORMATTER.format(
                doc_string=self.__doc_comment_formatter(enum.description, 0),
                enum_name=enum.name,
                enum_entries=entry_strs,
            )
            all_enums += enum_str

        with open(dialect_enums_format, "r") as dialect_enums_format_file:
            formatter = dialect_enums_format_file.read()
            with open(dialect_enums_file_out, "w") as dialect_enums_out:
                dialect_enums_out.write(
                    formatter.format(
                        dialect_name_lower=dialect_name_lower,
                        dialect_name_upper=dialect_name_lower.upper(),
                        all_enums=all_enums,
                    )
                )

    def __generate_enum_entry(self, enum_entry: MavlinkXmlEnumEntry) -> str:
        """Generate the C enum entry string for a single enum entry"""
        ENUM_ENTRY_FORMATTER = (
            "{doc_string}" + (" " * self.STANDARD_INDENT_SIZE) + "{entry_name} = {value},\n"
        )

        doc_string = enum_entry.description
        doc_string = doc_string.strip()
        if len(enum_entry.params) > 0:
            if not doc_string.endswith("\n"):
                doc_string += "\n"
            doc_string += "Param Values:\n"
            for param in enum_entry.params:
                doc_string += param.doc_string(self.STANDARD_INDENT_SIZE) + "\n"

        return ENUM_ENTRY_FORMATTER.format(
            doc_string=self.__doc_comment_formatter(doc_string, 1),
            entry_name=enum_entry.name,
            value=enum_entry.value,
        )
