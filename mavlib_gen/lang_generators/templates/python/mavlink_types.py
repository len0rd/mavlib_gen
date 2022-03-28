# Supporting types for mavlib_gen auto-generated messages
from abc import ABC, abstractmethod
from multiprocessing.sharedctypes import Value
import struct
from typing import Union


MAVLINK_PROTOCOL_V2_STX = 0xFD


class x25crc(object):
    """
    CRC-16/MCRF4XX - based on checksum.h from mavlink library
    Added from pymavlink. TOOD: use library that is used by
    validator?
    TODO: TEMP, pulled from pymavlink
    """

    def __init__(self, buf=None):
        self.crc = 0xFFFF
        if buf is not None:
            if isinstance(buf, str):
                self.accumulate_str(buf)
            else:
                self.accumulate(buf)

    def accumulate(self, buf: bytearray) -> int:
        """add in some more bytes"""
        accum = self.crc
        for b in buf:
            tmp = b ^ (accum & 0xFF)
            tmp = (tmp ^ (tmp << 4)) & 0xFF
            accum = (accum >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)
        self.crc = accum

    def accumulate_str(self, buf: Union[str, bytes, bytearray]) -> int:
        """add in some more bytes"""
        import array

        bytes_array = array.array("B")
        try:  # if buf is bytes
            bytes_array.frombytes(buf)
        except TypeError:  # if buf is str
            bytes_array.frombytes(buf.encode())
        except AttributeError:  # Python < 3.2
            bytes_array.fromstring(buf)
        self.accumulate(bytes_array)


class MavlinkChannel:
    """
    Represents a Mavlink Channel and can be used to pack/unpack Mavlink messages
    """

    def __init__(self, sys_id: int, comp_id: int, channel_id: int):
        self.sys_id = sys_id
        self.comp_id = comp_id
        self._channel_id = channel_id
        self.incompatibility_flags = 0
        """
        Mavlink incompatibility flags to use for this channel.
        Messages sent with this channel will communicate these flags.
        Messages received by this channel must have matching flags to be deserialized
        """
        self.compatibility_flags = 0
        """Mavlink compatibility flags to communicate with each message sent via this channel"""
        self._seq_id = 0

    @property
    def sequence_id(self) -> int:
        """
        Get the next sequence id to use for this channel
        8 bit value
        """
        self._seq_id = (self._seq_id + 1) % 256
        return self._seq_id


class MavlinkHeader:
    """
    Contains all the header properties that are contained in a Mavlink V2 message header
    """

    def __init__(
        self,
        msg_id: int,
        msg_len: int = 0,
        incompat_flags: int = 0,
        compat_flags: int = 0,
        seq: int = 0,
        src_sys: int = 0,
        src_comp: int = 0,
    ):
        self._msg_len = msg_len
        self._incompat_flags = incompat_flags
        self._compat_flags = compat_flags
        self._seq = seq
        self._src_sys = src_sys
        self._src_comp = src_comp
        self._msg_id = msg_id

    # (using properties so docs can reliably show up for users)

    @property
    def msg_id(self) -> int:
        """
        The Mavlink message ID.
        24bit value
        """
        return self._msg_id

    @property
    def payload_length(self) -> int:
        """
        The length of this messages payload in bytes.
        8bit value
        """
        return self._msg_len

    @payload_length.setter
    def payload_length(self, new_pld_len: int) -> None:
        if new_pld_len > 255:
            raise ValueError(f"Attempt to set 8bit payload length to {new_pld_len}")
        self._msg_len = new_pld_len

    @property
    def src_sys(self) -> int:
        """
        The source system id of this message.
        8bit value
        """
        return self._src_sys

    @src_sys.setter
    def src_sys(self, new_src_sys: int) -> None:
        if new_src_sys > 255:
            raise ValueError(f"Attempt to set 8bit source system to {new_src_sys}")
        self._src_sys = new_src_sys

    @property
    def src_comp(self) -> int:
        """
        The source component id of this message.
        8bit value
        """
        return self._src_comp

    @src_comp.setter
    def src_comp(self, new_src_comp: int) -> None:
        if new_src_comp > 255:
            raise ValueError(f"Attempt to set 8bit source component to {new_src_comp}")
        self._src_comp = new_src_comp

    @property
    def sequence_id(self) -> int:
        """
        The sequence ID of this message.
        8bit value
        """
        return self._seq

    @sequence_id.setter
    def sequence_id(self, new_seq_id: int) -> None:
        if new_seq_id > 255:
            raise ValueError(f"Attempt to set 8bit sequence id to {new_seq_id}")
        self._compat_flags = new_seq_id

    @property
    def compatibility_flags(self) -> int:
        """
        The compatibility flags for this message.
        8bit value
        """
        return self._compat_flags

    @compatibility_flags.setter
    def compatibility_flags(self, new_compat_flags: int) -> None:
        if new_compat_flags > 255:
            raise ValueError(f"Attempt to set 8bit compatibility flags to {new_compat_flags}")
        self._compat_flags = new_compat_flags

    @property
    def incompatibility_flags(self) -> int:
        """
        The incompatibility flags for this message.
        8bit value
        """
        return self._incompat_flags

    @incompatibility_flags.setter
    def incompatibility_flags(self, new_incompat_flags: int) -> None:
        if new_incompat_flags > 255:
            raise ValueError(f"Attempt to set 8bit incompatibility flags to {new_incompat_flags}")
        self._incompat_flags = new_incompat_flags

    def set_from_channel(self, channel: MavlinkChannel) -> None:
        """
        Set properties of this header based on the provided MavlinkChannel
        """
        self.sequence_id = channel.sequence_id
        self.compatibility_flags = channel.compatibility_flags
        self.incompatibility_flags = channel.incompatibility_flags
        self.src_sys = channel.sys_id
        self.src_comp = channel.comp_id

    def pack(self) -> bytearray:
        """
        Pack this mavlink header into a byte array that could be sent over a message
        """
        return struct.pack(
            "<BBBBBBBHB",
            MAVLINK_PROTOCOL_V2_STX,
            self.payload_length,
            self.incompatibility_flags,
            self.compatibility_flags,
            self.sequence_id,
            self.src_sys,
            self.src_comp,
            self.msg_id & 0xFFFF,
            self.msg_id >> 16,
        )


class MavlinkMessage(ABC):
    """
    Abstract base class for an instance of a Mavlink message
    """

    def __init__(self, msg_id: int):
        self._header = MavlinkHeader(msg_id)

    @property
    def header(self) -> MavlinkHeader:
        """
        Get an object holding all header information for this message
        """
        return self._header

    @abstractmethod
    def pack(self, channel: MavlinkChannel) -> bytearray:
        """
        Pack this message into a byte array that can be sent over a transport
        """
        pass

    def _pack(
        self, channel: MavlinkChannel, serialized_payload: bytearray, crc_extra: int
    ) -> bytearray:
        """
        Internal Pack method called by MavlinkMessage extensions
        """
        self.header.set_from_channel(channel)

        # Mavlink 2 supports 0-trimming payloads
        serialized_payload = serialized_payload.rstrip(0x00)
        self.header.payload_length = len(serialized_payload)
        packed_msg = self.header.pack() + serialized_payload
        msg_crc = x25crc(packed_msg[1:])
        msg_crc.accumulate_str(struct.pack("B", crc_extra))
        packed_msg += struct.pack("<H", msg_crc)
        return packed_msg
