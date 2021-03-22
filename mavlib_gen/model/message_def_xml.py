################################################################################
# \file message_def_xml
#
# Model object that represents a single message definition xml file
#
# Copyright (c) 2021 len0rd
#
# All rights reserved.
# This file is distributed under the terms of the MIT License.
# See the file 'LICENSE' in the root directory of the present
# distribution, or http://opensource.org/licenses/MIT.
################################################################################
import os, logging
from typing import List
from xmlschema.dataobjects import DataElement

log = logging.getLogger(__name__)

class MavlinkXml(object):

    TAG_MAP = {
        'messages' : (lambda mav_xml, data_elem: mav_xml.enumerate_messages(data_elem)),
        'enums'    : (lambda mav_xml, data_elem: mav_xml.enumerate_enums(data_elem)),
        'include'  : (lambda mav_xml, data_elem: mav_xml.includes.append(str(data_elem.text))),
        'version'  : (lambda mav_xml, data_elem: setattr(mav_xml, 'version', str(data_elem.text))),
        'dialect'  : (lambda mav_xml, data_elem: setattr(mav_xml, 'dialect', str(data_elem.text))),
    }

    def __init__(self, mavlink_data_elem : DataElement):

        self.includes = []
        self.messages = []
        self.enums = []
        self.version = None
        self.dialect = None

        for child in mavlink_data_elem:
            if not child.tag in self.TAG_MAP:
                log.error("Unknown element in MavlinkXml : {}".format(child.tag))
            else:
                self.TAG_MAP[child.tag](self, child)

    def enumerate_messages(self, messages_data_elem : DataElement):
        for child in messages_data_elem:
            self.messages.append(MavlinkXmlMessage(child))

    def enumerate_enums(self, enums_data_elem):
        return False

    def __repr__(self):
        rep = "messages:\n"
        for msg in self.messages:
            rep += " {}\n".format(msg.__repr__())
        return rep

class MavlinkXmlFile(object):

    def __init__(self, absolute_path, xml : MavlinkXml):
        """
        Construct a Message Definition xml object. These objects must contain
        their base filename (ie: 'common.xml'), the absolute path to the file
        ('/home/len0rd/common.xml') and the schema-validated xml object
        """
        self.absolute_path = absolute_path
        self.filename = os.path.basename(absolute_path)
        self.xml = xml
        self.dependencies = None

    def set_dependencies(self, deps : List[str]):
        """
        Update this objects list of dependencies.
        The dependency list is a list of all xml message definition files
        this xml directly or indirectly includes
        """
        self.dependencies = deps

class MavlinkXmlMessage(object):

    TAG_MAP = {
        'description' : (lambda msg, data_elem : setattr(msg, 'description', str(data_elem.text))),
        'extensions'  : (lambda msg, data_elem : setattr(msg, 'has_extensions', True)),
        'field'       : (lambda msg, data_elem : msg.__append_field(data_elem)),
        # TODO: deprecated and wip elements
    }

    def __init__(self, message_data_elem : DataElement):
        self.fields = []
        self.extension_fields = []
        self.has_extensions = False
        self.id = None
        self.name = None
        self.description = None

        for child in message_data_elem:
            if not child.tag in self.TAG_MAP:
                log.error("Unknown element in MavlinkXmlMessage: {}".format(child.tag))
            else:
                self.TAG_MAP[child.tag](self, child)

        # set any element attributes as object attributes (should set 'id' and 'name' attributes for a message)
        for k,v in message_data_elem.attrib.items():
            setattr(self, k, v)

    def __append_field(self, field_data_elem : DataElement):
        if self.has_extensions:
            self.extension_fields.append(MavlinkXmlMessageField(field_data_elem))
        else:
            self.fields.append(MavlinkXmlMessageField(field_data_elem))

    def __repr__(self):
        rep = "Msg({}, id={} fields:\n".format(self.name, self.id)
        for field in self.fields:
            rep += "  {}\n".format(field.__repr__())
        if len(self.extension_fields) > 0:
            rep += "  extensions:\n"
            for field in self.extension_fields:
                rep += "  {}\n".format(field.__repr__())
        rep += ")"
        return rep

class MavlinkXmlMessageField(object):

    def __init__(self, field_elem : DataElement):
        self.description = field_elem.text
        if self.description is not None:
            self.description = str(self.description).strip()

        # set any element attributes as object attributes (should set 'name' and 'type' attributes for a field at a minimum)
        # may also include 'units', 'instance', 'enum' etc
        for k,v in field_elem.attrib.items():
            setattr(self, k, v)

    def __repr__(self):
        rep = "Field({}, type={}".format(self.name, self.type)

        no_append_attrs = ['name', 'type', ]#'description']
        for k,v in self.__dict__.items():
            if not k in no_append_attrs:
                rep += ", {}={}".format(k,v)
        rep += ")"
        return rep

# class MavlinkXmlEnum(object):

# class MavlinkXmlEnumValue(object):

# class MavlinkXmlEnumValueParam(object):


