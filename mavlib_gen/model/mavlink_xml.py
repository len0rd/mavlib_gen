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
import logging
import operator
from typing import List
from xmlschema.dataobjects import DataElement
import crcmod
import re
from pathlib import Path

log = logging.getLogger(__name__)


# Helper methods (shared by multiple model objects)
def name_str_format_converter(str_in: str, format: str) -> str:
    """
    Make best-effort to fet the str_in name value in a particular format

    :TODO: This method works under the assumption that str_in is
        in a snake_case/snake-case (either UPPER or lower or Camel_Snake) already

    :param format: specify the desired format to return the name string in.
        Available types:
        'lower_snake' = lower snake case name (ie: "message_name")
        'UPPER_SNAKE' = upper snake case name (ie: "MESSAGE_NAME")
        'UpperCamel'  = upper camel case name (ie: "MessageName")
        If none of these options are correctly provided, the raw name string is returned
    """
    caseless_format = format.lower()
    if caseless_format == "lower_snake":
        return str_in.lower()
    elif caseless_format == "upper_snake":
        return str_in.upper()
    elif caseless_format == "uppercamel":
        all_words = re.split(r"([^a-zA-Z0-9])", str_in)
        return "".join(word.capitalize() for word in all_words if word.isalnum())
    else:
        return str_in


def raw_str_formatter(str_in: str, line_prefix: str = None, leading_newline: bool = False) -> str:
    """
    Get a formatted version of a raw string (typically a string from an XML definition). This mainly
    helps fix up multi-line descriptions to look nice while hopefully preserving the intended look
    of the author
    """
    processed_str = str_in
    # replace all tabs with 4 spaces
    processed_str = processed_str.replace("\t", "    ")
    # remove leading_newline if one is not desired
    if not leading_newline and processed_str.lstrip(" ")[0] == "\n":
        processed_str = processed_str.lstrip(" ")[1:]

    if "\n" in processed_str:
        # attempt to solve for the common number of leading whitespace characters that are shared
        # across all lines of the input string (trying to get rid of ws that comes from xml
        # indentation)
        START_VALUE = 1000000
        leading_spaces = START_VALUE  # (set to unreasonably large value for below comparison)
        for line in processed_str.split("\n"):
            num_leading_space_on_line = len(line) - len(line.lstrip(" "))
            if num_leading_space_on_line != 0 and num_leading_space_on_line < leading_spaces:
                leading_spaces = num_leading_space_on_line
        if leading_spaces != START_VALUE:
            # replace the common number of whitespace characters with line_prefix if present
            to_be_replaced = "\n" + (" " * leading_spaces)
            to_replace_with = "\n" + line_prefix if line_prefix is not None else "\n"
            processed_str = processed_str.replace(to_be_replaced, to_replace_with)
    # add leading newline if one is desired
    if leading_newline and processed_str[0] != "\n":
        prepend = "\n"
        if line_prefix is not None:
            prepend = prepend + line_prefix
        processed_str = prepend + processed_str

    return processed_str


class MavlinkXmlEnumEntryParam(object):
    """Represents a 'param' child within a mavlink XML enum entry"""

    def __init__(self, param_data_elem: DataElement):
        self._index = None
        self._description = ""
        self._label = None
        self._minValue = None
        self._maxValue = None
        # per schema, if not declared reserved is implicitly False
        self._reserved = False
        self._default = None
        self._units = None

        if param_data_elem.text is not None and len(str(param_data_elem.text)) > 0:
            self._description = str(param_data_elem.text)

        for k, v in param_data_elem.attrib.items():
            setattr(self, "_" + k, v)

        self._index = int(self._index)

    @property
    def index(self) -> int:
        return self._index

    @property
    def description(self) -> str:
        """description string attached to the param"""
        return self._description

    def doc_string(self, continuation_indent: int = 4) -> str:
        """Friendly doc string that can be used by generators"""
        indented_doc_str = self.description.replace("\n", "\n" + " " * continuation_indent)
        return "param {}: {}".format(self.index, indented_doc_str)

    # TODO: add other param values here as needed


