.. $URL$
.. $Rev$

What is PurePNG?
================

PurePNG is pure-Python package for reading and writing PNG.

PurePNG can read and write all PNG formats.  PNG supports a generous
variety of image formats: RGB or greyscale, with or without an alpha
channel; and a choice of bit depths from 1, 2 or 4 (as long as you want
greyscale or a pallete), 8, and 16 (but 16 bits is not allowed for
palettes).  A pixel can vary in size from 1 to 64 bits:
1/2/4/8/16/24/32/48/64.  In addition a PNG file can be `interlaced` or
not.  An interlaced file allows an incrementally refined display of
images being downloaded over slow links (yet it's not implemented in
PurePNG for now).

PurePNG is written in pure Python(that's why it's called `Pure`). So if
you write in Python you can understand code of PurePNG or inspect raw data
while debugging.

Comparison to other PNG tools
-----------------------------

The most obvious "competitor" to PurePNG is PIL.  Depending on what job
you want to do you might also want to use Netpbm (PurePNG can convert to
and from the Netpbm PNM format), or use :py:mod:`ctypes` to interface directly
to a compiled version of libpng.  If you know of others, let me know.

PIL's focus is not PNG.  PIL's focus is image processing, and this is where 
PurePNG sucks.  If you want to actually process an image---resize, rotate,
composite, crop--then you should use PIL. You may use `PIL Plugin`_ if you want
to use both PurePNG and PIL. In PurePNG you get the image as basically an array
of numbers.  So some image processing is possible fairly easily, for example
cropping to integer coordinates, or gamma conversion, but this very basic.

PurePNG can read and write Netpbm PAM files. PAM is useful as an intermediary
format for performing processing; it allows the pixel data to be transferred 
in a simple format that is easily processed.
Netpbm's support for PAM to PNG conversion is more limited than PurePNG's.
Netpbm will only convert a source PAM that has 4 channels (for example it does
not create greyscale--alpha PNG files from ``GRAYSCALE_ALPHA`` PAM files).
Netpbm's usual tool for create PNG files, ``pnmtopng``, requires an alpha
channel to be specified in a separate file.

PurePNG has good support for PNG's ``sBIT`` chunk.  This allows end to end
processing of files with any bit depth from 1 to 16 (for example a
10-bit scanner may use the ``sBIT`` chunk to declare that the samples in
a 16-bit PNG file are rescaled 10-bit samples; in this case, PurePNG
delivers 10-bit samples).  Netpbm handle's the ``sBIT`` chunk in a
similar way, but other toolsets may not (e.g. PIL with native plugin).

``libpng`` is made by the PNG gods, so if want to get at all that
goodness, then you may want to interface directly to libpng via
``ctypes``.  That could be a good idea for some things.  Installation
would be trickier.

Installation
------------

Because PurePNG is written in Python it's trivial to install into a Python
installation.  Just use ``python setup.py install``.

There is also "light" mode: you can just copy the :download:`../code/png/png.py` 
file.  You can even `curl` it straight into wherever you need it:
``curl -LO https://raw.githubusercontent.com/Scondo/purepng/master/code/png/png.py``.
This "light" module mode contains all features required for PNG reading and
writing, while "full" package mode contains extra features like Cython speedup,
other format support, PIL plugin etc.

PIL Plugin
----------
In "full" package PurePNG provide plugin for usage with PIL instead of PIL's
native PNG support. This plugin is in very early stage yet can be useful.
Just try it with ``from png import PngImagePlugin``

Benefit
^^^^^^^
* PurePNG rely on python's zlib instead of PIL. So this plugin can be useful when PIL built without zlib support.
* PurePNG handle ``sBIT`` chunk and rescale values if it's not correctly rescaled on write.
* PurePNG does not use separate palette or transparency when reading, providing full RGB and alpha channel instead.
* PurePNG should write gamma

Miss
^^^^
* PurePNG does not save custom chunks
* PurePNG does not use zlib dictionary and method (compression level used)


PurePNG compare to PyPNG
------------------------

PurePNG is fork of PyPNG - nice and simple module to work with png.

If you work with PyPNG in most cases you can use PurePNG as drop-in replace,
but few things are changed:

Buffer, not array
^^^^^^^^^^^^^^^^^

PyPNG document that rows in boxed flat row could be any sequence, but
in practice even unit-test check that it should be :py:class:`array.array`.
This changed from :py:class:`array.array` to any buffer-compatible sequence.

You can use :py:func:`buffer()` or :py:class:`memoryview()` functions to fetch row bytes
depending on your version of python if you have used :py:meth:`~array.array.tostring()` before.
And of course you may just use rows as sequence.

Python 2.2 no longer supported
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Most features were already broken in Python 2.2 and it couldn't be fixed.
So support of Python 2.2 is completely removed.

Python 2.2 is pretty old, you know?

PNM|PBM|PAM deprecated in module
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For now Netpbm image format kept in ``png`` module, but it will be moved
to a separate module within package.
So if you want to work with Netpbm images using PurePNG do not rely on
"light" module mode, use  "full" package. (see `Installation`_)