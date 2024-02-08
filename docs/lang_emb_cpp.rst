.. lang_emb_cpp

Language: Embedded C++
======================

Design Principles
-----------------

1. Keep implementation friendly for as small of an embedded device as possible

   - Avoid advanced C++ features (exceptions, RTTI)
   - Dont use dynamic allocation. This makes resource usage more deterministic
   - Dont use the STL for the above reasons
   - Many build-time options to fine-tuning library size

2. Minimize routing overhead

   - MAVLink objects are designed to minimize routing overhead/number of memcpy's in a situation where a node just wants to pass a message along.