class MavlinkXmlEnumEntry(object):
    """Represents an Enum entry/value within a mavlink XML enum"""

    def __init__(self, entry_data_elem: DataElement):
        self._params = []
        self._name = None
        self._value = None
        self._description = None

        TAG_MAP = {
            "description": (
                lambda entry, data_elem: setattr(entry, "_description", str(data_elem.text))
            ),
            "param": (lambda entry, data_elem: entry.__append_param(data_elem)),
        }

        for child in entry_data_elem:
            if child.tag not in TAG_MAP:
                log.error("Unknown element in MavlinkXmlEnumEntry: {}".format(child.tag))
            else:
                TAG_MAP[child.tag](self, child)

        for k, v in entry_data_elem.attrib.items():
            setattr(self, "_" + k, v)

        self._name = str(self._name)
        # store value as a string so its generated to look the same as the definition (useful
        # for hex numbers) the schema validates its a good value
        self._value = str(self._value)

    @property
    def name(self) -> str:
        """the unique enum entry name"""
        return self._name

    @property
    def value(self) -> str:
        """
        Value of the enum. Returned as a string so it will look identical to its declaration
        in the message definition. Useful for hex numbers
        """
        return self._value

    @property
    def description(self) -> str:
        """description string attached to the enum entry"""
        return self._description

    @property
    def params(self) -> List[MavlinkXmlEnumEntryParam]:
        """
        List of params attached to this entry in the order theyre defined, if any.
        Defaults to empty list
        """
        return self._params

    def __append_param(self, param_data_elem: DataElement) -> None:
        """Append a new param to this enum entry's list of params"""
        self._params.append(MavlinkXmlEnumEntryParam(param_data_elem))


class MavlinkXmlEnum(object):
    """Represents a single enum as defined in a mavlink XML"""

    def __init__(self, enum_data_elem: DataElement):
        self._entries = []
        self._name = None
        self._description = None

        TAG_MAP = {
            "description": (
                lambda enum, data_elem: setattr(enum, "_description", str(data_elem.text))
            ),
            "entry": (lambda enum, data_elem: enum.__append_entry(data_elem)),
        }

        for child in enum_data_elem:
            if child.tag not in TAG_MAP:
                log.error("Unknown element in MavlinkXmlEnum: {}".format(child.tag))
            else:
                TAG_MAP[child.tag](self, child)

        for k, v in enum_data_elem.attrib.items():
            setattr(self, "_" + k, v)

        self._name = str(self._name)

    @property
    def name(self) -> str:
        """the unique enum name"""
        return self._name

    @property
    def description(self) -> str:
        """description string attached to the enum"""
        return self._description

    @property
    def entries(self) -> List[MavlinkXmlEnumEntry]:
        """List of enum entries in the mavlink enum in the order they're defined"""
        return self._entries

    def __append_entry(self, entry_data_elem: DataElement) -> None:
        """Append a new entry to this enums list of entries"""
        self._entries.append(MavlinkXmlEnumEntry(entry_data_elem))


