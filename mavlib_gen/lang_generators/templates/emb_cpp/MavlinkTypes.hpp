/// Type definitions for MAVLink library
///
/// Included as part of message generation by mavlib_gen
#ifndef __MAVLINKTYPES_H__
#define __MAVLINKTYPES_H__
#include <stddef.h>
#include <stdint.h>

#ifndef MAV_STRUCT_PACK
#ifdef __GNUC__
#define MAV_STRUCT_PACK(__declaration__) __declaration__ __attribute__((packed))
#else
#define MAV_STRUCT_PACK(__declaration__) __pragma(pack(push, 1)) __declaration__ __pragma(pack(pop))
#endif
#endif

/// Defines the maximum number of fields that can be in a single message.
#ifndef MAV_MAX_NUM_MSG_FIELDS
#define MAV_MAX_NUM_MSG_FIELDS 64
#endif

namespace mavgen {

enum MavlinkFieldType {
    CHAR = 0,
    UINT8_T = 1,
    INT8_T = 2,
    UINT16_T = 3,
    INT16_T = 4,
    UINT32_T = 5,
    INT32_T = 6,
    UINT64_T = 7,
    INT64_T = 8,
    FLOAT = 9,
    DOUBLE = 10
};

/// Information about a properties common to all messages
struct MavlinkMsgInfo {
    uint32_t msgid;
    uint8_t crcExtra;
    uint8_t maxLength;
};

struct MavlinkMsgFieldInfo {
    /// @brief Name of the field
    const char* name;
    MavlinkFieldType type;
    /// If this field is an array, the max number of elements, otherwise 0
    size_t arrayLength;
    /// Total size of this field in bytes
    size_t byteSize;
    /// 0-based byte offset of where this field begins in a serialized payload
    size_t wireOffset;
};

/// @brief Detailed information about a message that can be optionally included at compile time
struct MavlinkMsgDetails {
    /// @brief Information on each field in this message
    MavlinkMsgFieldInfo fields[MAV_MAX_NUM_MSG_FIELDS];
    /// @brief Number of fields in @ref fields
    size_t numFields;
    /// @brief String name of this message
    const char* name;
};

/// Interface that all mavlink messages inherit
class IMavlinkMessage {
   public:
    /// @brief Get basic information about this message
    virtual const MavlinkMsgInfo& getMsgInfo() const = 0;

#ifdef MAV_INCLUDE_MSG_DETAILS
    /// @brief Get detailed information on this message and its fields
    virtual const MavlinkMsgDetails& getMsgDetails() const = 0;
#endif
};

}  // namespace mavgen

#endif /* __MAVLINKTYPES_H__ */
