A mavlink C lang generator with a permissive MIT license

## Features

- [Capable of generation based on complex include trees](#complex-include-trees)
- Simple, lean helper methods
- Thorough unit tests

### Complex Include Trees

One feature I've wanted in pymavlink for quite some time is the ability to generate
mavlink code from more advanced include trees, such as the one below.

**ADVANCED TREE HERE**

Such support allows developers to better separate/isolate specific modules of a
messaging system. Thus avoiding large, hard to navigate files.

### Simple, lean helper methods

*Stuff about parsing based on char arrays instead of single character*
