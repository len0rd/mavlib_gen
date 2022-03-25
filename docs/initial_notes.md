# c_mavlinkgen



## Desireds

* Smart regeneration - keep files of previously generated xml. compare against current xml generation to see which messages/headers need to be regenerated?
* Better freakin stat and error reporting (`mavlink_status_t` is a bloody mess)
  * #define to enable/disable health and stat reporting
* better architected helper methods, that allow the user to decide whether they want to use mavlinks internal buffers or provide their own
  * improve rx parsing method to accept a buffer of data.
  * If parsing of a message fails, move to the next STX found in the current internal buffer (dont just throw away the entire failed message), this would probably prevent a couple of packet drops (not a ton)
* actual unit tests of generated code (gtest)
* generator library/generated code is easy to extend
  * way to add additional field offset values to the metadata struct? ie: i want to know the offset of field 'x' in message ids 100-200
  * or other #defines or fields to the schema.
    * it would be really cool to define ACK message id in the schema of a command so it could be somehow generated into the code



## Necessary changes for complex include trees

* *dialect/dialect*.h should only include `MAVLINK_MESSAGE_CRCS/_INFOS`, etc for messages in the specific dialect ONLY. ie: common.h `MAVLINK_MESSAGE_CRCS` -> `MAVLINK_COMMON_MESSAGE_CRCS`
* *dialect*/mavlink.h is responsible for appending the relevant `MAVLINK_DIALECT_MESSAGE_CRCS` etc into `MAVLINK_MESSAGE_CRCS`, etc
  * should work such that a single dialect and its includes can be exported or function independently
* Add a top level mavlink.h (not in a *dialect*/ folder) that includes/appends all dialects that were used in generation together
  * Need to somehow work out include tree? top-level mavlink.h should only include child nodes (dialects that are not included by other dialtects)



## Questions

* Keep in C? Or move to C++?
* Use pymavlink's formatter/find and replace tool? Seems pretty good
  * No. Use Jinja


