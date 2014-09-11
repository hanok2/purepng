.. $URL$
.. $Rev$

Acceleration with Cython
========================

Part of png.py can be compiled with Cython to achieve better performance.
Compiled part is 'BaseFilter' class now.
Compilation use 'pngfilters.pxd' file do declare types and override functions.

Compilation
-----------
Compilation will be done automatically during setup process while Cython and c-compiler installed.
If you do not want to install binary-compiled part you may skip compilation 
using '--no-cython' option for setup.py.

When you use pypng without installation you may build cythonized code using
"setup.py build_ext --inplace"

Developing with Cython
----------------------
If you want to see how Cython compile it's part you can extract compiled part
into ``pngfilters.py`` using ``unimport.py`` and later compile with Cython like 
``cython pngfilters.py``
Be careful! You should remove ``pngfilters.py`` after compilation to avoid errors!

Main idea of PurePNG is polyglot so don't use any Cython-specific construction 
in ``png.py`` - you will broke pure-python mode which is core of all.
If you have want to improve performance using such things - separate this
in function and write twice: in ``png.py`` using pure-python syntax and in 
``pngfilters.pxd`` using cython and ``cdef inline``.

If you modify part of ``png.py`` that should be compiled and know nothing about
cython feel free to commit and pull request - someone should fix things you can
break before release.
So if you want to make release - pass unittest both with and without compiled part.