class MavlinkXmlMessageField(object):
    def __init__(
        self,
        field_elem: DataElement = None,
        name: str = None,
        typename: str = None,
        description: str = None,
    ):
        if field_elem is not None:
            self.description = field_elem.text
            if self.description is not None:
                self.description = str(self.description).strip()

            # set any element attributes as object attributes (should set 'name' and 'type'
            # attributes for a field at a minimum) may also include 'units', 'instance', 'enum' etc
            for k, v in field_elem.attrib.items():
                setattr(self, k, v)
        elif name is not None:
            self.name = name
            self.type = typename
            self.description = description

        self.__determine_type_attributes()

    def __determine_type_attributes(self) -> None:
        """Determine meta-information about this field from its 'type' attribute"""
        BASE_TYPE_LEN_MAP = {
            "uint64_t": 8,
            "int64_t": 8,
            "double": 8,
            "uint32_t": 4,
            "int32_t": 4,
            "float": 4,
            "uint16_t": 2,
            "int16_t": 2,
            "uint8_t": 1,
            "int8_t": 1,
            "char": 1,
            "uint8_t_mavlink_version": 1,
        }

        self.base_type = self.type
        if self.type == "uint8_t_mavlink_version":
            self.base_type = "uint8_t"
        arr_open_idx = self.type.find("[")
        arr_len = 0
        if arr_open_idx != -1:
            self.base_type = self.type[:arr_open_idx]
            arr_len = int(self.type[arr_open_idx + 1 : -1])

        self.base_type_len = BASE_TYPE_LEN_MAP[self.base_type]

        if arr_len > 0:
            self.field_len = self.base_type_len * arr_len
            self.array_len = arr_len
        else:
            self.field_len = self.base_type_len
            self.array_len = 0

    @property
    def is_array(self) -> bool:
        return self.array_len > 0

    def get_name(self, format: str) -> str:
        """
        :param format: specify the desired format to return the field name string in.
            Available types:
            'lower_snake' = lower snake case name (ie: "message_name")
            'UPPER_SNAKE' = upper snake case name (ie: "MESSAGE_NAME")
            'UpperCamel'  = upper camel case name (ie: "MessageName")
            If none of these options are correctly provided, the raw name string is returned
        """
        return name_str_format_converter(self.name, format)

    def get_type(self, lang: str) -> str:
        """
        Get what the internal type of this field would be in the specified language

        :param lang: The language to convert the mavlink type into
            Available Languages:
            'c'
            'python' - Returns the type-hint version of this fields type.
                EX: list of uint8's is returned as "List[int]"
        """
        lang = lang.lower()
        if lang == "c":
            return self.type
        elif lang == "python":
            type_out = self.type
            if "int" in self.type:
                type_out = "List[int]" if self.is_array else "int"
            elif "char" in self.type:
                type_out = "str"
            else:
                type_out = "List[float]" if self.is_array else "float"
            return type_out
        return self.type

    def formatted_description(self, line_prefix: str = None, leading_newline: bool = False) -> str:
        """
        Get a formatted version of this fields description. This mainly helps fix up multi-line
        descriptions to look nice while hopefully preserving the desired look of the author
        """
        return raw_str_formatter(
            self.description, line_prefix=line_prefix, leading_newline=leading_newline
        )

    def __repr__(self):
        rep = "Field({}, type={}".format(self.name, self.type)

        no_append_attrs = [
            "name",
            "type",
        ]  # 'description']
        for k, v in self.__dict__.items():
            if k not in no_append_attrs:
                rep += ", {}={}".format(k, v)
        rep += ")"
        return rep


