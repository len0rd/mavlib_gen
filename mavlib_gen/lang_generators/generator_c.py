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
from ..model.message_def_xml import MessageDefXml

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

    def generate(self, validated_xmls : Dict[str, MessageDefXml], output_dir : str) -> bool:
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

    def generate_single_xml(self, dialect : MessageDefXml, outdir : str) -> bool:

        # place generated files within a subdirectory of outdir. the subdirectory
        # is named based on the xml filename
        subdir_name = dialect.filename
        if subdir_name.endswith('.xml'):
            subdir_name = subdir_name[:-4]

        gen_dir = os.path.abspath(os.path.join(outdir, subdir_name))
        print("{} generating in {}".format(dialect.filename, gen_dir))

        if not os.path.exists(gen_dir) or not os.path.isdir(gen_dir):
            os.mkdir(gen_dir)

        xml_dict = dialect.xml_dict
        # first generate messages
        if 'messages' in xml_dict and 'message' in xml_dict['messages']:
            with open(self.msg_def_format) as mdef_format_file:
                msg_def_format = mdef_format_file.read()
                for msg_def in xml_dict['messages']['message']:
                    if not self.__generate_msg(msg_def, msg_def_format, gen_dir):
                        # generating this message header failed
                        print("msg gen failed")
                        return False

    def __generate_msg(self, msg_def : dict, formatter : str, outdir : str) -> bool:
        """
        Generate a single message using 'formatter' as the format string and placing
        the resulting output in 'outdir'
        """
        msg_name_upper = msg_def['@name'].upper()
        msg_name_lower = msg_def['@name'].lower()
        msg_id = msg_def['@id']

        if 'description' in msg_def:
            raw_desc = self.__generic_description_formatter(msg_def['description']['$'])
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
            ))

        return True

    def __generate_msg_field_strings(self, msg_def: dict) -> str:
        """generate the struct definition strings for all the fields in the message def"""

        MSG_FIELD_FORMATTER = "{field_desc}    {type} {name};"

        all_fields = ''

        if 'field' in msg_def:
            for field in msg_def['field']:
                field_desc = ''
                if '$' in field:
                    raw_field_desc = self.__generic_description_formatter(field['$'])
                    if len(raw_field_desc) > 0:
                        field_desc = self.FIELD_DOC_COMMENT_PREPEND + raw_field_desc.replace('\n', '\n' + self.FIELD_DOC_COMMENT_PREPEND) + '\n'

                field_str = MSG_FIELD_FORMATTER.format(
                    field_desc=field_desc,
                    type=field['@type'],
                    name=field['@name'],
                )
                all_fields += field_str + '\n'
            all_fields = all_fields.rstrip('\n')

        return all_fields

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
