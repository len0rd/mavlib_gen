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
import os
import logging
import re
import xmlschema
from xml.etree import ElementTree
import networkx as netx
from .model.mavlink_xml import MavlinkXmlFile, MavlinkXml
from typing import List, Dict
from abc import ABC, abstractmethod

# return codes from MavlinkXmlValidator.is_msg_def_unique
MSG_DEF_UNIQUE = 1
MSG_DEF_DUPLICATE = 0
MSG_DEF_DUPLICATE_ERR = -1

log = logging.getLogger(__name__)


class AbstractXmlValidator(ABC):
    """
    Abstract base class for an XML Validator that can be extended by 3rd parties
    to insert custom validation logic into the mavlink generation process
    """

    @abstractmethod
    def validate(self, xmls : Dict[str, MavlinkXmlFile], include_graph : netx.DiGraph) -> bool:
        """
        Run the custom validator, return True if the xmls pass your validation
        rules, otherwise False

        Note: for your custom validator to be run, you must add it to the run list
            via @ref MavlinkXmlValidator.add_custom_validator
        """
        pass


class UniqueMsgIdNameAcrossDependencies(AbstractXmlValidator):
    """
    Verify all message ids and names are unique across an XML + its dependencies
    Note: unique message ids are verified on a per-xml basis by the schema
    @ref MavlinkXmlValidator adds and runs this validator automatically
    """

    def validate(self, msg_defs : Dict[str, MavlinkXmlFile], include_graph : netx.DiGraph) -> bool:
        # for each xml
        for fname, mdef in msg_defs.items():
            processed = []  # keep a list of the dialect names processed for better error reporting
            if mdef.dependencies is None:
                # no dependencies for this xml to check against
                continue
            if len(mdef.xml.messages) > 0:
                base_msgid_set = {msg.id for msg in mdef.xml.messages}
                base_msgname_set = {msg.name for msg in mdef.xml.messages}
            else:
                base_msgid_set = set()
                base_msgname_set = set()
            processed.append(fname)
            for dep in mdef.dependencies:
                dependency_xml_file = msg_defs[dep]
                if len(dependency_xml_file.xml.messages) > 0:
                    dep_msgid_set = {msg.id for msg in dependency_xml_file.xml.messages}
                    dep_msgname_set = {msg.name for msg in dependency_xml_file.xml.messages}
                else:
                    # this dependency has no messages/msg_ids, good to continue
                    continue
                # check for id or name intersections
                conflicting_ids = base_msgid_set.intersection(dep_msgid_set)
                if len(conflicting_ids) > 0:
                    log.error("One of '{}'s dependencies has a conflicting message id with one of its other "
                        "dependencies (or with '{}' itself)".format(fname, fname))
                    log.error("Conflicting id(s): {}. This conflict can be found in {} and one of the following: {}"
                        .format(conflicting_ids, dependency_xml_file.filename, processed))
                    return False
                conflicting_names = base_msgname_set.intersection(dep_msgname_set)
                if len(conflicting_names) > 0:
                    log.error("One of '{}'s dependencies has a conflicting message name with one of its other "
                        "dependencies (or with '{}' itself)".format(fname, fname))
                    log.error("Conflicting name(s): {}. This conflict can be found in {} and one of the following: {}"
                        .format(conflicting_names, dependency_xml_file.filename, processed))
                    return False
                # otherwise, no conflicts
                base_msgid_set.update(dep_msgid_set)
                base_msgname_set.update(dep_msgname_set)

                processed.append(dependency_xml_file.filename)
        return True