class MavlinkXmlMessage(object):
    def __init__(self, message_data_elem: DataElement):
        # use properties of the same name (minus the leading '_') to get
        self._fields = []
        self._sorted_fields = []
        self._extension_fields = []
        # marked as true if there are extension fields. Should be equivalent to
        # len(extension_fields) > 0
        self.has_extensions = False
        self._id = None
        self._name = None
        self._description = None
        self._crc_extra = 0
        self._length = 0

        TAG_MAP = {
            "description": (
                lambda msg, data_elem: setattr(msg, "_description", str(data_elem.text))
            ),
            "extensions": (lambda msg, data_elem: setattr(msg, "has_extensions", True)),
            "field": (lambda msg, data_elem: msg.__append_field(data_elem)),
            # TODO: deprecated and wip elements
        }

        for child in message_data_elem:
            if child.tag not in TAG_MAP:
                log.error("Unknown element in MavlinkXmlMessage: {}".format(child.tag))
            else:
                TAG_MAP[child.tag](self, child)

        # set any element attributes as object attributes (should set 'id' and 'name' attributes
        # for a message)
        for k, v in message_data_elem.attrib.items():
            setattr(self, "_" + k, v)

        self._id = int(self._id)
        self._name = str(self._name)
        self._length = sum(field.field_len for field in self._fields) + sum(
            field.field_len for field in self._extension_fields
        )

        self.__reorder_fields()

        self.__calculate_crc_extra()

    # message properties:

    @property
    def id(self) -> int:
        """the 24-bit unsigned message id"""
        return self._id

    @property
    def name(self) -> str:
        """the unique message name"""
        return self._name

    def get_name(self, format: str) -> str:
        """
        :param format: specify the desired format to return the message name string in.
            Available types:
            'lower_snake' = lower snake case name (ie: "message_name")
            'UPPER_SNAKE' = upper snake case name (ie: "MESSAGE_NAME")
            'UpperCamel'  = upper camel case name (ie: "MessageName")
            If none of these options are correctly provided, the raw name string is returned
        """
        return name_str_format_converter(self.name, format)

    @property
    def description(self) -> str:
        """description string attached to the message"""
        return self._description

    def formatted_description(self, line_prefix: str = None, leading_newline: bool = False) -> str:
        """
        Get a formatted version of this messages description. This mainly helps fix up multi-line
        descriptions to look nice while hopefully preserving the desired look of the author
        """
        return raw_str_formatter(
            self.description, line_prefix=line_prefix, leading_newline=leading_newline
        )

    @property
    def fields(self) -> List[MavlinkXmlMessageField]:
        """the messages non-extension fields sorted in xml definition order"""
        return self._fields

    @property
    def num_fields(self) -> int:
        """number of fields (including extension fields) in this message"""
        return len(self.fields) + len(self.extension_fields)

    # TODO: name change to fields_sorted?
    @property
    def sorted_fields(self) -> List[MavlinkXmlMessageField]:
        """
        the messages non-extension fields sorted in mavlink-order. The contents
        is the same as @ref fields, just in the byte/serialization order that will be used
        over the wire
        """
        return self._sorted_fields

    @property
    def extension_fields(self) -> List[MavlinkXmlMessageField]:
        """the messages extension fields in xml definition order, if any"""
        return self._extension_fields

    @property
    def all_fields(self) -> List[MavlinkXmlMessageField]:
        """Return all fields in a message, including its extension fields"""
        all_fields = self._fields
        all_fields.extend(self._extension_fields)
        return all_fields

    @property
    def all_fields_sorted(self) -> List[MavlinkXmlMessageField]:
        """All of the messages fields (including extension fields if any) in mavlink-order"""
        all_sorted = self._sorted_fields
        all_sorted.extend(self._extension_fields)
        return all_sorted

    @property
    def crc_extra(self) -> int:
        """
        The Mavlink CRC_EXTRA for this message.
        See https://mavlink.io/en/guide/serialization.html#crc_extra
        """
        return self._crc_extra

    @property
    def byte_length(self) -> int:
        """The maximum length of the message payload (does not include the header) in bytes"""
        return self._length

    def __reorder_fields(self) -> None:
        """reorder the fields array to comply with Mavlink field reordering rules"""
        # fun fact: the way mavlink reorders fields is actually terrible
        # for now just sort the fields array itself (why maintain original field order? nice
        # for generated function calls?)
        if len(self._fields) > 0:
            self._sorted_fields = sorted(
                self._fields, key=operator.attrgetter("base_type_len"), reverse=True
            )

    def __calculate_crc_extra(self) -> None:
        """Calculate and set the CRC_EXTRA for this message"""
        mav_crc_generator = crcmod.predefined.Crc("crc-16-mcrf4xx")
        msg_name_str = self.name + " "

        mav_crc_generator.update(msg_name_str.encode())
        for field in self._sorted_fields:
            field_type = field.base_type + " "
            field_name = field.name + " "
            mav_crc_generator.update(field_type.encode())
            mav_crc_generator.update(field_name.encode())
            if field.is_array:
                mav_crc_generator.update(bytes([field.array_len]))

        digest = int(mav_crc_generator.hexdigest(), 16)
        self._crc_extra = (digest & 0xFF) ^ (digest >> 8)

    def __append_field(self, field_data_elem: DataElement) -> None:
        """append a new field to the correct list (fields or extension_fields"""
        # on construction, has_extensions is marked True once an 'extensions' element is
        # encountered.meaning all field elements following has_extension being set to True are
        # extension fields
        if self.has_extensions:
            self._extension_fields.append(MavlinkXmlMessageField(field_data_elem))
        else:
            self._fields.append(MavlinkXmlMessageField(field_data_elem))

    def __repr__(self):
        rep = "Msg({}, id={} fields:\n".format(self.name, self.id)
        for field in self._fields:
            rep += "  {}\n".format(field.__repr__())
        if len(self._extension_fields) > 0:
            rep += "  extensions:\n"
            for field in self._extension_fields:
                rep += "  {}\n".format(field.__repr__())
        rep += ")"
        return rep


