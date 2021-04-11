/// Types used by the mavlink library
#ifndef __MAVLINK_TYPES_H__
#define __MAVLINK_TYPES_H__
#include <stdint.h>

#ifndef MAV_STRUCT_PACK
#ifdef __GNUC__
  #define MAV_STRUCT_PACK(__Declaration__) __Declaration__ __attribute__((packed))
#else
  #define MAV_STRUCT_PACK(__Declaration__) __pragma( pack(push, 1) ) __Declaration__ __pragma( pack(pop) )
#endif
#endif

#define MAVLINK_NUM_CHECKSUM_BYTES 2
#define MAVLINK_NUM_HEADER_BYTES 10
#define MAVLINK_NUM_NON_PAYLOAD_BYTES (MAVLINK_NUM_HEADER_BYTES+MAVLINK_NUM_CHECKSUM_BYTES)
#define MAVLINK_MAX_PAYLOAD_LEN 255

#ifndef MAVLINK_MAX_CHANNELS
  // Allow 4 channels by default
  #define MAVLINK_MAX_CHANNELS 4
#endif /* MAVLINK_MAX_CHANNELS */

#ifndef MAVLINK_CHANNEL_T
  typedef size_t mavlink_channel_t;
#endif /* MAVLINK_CHANNEL_T */

/// Definition of a generic mavlink message
/// NOTE: this struct is not packed, meaning there may be
/// padding between the header, payload and checksum regions
typedef struct __mavlink_message_t {
    union {
        MAV_STRUCT_PACK(struct {
            uint8_t magic;            ///< magic stx byte
            uint8_t len;              ///< length of the message payload
            uint8_t incompat_flags;   ///< flags that must be understood for compatibility
            uint8_t compat_flags;     ///< flags that can be ignored if not understood
            uint8_t seq;              ///< component increments for each message sent
            uint8_t sysid;            ///< source system id of the message
            uint8_t compid;           ///< source component id of the message
            uint32_t msgid:24;        ///< 3-byte id of message type in payload
        });
        uint8_t bytes[MAVLINK_NUM_HEADER_BYTES];    ///< convenience packed array used in parsing
    } header;                                       ///< message packet header
    uint8_t payload[MAVLINK_MAX_PAYLOAD_LEN];       ///< message data. Contents dependent on type
    union {
        uint16_t ck;                                ///< checksum as a single uint
        uint8_t bytes[MAVLINK_NUM_CHECKSUM_BYTES];  ///< individual checksum bytes
    } checksum;                                     ///< CRC-16/MCRF4XX for message (excluding magic byte)
} mavlink_message_t;

/// Function pointer to a send_bytes method for mavlink TX helpers to use.
/// Certain TX helpers can use this callback method to queue/send bytes as it
/// gets them ready to transmit
/// @param tx_bytes
///   Pointer to the current array of bytes to send
/// @param tx_len
///   Number of bytes in tx_bytes to win
/// @return int
///   Return 0 on success. All other error codes will result in the mavlink
///   TX helper dropping the current message it's attempting to send
typedef int (*mavlink_send_bytes_fn_t)(const uint8_t *tx_bytes, uint32_t tx_len);

typedef struct __mavlink_tx_info_t {
    uint16_t final_crc;   // final CRC produced for the messaged
    uint8_t  trimmed_len; // Trimmed length of the payload
    uint8_t  seq;         // Sequence id the message was transmitted with
};

typedef struct __mavlink_info_t {
    uint32_t msgid;
    uint8_t crc_extra;
    uint8_t len;
} mavlink_info_t;

/// The state machine for the comm parser
typedef enum {
    MAVLINK_PARSE_STATE_UNINIT=0,
    MAVLINK_PARSE_STATE_IDLE,
    MAVLINK_PARSE_STATE_GOT_STX,
    MAVLINK_PARSE_STATE_GOT_LENGTH,
    MAVLINK_PARSE_STATE_GOT_INCOMPAT_FLAGS,
    MAVLINK_PARSE_STATE_GOT_COMPAT_FLAGS,
    MAVLINK_PARSE_STATE_GOT_SEQ,
    MAVLINK_PARSE_STATE_GOT_SYSID,
    MAVLINK_PARSE_STATE_GOT_COMPID,
    MAVLINK_PARSE_STATE_GOT_MSGID1,
    MAVLINK_PARSE_STATE_GOT_MSGID2,
    MAVLINK_PARSE_STATE_GOT_MSGID3,
    MAVLINK_PARSE_STATE_GOT_PAYLOAD,
    MAVLINK_PARSE_STATE_GOT_CRC1,
    MAVLINK_PARSE_STATE_GOT_BAD_CRC1,
    MAVLINK_PARSE_STATE_SIGNATURE_WAIT
} mavlink_parse_state_t;

/// The current state of a Mavlink channel. A "channel" encapsulates one transport
/// resource (ie: a UART or TCP socket). Generally a user does not need to interact
/// with this struct beyond allocating it on startup and passing it to helper methods
/// if desired
typedef struct __mavlink_channel_state_t {
    uint8_t tx_seq; // current sequence id this channel is on to transmit
    mavlink_send_bytes_fn_t default_cb; // default function to use while sending bytes
    mavlink_parse_state_t rx_parse_state; // current state of this channels rx parsing machine
} mavlink_channel_state_t;

#endif /* __MAVLINK_TYPES_H__*/
