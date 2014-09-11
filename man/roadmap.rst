.. $URL$
.. $Rev$

Roadmap and versions
====================

PurePNG use odd/even minor version numbering with odd for development and even for stable versions.


PyPNG
-----
PyPNG with it's 0.0.* version could be treated as previous stable version of PurePNG.
David Jones works carefully on this.

0.1 ==> 0.2
-----------
Done
^^^^
* Reworked Cython concept.
* Add optional filtering on save.
* Module/package duality
* Python 2/3 polyglot (and partitial Cython)
* Using bytearray when possible.
* Rows in boxed flat row now may be any buffer-compatible, not only array.
* Python 2.2 support removed.

Planned
^^^^^^^
PIL plugin

Release
^^^^^^^
Suppose 0.1 will provide stable interface in the end of 2014. And after few month will be released as 0.2.

Future
------
* Cython-accelerated scaling
* Support more chunks at least for direct reading|embeding.
* Provide optimisation functions like 'try to pallete' or 'try to greyscale'
* Other Cython acceleration when possible
