################################################################################
# \file validator
#
# Methods and helpers for ensuring XML files are valid Mavlink message
# definitions
#
# Copyright (c) 2021 len0rd
#
# All rights reserved.
# This file is distributed under the terms of the MIT License.
# See the file 'LICENSE' in the root directory of the present
# distribution, or http://opensource.org/licenses/MIT.
#################################################################################
import os, logging, re
import xmlschema
from xml.etree import ElementTree
import networkx as netx
from .model.message_def_xml import MessageDefXml
from typing import List

# return codes from MavlinkXmlValidator.is_msg_def_unique
MSG_DEF_UNIQUE = 1
MSG_DEF_DUPLICATE = 0
MSG_DEF_DUPLICATE_ERR = -1

log = logging.getLogger(__name__)

class MavlinkXmlValidator(object):

    def __init__(self):
        script_dir = os.path.dirname(__file__)
        base_url = os.path.abspath(os.path.join(script_dir, 'schema'))
        self.schema = xmlschema.XMLSchema11(os.path.join(base_url, 'mavlink_schema.xsd'), base_url=base_url)

    def validate_single_xml(self, xml_filename : str):
        """
        Validate an individual xml.
        TODO: validation needs to be performed on combined/included xmls (no msgid conflicts, etc)
        """
        if not os.path.isfile(xml_filename):
            log.error("Unable to locate '{}'".format(xml_filename))
            return None

        # attempt to read the xml directly into a dictionary
        try:
            xml_dict = self.schema.to_dict(xml_filename)
        except ElementTree.ParseError as parseErr:
            log.error("Failed to parse '{}': {}".format(os.path.relpath(xml_filename), parseErr))
            return None
        except xmlschema.validators.exceptions.XMLSchemaValidationError as xsve:
            self.report_schama_validation_error(xsve, xml_filename)
            return None
        log.debug("{} passed validation".format(xml_filename))
        return MessageDefXml(os.path.abspath(xml_filename), xml_dict)

    def report_schama_validation_error(self, validation_exception, xml_filename):
        """Helper method to report validation errors in a useful way that I like"""
        log.error("Validation of message definition file '{}' failed!".format(os.path.relpath(xml_filename)))
        reason = ""
        if validation_exception.reason is not None:
            reason += "Reason: {}".format(validation_exception.reason)
        if validation_exception.path is not None:
            reason += " At path '{}':".format(validation_exception.path)
        log.error(reason)
        if xmlschema.etree.is_etree_element(validation_exception.elem):
            log.error("\n{}".format(xmlschema.etree.etree_tostring(validation_exception.elem, validation_exception.namespaces, '', 5)))

    def is_msg_def_unique(self, msg_def : MessageDefXml, other_msg_defs : List[MessageDefXml]) -> int:
        """
        Check that 'msg_def' is unique to the definitions in 'other_msg_defs'
        """
        for mdef_b in other_msg_defs:
            if mdef_b.filename == msg_def.filename:
                if mdef_b.absolute_path != msg_def.absolute_path:
                    log.error("Non-identical include paths for message definition file '{}' ('{}' vs '{}')".format(
                        mdef_b.filename, mdef_b.absolute_path, msg_def.absolute_path))
                    return MSG_DEF_DUPLICATE_ERR
                return MSG_DEF_DUPLICATE
        return MSG_DEF_UNIQUE

    def expand_includes(self, validated_xmls : List[MessageDefXml]) -> List[MessageDefXml]:
        """
        Expand the includes of each message definition xml in validated_xmls.
        This method has a number of responsibilities:
        - ensure no duplicates are added to the validated_xmls list
        - validate the schema of all included message definition xmls
        - Ensure valid include paths (no circular dependencies)
        Note: The schema has a constraint which ensures include tag contents are unique within a definition file
        """
        # Use a Directed Acyclic Graph (DAG) to ensure valid include tree
        # with definitions <include> tags (no circular dependencies)
        include_graph = netx.DiGraph()

        input_xml_len = len(validated_xmls)
        # ensure we only iterate and expand on the xmls provided in the initial parameter
        for ii in range(0, input_xml_len):
            if 'include' in validated_xmls[ii].xml_dict:
                for include_path in validated_xmls[ii].xml_dict['include']:
                    # per the mavlink schema definition, include tags are relative to the dialect file they are contained in
                    # NOTE: include_path is split on unix or windows path separator to ensure the abs_include_path generated
                    #       works for the current os
                    split_include_path = re.split('[\\\/]', include_path)
                    abs_include_path = os.path.join(os.path.dirname(validated_xmls[ii].absolute_path), *split_include_path)
                    if not os.path.isfile(abs_include_path):
                        log.error("Failed to resolve include '{}' in definition '{}' to a file".format(include_path, validated_xmls[ii].filename))
                        log.debug("  Expected absolute path that doesnt exist: '{}'".format(abs_include_path))
                        return None

                    # make a simple MessageDefXml to run a duplicate check with the current list
                    dup_check_def = MessageDefXml(abs_include_path, {})
                    uniqueness_result = self.is_msg_def_unique(dup_check_def, validated_xmls)
                    if uniqueness_result == MSG_DEF_DUPLICATE_ERR:
                        log.error("Second non-identical include path originated from '{}' include tag in '{}'".format(include_path, validated_xmls[ii].filename))
                        return None
                    elif uniqueness_result == MSG_DEF_DUPLICATE:
                        # This file has already been validated and added to the validated_xmls list.
                        # All thats left to do is add the edge/relationship to the DAG (which is done below)
                        pass
                    elif uniqueness_result == MSG_DEF_UNIQUE:
                        print("its unique")
                        # TODO: validate the xml schema, append to validated_xmls

                    else:
                        raise ValueError("Unknown result {} from validator.is_msg_def_unique".format(uniqueness_result))

                    include_graph.add_edges_from([(validated_xmls[ii].filename, dup_check_def.filename)])

                    # confirm the DAG is still directed and acyclic (to circular dependencies) before proceeding
                    if (not netx.is_directed(include_graph)) or (not netx.is_directed_acyclic_graph(include_graph)):
                        log.error("Circular dependency detected involving '{}' and its included dialect '{}'".format(validated_xmls[ii].filename, dup_check_def.filename))

        return validated_xmls

    def validate(self, xmls : List[str]) -> List[MessageDefXml]:
        """
        Validate the provided list of xmls
        """

        # first validate and load up all the xml files specified in the input parameter
        validated_xmls = []
        for xml_filename in xmls:
            valid_msg_def = self.validate_single_xml(xml_filename)
            if valid_msg_def is None:
                return None

            uniqueness_result = self.is_msg_def_unique(valid_msg_def, validated_xmls)
            if uniqueness_result == MSG_DEF_UNIQUE:
                validated_xmls.append(valid_msg_def)
            elif uniqueness_result == MSG_DEF_DUPLICATE_ERR:
                return None
            elif uniqueness_result == MSG_DEF_DUPLICATE:
                pass
            else:
                raise ValueError("Unknown result {} from validator.is_msg_def_unique".format(uniqueness_result))

            # otherwise, its a duplicate and is already in the validated_xmls list

        # now expand the includes of all the current validated xmls and verify the include tree
        validated_xmls = self.expand_includes(validated_xmls)

        return validated_xmls
