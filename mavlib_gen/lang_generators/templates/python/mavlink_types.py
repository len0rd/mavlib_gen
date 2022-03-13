# Supporting types for mavlib_gen auto-generated messages
from abc import ABC, abstractmethod


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

    # (using properties so docs can easily show up for users)

    @property
    def msg_id(self) -> int:
        """
        Get the Mavlink message ID.
        24bit value
        """
        return self._msg_id

    @property
    def payload_length(self) -> int:
        """
        Get the length of this messages payload in bytes.
        8bit value
        """
        return self._msg_len

    @property
    def src_sys(self) -> int:
        """
        Get the source system id of this message.
        8bit value
        """
        return self._src_sys

    @property
    def src_comp(self) -> int:
        """
        Get the source component id of this message.
        8bit value
        """
        return self._src_comp

    @property
    def seq_id(self) -> int:
        """
        Get the sequence ID of this message.
        8bit value
        """
        return self._seq

    @property
    def compatibility_flags(self) -> int:
        """
        Get the compatibility flags for this message.
        8bit value
        """
        return self._compat_flags

    @property
    def incompatibility_flags(self) -> int:
        """
        Get the incompatibility flags for this message.
        8bit value
        """
        return self._incompat_flags


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
    def pack(self) -> bytearray:
        """
        Pack this message into a byte array that can be sent over a transport
        """
        pass
