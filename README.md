# Mavlib Gen

[![Library checks](https://github.com/len0rd/mavlib_gen/actions/workflows/base.yml/badge.svg?branch=main&event=push)](https://github.com/len0rd/mavlib_gen/actions/workflows/base.yml) [![Library coverage](https://codecov.io/gh/len0rd/mavlib_gen/branch/main/graph/badge.svg?token=4HDIQKTBN8)](https://codecov.io/gh/len0rd/mavlib_gen)

A [MAVLink](https://mavlink.io/en/) generator with a permissive MIT license. This project is for a MAVLink generator ONLY.
No additional features or tools will be included in this project.

## Language Support

Language         | Generator Status | Notes
-----------------|------------------|------
C                | 40%              |
Python           | 10%              |
Graphviz         | 100%             | Generates message structure diagrams for documentation
Embedded C++     | 20%              | C++ implementation with no STL or dynamic allocation
ReStructuredText | 90%              | Sphinx-compatible RST docs of messages that can also utilize the dot files produced by the graphviz generator

## Features

- [Capable of generation based on complex include trees](#complex-include-trees)
- [Simple, lean helper methods within generated code](#simple-lean-helper-methods)
- [Thorough unit tests](#thorough-unit-tests)
- [Versioned releases](#versioned-releases)

### Complex Include Trees

One feature I've wanted in pymavlink for quite some time is the ability to generate
mavlink code from more advanced include trees, such as the one below.

![example_of_complex_tree](docs/_img/complex_include_tree_ex.svg)

Such support allows developers to better isolate specific modules of a
MAVLink message system. Thus avoiding large, hard to navigate definition files.

### Simple, lean helper methods

*Stuff about parsing based on char arrays instead of single character*

### Thorough unit tests

Thorough tests on both the generator and the generated code mean user can have assurances the
library will work as expected with every update

### Versioned releases

Proper release versioning means compatibility can break between major versions. This becomes
increasingly important as the project ages to help keep code uncluttered and readable.

## TODO

- [ ] yaml-based generation configuration
- [ ] Use `@dataclass` for python-generated message classes
- [ ]  generator option to only regen on CRC_EXTRA changes
