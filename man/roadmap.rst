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
* PIL plugin
* Raw iCCP read/write
* Text information (read tEXt and zTXt, write tEXt, partitially iTXt )
* pHYs support


Future
------
* Cython-accelerated scaling
* Support more chunks at least for direct reading|embeding.
* Provide optimisation functions like 'try to pallete' or 'try to greyscale'
* Integrate most tools (incl. picture formats) into package
* Other Cython acceleration when possible
