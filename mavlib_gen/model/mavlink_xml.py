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
import os, logging, operator
from typing import List
from xmlschema.dataobjects import DataElement

log = logging.getLogger(__name__)

class MavlinkXml(object):

    def __init__(self, mavlink_data_elem : DataElement):
        self.includes = []
        self.messages = []
        self.enums = []
        self.version = None
        self.dialect = None

        TAG_MAP = {
            'messages' : (lambda mav_xml, data_elem: mav_xml.__enumerate_messages(data_elem)),
            'enums'    : (lambda mav_xml, data_elem: mav_xml.__enumerate_enums(data_elem)),
            'include'  : (lambda mav_xml, data_elem: mav_xml.includes.append(str(data_elem.text))),
            'version'  : (lambda mav_xml, data_elem: setattr(mav_xml, 'version', str(data_elem.text))),
            'dialect'  : (lambda mav_xml, data_elem: setattr(mav_xml, 'dialect', str(data_elem.text))),
        }

        for child in mavlink_data_elem:
            if not child.tag in TAG_MAP:
                log.error("Unknown element in MavlinkXml : {}".format(child.tag))
            else:
                TAG_MAP[child.tag](self, child)

    def __enumerate_messages(self, messages_data_elem : DataElement):
        """Used during construction to import message definitions into the object"""
        for child in messages_data_elem:
            self.messages.append(MavlinkXmlMessage(child))

    def __enumerate_enums(self, enums_data_elem):
        """Used during construction to import enum definitions into the object"""
        return False

    def __repr__(self):
        rep = "messages:\n"
        for msg in self.messages:
            rep += " {}\n".format(msg.__repr__())
        return rep

class MavlinkXmlFile(object):
    """
    Top-level model object to contain information on a mavlink xml definition
    file including its parsed/validated @ref MavlinkXml object
    """

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

    def __init__(self, message_data_elem : DataElement):
        self.fields = []
        self.extension_fields = []
        self.has_extensions = False
        self.id = None
        self.name = None
        self.description = None

        TAG_MAP = {
            'description' : (lambda msg, data_elem : setattr(msg, 'description', str(data_elem.text))),
            'extensions'  : (lambda msg, data_elem : setattr(msg, 'has_extensions', True)),
            'field'       : (lambda msg, data_elem : msg.__append_field(data_elem)),
            # TODO: deprecated and wip elements
        }

        for child in message_data_elem:
            if not child.tag in TAG_MAP:
                log.error("Unknown element in MavlinkXmlMessage: {}".format(child.tag))
            else:
                TAG_MAP[child.tag](self, child)

        # set any element attributes as object attributes (should set 'id' and 'name' attributes for a message)
        for k,v in message_data_elem.attrib.items():
            setattr(self, k, v)

        self.__reorder_fields()

    def __reorder_fields(self):
        """reorder the fields array to comply with Mavlink field reordering rules"""
        # fun fact: the way mavlink reorders fields is actually terrible
        # for now just sort the fields array itself (why maintain original field order? nice for generated function calls?)
        if len(self.fields) > 0:
            self.fields.sort(key=operator.attrgetter('base_type_len'))

    def __append_field(self, field_data_elem : DataElement):
        """append a new field to the correct list (fields or extension_fields"""
        # on construction, has_extensions is marked True once an 'extensions' element is encountered.
        # meaning all field elements following has_extension being set to True are extension fields
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

        BASE_TYPE_LEN_MAP = {
            'uint64_t' : 8,
            'int64_t'  : 8,
            'double'   : 8,
            'uint32_t' : 4,
            'int32_t'  : 4,
            'float'    : 4,
            'uint16_t' : 2,
            'int16_t'  : 2,
            'uint8_t'  : 1,
            'int8_t'   : 1,
            'char'     : 1,
            'uint8_t_mavlink_version'  : 1,
        }

        base_type = self.type
        arr_open_idx = self.type.find('[')
        arr_len = 0
        if arr_open_idx != -1:
            base_type = self.type[:arr_open_idx]
            arr_len = int(self.type[arr_open_idx+1:-1])

        self.base_type_len = BASE_TYPE_LEN_MAP[base_type]

        if arr_len > 0:
            self.field_len = self.base_type_len * arr_len
        else:
            self.field_len = self.base_type_len

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


