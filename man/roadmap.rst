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
0.1.1 is feature freeze and 0.2 is about to release.
Just wait some time to be sure about bugs.
Examples and tests are subject to change.

0.3 ==> 0.4
-----------
* Provide optimisation functions like 'try to pallete' or 'try to greyscale'
* Separate pnm support to module within package
* Rework iccp module to become part of package
* Better text support
* Enhance PIL plugin, support 'raw' reading with palette handled by PIL

Future
------
* Cython-accelerated scaling
* Support more chunks at least for direct reading|embeding.
* Integrate most tools (incl. picture formats) into package
* Other Cython acceleration when possible
