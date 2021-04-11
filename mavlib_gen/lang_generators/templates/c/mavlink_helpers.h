/// Helper methods for serializing/de-serializing mavlink messages
#ifndef __MAVLINK_HELPERS_H__
#define __MAVLINK_HELPERS_H__
#include "mavlink_types.h"


/// Attempt to parse the provided buffer into a message. Returns on the first
/// successfully parsed message
int mavlink_parse_buf(const uint8_t *buf_in, mavlink_message_t *msg_out, uint8_t parse_buf);


/// Send a message over a transport using the provided send_bytes function
///
/// @param chan_state
///     Current state for the channel this message is being sent out on.
/// @param msg_payload
///     Pointer to the begining of this messages payload. The payload is the actual message struct,
///     not a mavlink_message_t (which encapsulates a payload + all the header bytes)
/// @param msgid
///     The unique message id of the provided msg_payload
/// @param crc_extra
///     The CRC extra for this message. the crc_extra is the magic byte generated from the
///     message definition to help ensure platforms are using the same version of a message
/// @param len
///     Maximum length of the msg_payload
/// @param sysid
///     Source system id to use in this messages header
/// @param compid
///     Source component id to use in this messages header
/// @param tx_func
///     Pointer to a function that can be used to send message bytes. This may be called
///     multiple times to send a single message
int mavlink_tx_msg_cb(mavlink_channel_state_t *chan_state, const void* msg_payload, uint32_t msgid,
        uint8_t crc_extra, uint8_t len, uint8_t sysid, uint8_t compid, mavlink_send_bytes_fn_t tx_func);

inline int mavlink_tx_msg_cb(mavlink_channel_state_t *chan_state, const void* msg_payload,
        const mavlink_info_t *msg_info, uint8_t sysid, uint8_t compid, mavlink_send_bytes_fn_t tx_func) {
    return mavlink_tx_msg_cb(chan_state, msg_payload, msg_info->msgid, msg_info->crc_extra,
            msg_info->len, sysid, compid, tx_func);
}

inline int mavlink_tx_msg_cb(mavlink_channel_state_t *chan_state, const void* msg_payload,
        const mavlink_info_t *msg_info, uint8_t sysid, uint8_t compid) {
    return mavlink_tx_msg_cb(chan_state, msg_payload, msg_info->msgid, msg_info->crc_extra,
            msg_info->len, sysid, compid, chan_state->default_cb);
}

#endif /* __MAVLINK_HELPERS_H__ */
