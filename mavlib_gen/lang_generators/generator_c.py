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
import os, logging
from .generator_base import AbstractLangGenerator
from typing import Dict
from ..model.mavlink_xml import MavlinkXmlFile, MavlinkXmlMessage, MavlinkXmlMessageField

log = logging.getLogger(__name__)

class CLangGenerator(AbstractLangGenerator):

    def __init__(self):
        script_dir = os.path.dirname(__file__)
        self.template_dir = os.path.abspath(os.path.join(script_dir, 'templates', 'c'))
        self.msg_def_format = os.path.join(self.template_dir, 'message_definition.h.in')

    DOC_COMMENT_PREPEND = ' * '
    FIELD_DOC_COMMENT_PREPEND = '    /// '

    def lang_name(self) -> str:
        return 'c'

    def generate(self, validated_xmls : Dict[str, MavlinkXmlFile], output_dir : str) -> bool:
        if validated_xmls is None or len(validated_xmls) == 0 or output_dir is None:
            return False

        if not os.path.exists(output_dir) or not os.path.isdir(output_dir):
            print("create dir {}".format(output_dir))
            os.mkdir(output_dir)

        for name, dialect_def in  validated_xmls.items():
            successfully_generated = self.generate_single_xml(dialect_def, output_dir)
            if not successfully_generated:
                log.error("C lang failed to generate for dialect {}".format(name))
                return False

        return True

    def generate_single_xml(self, dialect : MavlinkXmlFile, outdir : str) -> bool:

        # place generated files within a subdirectory of outdir. the subdirectory
        # is named based on the xml filename
        subdir_name = dialect.filename
        if subdir_name.endswith('.xml'):
            subdir_name = subdir_name[:-4]

        gen_dir = os.path.abspath(os.path.join(outdir, subdir_name))
        print("{} generating in {}".format(dialect.filename, gen_dir))

        if not os.path.exists(gen_dir) or not os.path.isdir(gen_dir):
            os.mkdir(gen_dir)

        xml = dialect.xml
        # first generate messages
        if len(xml.messages) > 0:
            with open(self.msg_def_format) as mdef_format_file:
                msg_def_format = mdef_format_file.read()
                for msg_def in xml.messages:
                    if not self.__generate_msg(msg_def, msg_def_format, gen_dir):
                        # generating this message header failed
                        print("msg gen failed")
                        return False

        return True

    def __generate_msg(self, msg_def : MavlinkXmlMessage, formatter : str, outdir : str) -> bool:
        """
        Generate a single message using 'formatter' as the format string and placing
        the resulting output in 'outdir'
        """
        msg_name_upper = msg_def.name.upper()
        msg_name_lower = msg_def.name.lower()
        msg_id = msg_def.id

        if msg_def.description is not None:
            raw_desc = self.__generic_description_formatter(msg_def.description)
            formatted_msg_desc = self.DOC_COMMENT_PREPEND + raw_desc.replace('\n', '\n' + self.DOC_COMMENT_PREPEND)
        else:
            formatted_msg_desc = self.DOC_COMMENT_PREPEND + msg_name_lower + ' struct definition'

        mdef_file_out = os.path.abspath(os.path.join(outdir, 'mavlink_msg_{}.h'.format(msg_name_lower)))

        # write out the definition file
        with open(mdef_file_out, 'w') as out_file:
            out_file.write(formatter.format(
                msg_name_upper=msg_name_upper,
                msg_name_lower=msg_name_lower,
                formatted_msg_desc=formatted_msg_desc,
                msg_id=msg_id,
                struct_packed_def_start='',
                struct_packed_def_end='',
                fields=self.__generate_msg_field_strings(msg_def),
                crc_extra=msg_def.crc_extra,
                msg_len=msg_def.length
            ))

        return True

    def __generate_msg_field_strings(self, msg_def: MavlinkXmlMessage) -> str:
        """generate the struct definition strings for all the fields in the message def"""

        all_fields = ''

        if len(msg_def.sorted_fields) > 0:
            for field in msg_def.sorted_fields:
                all_fields += self.__generate_single_field_string(field) + '\n'
        if msg_def.has_extensions or len(msg_def.extension_fields) > 0:
            all_fields += "// extension fields:\n"
            for field in msg_def.extension_fields:
                all_fields += self.__generate_single_field_string(field) + '\n'

        return all_fields.rstrip('\n')

    def __generate_single_field_string(self, field : MavlinkXmlMessageField) -> str:
        """generate the definition string for a single message field"""
        MSG_FIELD_FORMATTER = "{field_desc}    {type} {name};"

        field_desc = ''
        if field.description is not None:
            raw_field_desc = self.__generic_description_formatter(field.description)
            if len(raw_field_desc) > 0:
                field_desc = self.FIELD_DOC_COMMENT_PREPEND + raw_field_desc.replace('\n', '\n' + self.FIELD_DOC_COMMENT_PREPEND) + '\n'

        field_str = MSG_FIELD_FORMATTER.format(
            field_desc=field_desc,
            type=field.type,
            name=field.name,
        )
        return field_str

    def __generic_description_formatter(self, raw_desc : str) -> str:
        """
        Perform basic/generic description formatting
        on the provided string. return the formatted string
        """
        raw_desc = raw_desc.strip()
        if raw_desc.endswith('\n'):
            raw_desc = raw_desc[:-1]
        if raw_desc.startswith('\n'):
            raw_desc = raw_desc[1:]
        return raw_desc