class MavlinkXml(object):
    def __init__(self, mavlink_data_elem: DataElement):
        self.includes = []
        self._messages = []
        self._enums = []
        self.version = None
        self.dialect = None

        TAG_MAP = {
            "messages": (lambda mav_xml, data_elem: mav_xml.__enumerate_messages(data_elem)),
            "enums": (lambda mav_xml, data_elem: mav_xml.__enumerate_enums(data_elem)),
            "include": (lambda mav_xml, data_elem: mav_xml.includes.append(str(data_elem.text))),
            "version": (
                lambda mav_xml, data_elem: setattr(mav_xml, "version", str(data_elem.text))
            ),
            "dialect": (
                lambda mav_xml, data_elem: setattr(mav_xml, "dialect", str(data_elem.text))
            ),
        }

        for child in mavlink_data_elem:
            if child.tag not in TAG_MAP:
                log.error("Unknown element in MavlinkXml : {}".format(child.tag))
            else:
                TAG_MAP[child.tag](self, child)

    @property
    def messages(self) -> List[MavlinkXmlMessage]:
        """List of all messages contained in this mavlink dialect xml"""
        return self._messages

    @property
    def enums(self) -> List[MavlinkXmlEnum]:
        """List of all enums contained in this mavlink dialect xml"""
        return self._enums

    @property
    def include_names(self) -> List[str]:
        """
        String list of files inside this XMLs `<include>` tags, without any paths, just the
        base filename
        """
        return [Path(fname).name for fname in self.includes]

    def __enumerate_messages(self, messages_data_elem: DataElement) -> None:
        """Used during construction to import message definitions into the object"""
        for child in messages_data_elem:
            self._messages.append(MavlinkXmlMessage(child))

    def __enumerate_enums(self, enums_data_elem: DataElement) -> None:
        """Used during construction to import enum definitions into the object"""
        for child in enums_data_elem:
            self._enums.append(MavlinkXmlEnum(child))

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

    def __init__(self, absolute_path: str, xml: MavlinkXml):
        """
        Construct a Message Definition xml object. These objects must contain
        their base filename (ie: 'common.xml'), the absolute path to the file
        ('/home/len0rd/common.xml') and the schema-validated xml object
        """
        self.absolute_path = absolute_path
        self.filename = Path(absolute_path).name
        self._xml = xml
        self.dependencies = None

    @property
    def xml(self) -> MavlinkXml:
        """
        Get the XML model object for this file which contains all message and enum definition
        model objects
        """
        return self._xml

    def set_dependencies(self, deps: List[str]) -> None:
        """
        Update this objects list of dependencies.
        The dependency list is a list of all xml message definition files
        this xml directly or indirectly includes
        """
        self.dependencies = deps