class MavlinkXmlValidator(object):
    """
    Main class used to read in XMLs, verify they adhere to the mavlink schema and
    expand their includes
    """

    def __init__(self):
        script_dir = os.path.dirname(__file__)
        base_url = os.path.abspath(os.path.join(script_dir, 'schema'))
        self.schema = xmlschema.XMLSchema11(os.path.join(base_url, 'mavlink_schema.xsd'),
            base_url=base_url, converter=xmlschema.DataElementConverter)
        self.custom_validators = []
        self.msgid_name_validator = UniqueMsgIdNameAcrossDependencies()
        self.custom_validators.append(self.msgid_name_validator)

    def add_validator(self, custom_validator : AbstractXmlValidator) -> None:
        """Add a custom validator to the list of validators to be run when @ref validate is called"""
        self.custom_validators.append(custom_validator)

    def validate_single_xml(self, xml_filename : str) -> MavlinkXmlFile:
        """
        Validate an individual xml.
        TODO: validation needs to be performed on combined/included xmls (no msgid conflicts, etc)
        """
        if not os.path.isfile(xml_filename):
            log.error("Unable to locate '{}'".format(xml_filename))
            return None

        # attempt to read the xml directly into a dictionary
        try:
            xml_elem = self.schema.decode(xml_filename)
            # translate into our model objects
            # TODO: take care of this at the converter level so we dont need intermediate xml_elem
            xml_model = MavlinkXml(xml_elem)
        except ElementTree.ParseError as parseErr:
            log.error("Failed to parse '{}': {}".format(os.path.relpath(xml_filename), parseErr))
            return None
        except xmlschema.validators.exceptions.XMLSchemaValidationError as xsve:
            self.__report_schama_validation_error(xsve, xml_filename)
            return None
        log.debug("{} passed validation".format(xml_filename))
        return MavlinkXmlFile(os.path.abspath(xml_filename), xml_model)

    def __report_schama_validation_error(self, xsve : xmlschema.validators.exceptions.XMLSchemaValidationError,
            xml_filename : str) -> None:
        """Helper method to report validation errors in a useful way that I like"""
        log.error("Validation of message definition file '{}' failed!".format(os.path.relpath(xml_filename)))
        reason = ""
        if xsve.reason is not None:
            reason += "Reason: {}".format(xsve.reason)
        if xsve.path is not None:
            reason += " At path '{}':".format(xsve.path)
        log.error(reason)
        if xmlschema.etree.is_etree_element(xsve.elem):
            log.error("\n{}".format(xmlschema.etree.etree_tostring(
                xsve.elem, xsve.namespaces, '', 5)))

    def is_msg_def_unique(self, msg_def : MavlinkXmlFile, other_msg_defs : Dict[str, MavlinkXmlFile]) -> int:
        """
        Check that 'msg_def' is unique to the definitions in 'other_msg_defs'
        Since the dialect filename is used in generation to name other files, we cannot allow two different
        msg defs to have the same name
        """
        if msg_def.filename in other_msg_defs:
            if msg_def.absolute_path != other_msg_defs[msg_def.filename].absolute_path:
                log.error("Non-identical include paths for message definition file '{}' ('{}' vs '{}')".format(
                    other_msg_defs[msg_def.filename].filename, other_msg_defs[msg_def.filename].absolute_path,
                    msg_def.absolute_path))
                return MSG_DEF_DUPLICATE_ERR
            return MSG_DEF_DUPLICATE
        return MSG_DEF_UNIQUE

    def expand_includes(self, validated_xmls : Dict[str, MavlinkXmlFile]) -> (Dict[str, MavlinkXmlFile], netx.DiGraph):
        """
        Expand the includes of each message definition xml in validated_xmls.
        This method has a number of responsibilities:
        - ensure no duplicates are added to the validated_xmls dict
        - validate the schema of all included message definition xmls (using @ref validate_single_xml)
        - Ensure valid include tree (no circular dependencies)
        Note: The schema has a constraint which ensures include tag contents are unique within a definition file
        """
        # Use a Directed Acyclic Graph (DAG) to ensure valid include tree
        # with definitions <include> tags (no circular dependencies)
        include_graph = netx.DiGraph()

        xmls_to_expand = list(validated_xmls.keys())
        # ensure we only iterate and expand on the xmls provided in the initial parameter
        while len(xmls_to_expand) > 0:
            current_xmls_to_expand = xmls_to_expand
            xmls_to_expand = []
            for cur_dialect in current_xmls_to_expand:
                log.debug("Expanding includes in dialect {}".format(cur_dialect))
                if len(validated_xmls[cur_dialect].xml.includes) == 0:
                    # add the xml to the graph (becomes important later when analyzing dependencies for generation)
                    include_graph.add_node(validated_xmls[cur_dialect].filename)
                else:
                    for include_path in validated_xmls[cur_dialect].xml.includes:
                        # per the mavlink schema definition, include tags are relative to the dialect file
                        # they are contained in
                        # NOTE: include_path is split on unix or windows path separator to ensure the
                        #       abs_include_path generated works for the current os
                        split_include_path = re.split(r'[\\\/]', include_path)
                        abs_include_path = os.path.abspath(
                            os.path.join(os.path.dirname(validated_xmls[cur_dialect].absolute_path),
                                *split_include_path))
                        if not os.path.isfile(abs_include_path):
                            log.error("Failed to resolve include '{}' in definition "
                                "'{}' to a file".format(include_path, cur_dialect))
                            log.debug("  Expected absolute path that doesnt exist: '{}'".format(abs_include_path))
                            return None

                        # make a barebones MavlinkXmlFile to run a duplicate check with the current list
                        dup_check_def = MavlinkXmlFile(abs_include_path, {})
                        uniqueness_result = self.is_msg_def_unique(dup_check_def, validated_xmls)
                        if uniqueness_result == MSG_DEF_DUPLICATE_ERR:
                            log.error("Second non-identical include path originated from '{}' include"
                                " tag in '{}'".format(include_path, cur_dialect))
                            return None
                        elif uniqueness_result == MSG_DEF_DUPLICATE:
                            # This file has already been validated and added to the validated_xmls list.
                            # All thats left to do is add the edge/relationship to the DAG (which is done below)
                            pass
                        elif uniqueness_result == MSG_DEF_UNIQUE:
                            validated_xml = self.validate_single_xml(abs_include_path)
                            if validated_xml is None:
                                return None
                            validated_xmls[validated_xml.filename] = validated_xml
                            xmls_to_expand.append(validated_xml.filename)
                        else:
                            raise ValueError("Unknown result {} from validator.is_msg_def_unique"
                                .format(uniqueness_result))

                        log.debug("Create edge {} - {}".format(cur_dialect, dup_check_def.filename))
                        include_graph.add_edges_from([(cur_dialect, dup_check_def.filename)])

                        # confirm the DAG is still directed and acyclic (to circular dependencies) before proceeding
                        if not netx.is_directed_acyclic_graph(include_graph):
                            log.error("Circular dependency detected involving '{}' and its included"
                                " dialect '{}'".format(cur_dialect, dup_check_def.filename))
                            return None
        return validated_xmls, include_graph

    def generate_dependency_list(self, validated_xmls : Dict[str, MavlinkXmlFile],
            include_graph : netx.DiGraph) -> None:
        """
        For each dialect xml, use the include graph to generate its list of dependencies.
        The resulting list of dependencies is the list of all xmls directly or indirectly included by the dialect.
        Each xmls list is set in its MavlinkXmlFile object
        """

        all_nodes = list(validated_xmls.keys())
        for node in all_nodes:
            includes = []
            # a 'reachable_node' comes from a depth-first-search (dfs) of the graph and indicates all includes
            # that are directly or indirectly included by the root 'node'
            for reachable_node in netx.dfs_postorder_nodes(include_graph, source=node):
                if reachable_node != node:  # we know we're reachable from ourself
                    includes.append(reachable_node)
            log.debug("{} uses the following includes: {}".format(node, includes))
            validated_xmls[node].set_dependencies(includes)

    def validate(self, xmls : List[str]) -> Dict[str, MavlinkXmlFile]:
        """
        Validate the provided list of xmls

        Steps:
        - Confirm each input xml is valid using @ref validate_single_xml
        - Expand the validated_xmls dictionary from just the input xmls to all xmls they include
          using @ref expand_includes
        - Generate a dependency list for all xmls using @ref generate_dependency_list
        """

        # first validate and load up all the xml files specified in the input parameter
        validated_xmls = {}
        for xml_filename in xmls:
            valid_msg_def = self.validate_single_xml(xml_filename)
            if valid_msg_def is None:
                return None

            uniqueness_result = self.is_msg_def_unique(valid_msg_def, validated_xmls)
            if uniqueness_result == MSG_DEF_UNIQUE:
                validated_xmls[valid_msg_def.filename] = valid_msg_def
            elif uniqueness_result == MSG_DEF_DUPLICATE_ERR:
                return None
            elif uniqueness_result == MSG_DEF_DUPLICATE:
                pass
            else:
                raise ValueError("Unknown result {} from validator.is_msg_def_unique".format(uniqueness_result))

        # now expand the includes of all the current validated xmls and verify the include tree
        result = self.expand_includes(validated_xmls)
        if result is None:
            # something went wrong while expanding includes
            return None
        validated_xmls = result[0]
        include_dag = result[1]

        # generate list of all dependencies for each xml
        self.generate_dependency_list(validated_xmls, include_dag)

        # run through all the attached custom validators
        for custom_validator in self.custom_validators:
            if not custom_validator.validate(validated_xmls, include_dag):
                log.error("{} failed validation".format(type(custom_validator).__name__))
                return None

        # successfully read, expanded and validated!
        return validated_xmls
