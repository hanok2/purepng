"""
PurePNG core self-test

This file comprises the tests that are internally validated (as
opposed to tests which produce output files that are externally
validated).  Primarily they are unittests.

Note that it is difficult to internally validate the results of
writing a PNG file.  The only thing we can do is read it back in
again, which merely checks consistency, not that the PNG file we
produce is valid.
"""

from __future__ import generators
import logging
# logging.getLogger().setLevel(logging.INFO)

# (For an in-memory binary file IO object) We use BytesIO where
# available, otherwise we use StringIO, but name it BytesIO.
try:
    from io import BytesIO
except ImportError:
    from StringIO import StringIO as BytesIO

import struct
# http://www.python.org/doc/2.4.4/lib/module-unittest.html
import unittest
import zlib
import itertools
import datetime
import tarfile
import os.path

try:
    from itertool import izip as zip
except ImportError:
    pass

try:
    from functools import reduce
except ImportError:
    # suppose to get there on python<2.7 where reduce is only built-in function
    pass

try:
    from png import array
except ImportError:
    # It's not worth add array to Py3 import when no need for hacks
    from array import array

import png
import png.pnm2png
import pngsuite
import sys

from png import strtobytes      # Don't do this at home.


def buf_emu(not_buffer):
    """Buffer emulator"""
    if hasattr(not_buffer, 'tostring'):
        return not_buffer.tostring()
    else:
        try:
            return bytes(not_buffer)
        except NameError:
            return str(not_buffer)
try:
    buffer
except NameError:
    try:
        buffer = memoryview
    except NameError:
        buffer = buf_emu


def group(s, n):
    """Repack iterator items into groups"""
    # See http://www.python.org/doc/2.6/library/functions.html#zip
    return list(zip(*[iter(s)] * n))


def topngbytes(name, rows, x, y, **k):
    """
    Convenience function for creating a PNG file "in memory" as a string.

    Creates a :class:`Writer` instance using the keyword arguments, then
    passes `rows` to its :meth:`Writer.write` method.
    The resulting PNG file is returned as a string.  `name` is used
    to identify the file for debugging.
    """
    import os

    logging.info(name)
    f = BytesIO()
    w = png.Writer(x, y, **k)
    w.write(f, rows)
    if os.environ.get('PYPNG_TEST_TMP'):
        w = open(name, 'wb')
        w.write(f.getvalue())
        w.close()
    return f.getvalue()


def _redirect_io(inp, out, f):
    """
    Calls the function `f` redirecting stdin and stdout to `inp` and `out`.

    They are restored when `f` returns.
    This function returns whatever `f` returns.
    """

    import os

    oldin, sys.stdin = sys.stdin, inp
    oldout, sys.stdout = sys.stdout, out
    try:
        x = f()
    finally:
        sys.stdin = oldin
        sys.stdout = oldout
    if os.environ.get('PYPNG_TEST_TMP') and hasattr(out,'getvalue'):
        name = mycallersname()
        if name:
            w = open(name+'.png', 'wb')
            w.write(out.getvalue())
            w.close()
    return x


def mycallersname():
    """
    Returns the name of the caller of the caller of this function

    (hence the name of the caller of the function in which
    "mycallersname()" textually appears).  Returns None if this cannot
    be determined.
    """
    # http://docs.python.org/library/inspect.html#the-interpreter-stack
    import inspect

    frame = inspect.currentframe()
    if not frame:
        return None
    frame_,filename_,lineno_,funname,linelist_,listi_ = (
      inspect.getouterframes(frame)[2])
    return funname


def seqtobytes(s):
    """
    Convert a sequence of integers to a *bytes* instance.

    Good for plastering over Python 2 / Python 3 cracks.
    """
    return strtobytes(''.join([chr(x) for x in s]))


class Test(unittest.TestCase):

    """Main test unit"""

    def helperLN(self, n):
        """Helper for L-tests"""
        mask = (1 << n) - 1
        # Use small chunk_limit so that multiple chunk writing is tested.
        w = png.Writer(15, 17, greyscale=True, bitdepth=n, chunk_limit=99)
        f = BytesIO()
        w.write_array(f, array('B', [mask & it for it in range(1, 256)]))
        r = png.Reader(bytes=f.getvalue())
        x, y, pixels, _ = r.read()
        self.assertEqual(x, 15)
        self.assertEqual(y, 17)
        self.assertEqual(list(itertools.chain(*pixels)),
                         [mask & it for it in range(1, 256)])

    def testL8(self):
        """Test L with depth 8"""
        return self.helperLN(8)

    def testL4(self):
        """Test L with depth 4"""
        return self.helperLN(4)

    def testL2(self):
        """Test L with depth 2. Also tests asRGB8."""
        w = png.Writer(1, 4, greyscale=True, bitdepth=2)
        f = BytesIO()
        w.write_array(f, array('B', range(4)))
        r = png.Reader(bytes=f.getvalue())
        x, y, pixels, _ = r.asRGB8()
        self.assertEqual(x, 1)
        self.assertEqual(y, 4)
        for i, row in enumerate(pixels):
            self.assertEqual(len(row), 3)
            self.assertEqual(list(row), [0x55*i]*3)

    def testP2(self):
        """2-bit palette."""
        a = (255,255,255)
        b = (200,120,120)
        c = (50,99,50)
        w = png.Writer(1, 4, bitdepth=2, palette=[a,b,c])
        f = BytesIO()
        w.write_array(f, array('B', (0,1,1,2)))
        r = png.Reader(bytes=f.getvalue())
        x,y,pixels,meta = r.asRGB8()
        self.assertEqual(x, 1)
        self.assertEqual(y, 4)
        self.assertEqual([list(p) for p in pixels], [list(p) for p in (a, b, b, c)])

    def testPtrns(self):
        """Test colour type 3 and tRNS chunk (and 4-bit palette)."""
        a = (50,99,50,50)
        b = (200,120,120,80)
        c = (255,255,255)
        d = (200,120,120)
        e = (50,99,50)
        w = png.Writer(3, 3, bitdepth=4, palette=[a,b,c,d,e])
        f = BytesIO()
        w.write_array(f, array('B', (4, 3, 2, 3, 2, 0, 2, 0, 1)))
        r = png.Reader(bytes=f.getvalue())
        x,y,pixels,meta = r.asRGBA8()
        self.assertEqual(x, 3)
        self.assertEqual(y, 3)
        c = c+(255,)
        d = d+(255,)
        e = e+(255,)
        boxed = [(e,d,c),(d,c,a),(c,a,b)]
        flat = [itertools.chain(*row) for row in boxed]
        self.assertEqual([list(it) for it in pixels],
                         [list(it) for it in flat])

    def testRGBtoRGBA(self):
        """asRGBA8() on colour type 2 source."""
        # Also test that png.Reader can take a "file-like" object.
        pngsuite.png["basn2c08"].seek(0)
        r = png.Reader(pngsuite.basn2c08)
        x, y, pixels, meta = r.asRGBA8()
        # Test the pixels at row 9 columns 0 and 1.
        row9 = list(pixels)[9]
        self.assertEqual(list(row9[0:8]),
                         [0xff, 0xdf, 0xff, 0xff, 0xff, 0xde, 0xff, 0xff])

        # More testing: rescale and bitdepth > 8
        pngsuite.basn2c16.seek(0)
        r = png.Reader(pngsuite.basn2c16)
        x, y, pixels, meta = r.asRGBA8()
        # Test the pixels at row 9 columns 0 and 1.
        row9 = list(pixels)[9]
        self.assertEqual(list(row9[0:8]),
                         [255, 181, 0, 255, 247, 181, 0, 255])

    def testLtoRGBA(self):
        """asRGBA() on grey source."""
        pngsuite.basi0g08.seek(0)
        r = png.Reader(pngsuite.basi0g08)
        x,y,pixels,meta = r.asRGBA()
        row9 = list(list(pixels)[9])
        self.assertEqual(row9[0:8],
          [222, 222, 222, 255, 221, 221, 221, 255])

    def testCtrns(self):
        """Test colour type 2 and tRNS chunk."""
        pngsuite.tbrn2c08.seek(0)
        r = png.Reader(pngsuite.tbrn2c08)
        x,y,pixels,meta = r.asRGBA8()
        # I just happen to know that the first pixel is transparent.
        # In particular it should be #7f7f7f00 (changed to #ffffff00 in 2011)
        row0 = list(pixels)[0]
        self.assertEqual(tuple(row0[0:4]), (0xff, 0xff, 0xff, 0x00))

    def testAdam7read(self):
        """
        Adam7 interlace reading.

        Specifically, test that for images in the PngSuite that
        have both an interlaced and straightlaced pair that both
        images from the pair produce the same array of pixels.
        """
        for candidate in pngsuite.png:
            if not candidate.startswith('basn'):
                continue
            candi = candidate.replace('n', 'i')
            if candi not in pngsuite.png:
                continue
            logging.info('adam7 read' + candidate)
            straight = png.Reader(pngsuite.png[candidate])
            adam7 = png.Reader(pngsuite.png[candi])
            pngsuite.png[candidate].seek(0)
            pngsuite.png[candi].seek(0)
            # Just compare the pixels.  Ignore x,y (because they're
            # likely to be correct?); metadata is ignored because the
            # "interlace" member differs.  Lame.
            straight = straight.read()[2]
            adam7 = adam7.read()[2]
            self.assertEqual([list(it) for it in straight],
                             [list(it) for it in adam7])

    def testAdam7write(self):
        """
        Adam7 interlace writing.

        For each test image in the PngSuite, write an interlaced
        and a straightlaced version.  Decode both, and compare results.
        """
        # Not such a great test, because the only way we can check what
        # we have written is to read it back again.
        # Check different filter modes: default by number; default by name;
        #                              adaptive by name; adaptive by dict
        for filtertype in (0, 1, 2, 'average', 'paeth',
                           'sum', {'name': 'entropy'}):
            for name, file_ in pngsuite.png.items():
                # Only certain colour types supported for this test.
                if name[3:5] not in ['n0', 'n2', 'n4', 'n6'] or\
                        not name.lower().startswith('basn'):
                    continue
                file_.seek(0)
                it = png.Reader(file_)
                x, y, pixels, _ = it.read()
                # straightlaced is easier to filter, so we test interlaced
                # using straight as reference
                pngi = topngbytes('adam7wn' + name + '.png', pixels,
                                  x=x, y=y, bitdepth=it.bitdepth,
                                  greyscale=it.greyscale, alpha=it.alpha,
                                  transparent=it.transparent,
                                  interlace=False, filter_type=0)

                x, y, ps, _ = png.Reader(bytes=pngi).read()
                file_.seek(0)
                it = png.Reader(file_)
                x, y, pixels, _ = it.read()
                pngs = topngbytes('adam7wi' + name + '.png', pixels,
                                  x=x, y=y, bitdepth=it.bitdepth,
                                  greyscale=it.greyscale, alpha=it.alpha,
                                  transparent=it.transparent,
                                  interlace=True, filter_type=filtertype)
                x, y, pi, _ = png.Reader(bytes=pngs).read()
                self.assertEqual([list(it) for it in ps], [list(it) for it in pi])

    def testLA4(self):
        """Create an LA image with bitdepth 4."""
        bytes = topngbytes('la4.png', [[5, 12]], 1, 1,
          greyscale=True, alpha=True, bitdepth=4)
        sbit = png.Reader(bytes=bytes).chunk('sBIT')[1]
        self.assertEqual(sbit, strtobytes('\x04\x04'))

    def testPal(self):
        """Test that a palette PNG returns the palette in info."""
        pngsuite.basn3p04.seek(0)
        r = png.Reader(pngsuite.basn3p04)
        x,y,pixels,info = r.read()
        self.assertEqual(x, 32)
        self.assertEqual(y, 32)
        self.assertEqual('palette' in info, True)

    def testBkdgPal(self):
        """Test background in palleted image"""
        pngsuite.tbyn3p08.seek(0)
        r = png.Reader(pngsuite.tbyn3p08)
        info = r.read()[3]
        # TODO: in fact it would be much better if 'background' will return
        # usual three-tuple
        pal = info['palette']
        bkgd_idx = info['background'][0]
        # Opague yellow
        self.assertEqual(pal[bkgd_idx], (255, 255, 0, 255))

    def testBkdg(self):
        """Test simple RGB background"""
        pngsuite.bgwn6a08.seek(0)
        r = png.Reader(pngsuite.bgwn6a08)
        info = r.read()[3]
        # white background
        self.assertEqual(info['background'], (255, 255, 255))

    def testPalWrite(self):
        """Test palette kept intact after writing and re-reading"""
        pngsuite.png['basn3p04'].seek(0)
        r = png.Reader(pngsuite.png['basn3p04'])
        pixels, info = r.read()[2:]
        w = png.Writer(**info)
        o = BytesIO()
        w.write(o, pixels)
        o.flush()
        o.seek(0)
        r = png.Reader(file=o)
        again_info = r.read()[3]
        # Same palette
        self.assertEqual(again_info['palette'], info['palette'])

    def testBkgdWrite(self):
        """Test write(change) simple background"""
        pngsuite.bgwn6a08.seek(0)
        r = png.Reader(pngsuite.bgwn6a08)
        _, _, pixels, info = r.read()
        info['background'] = (0, 0, 255)
        w = png.Writer(**info)
        o = BytesIO()
        w.write(o, pixels)
        o.flush()
        o.seek(0)
        r = png.Reader(file=o)
        info = r.read()[3]
        # blue background
        self.assertEqual(info['background'], (0, 0, 255))

    def testPalExpand(self):
        """Test that bitdepth can be used to fiddle with pallete image."""
        pngsuite.png['basn3p04'].seek(0)
        r = png.Reader(pngsuite.png['basn3p04'])
        pixels, info = r.read()[2:]
        pixels = [list(row) for row in pixels]
        info['bitdepth'] = 8
        w = png.Writer(**info)
        o = BytesIO()
        w.write(o, pixels)
        o.flush()
        o.seek(0)
        r = png.Reader(file=o)
        again_pixels = r.read()[2]
        # Same pixels
        again_pixels = [list(row) for row in again_pixels]
        self.assertEqual(again_pixels, pixels)

    def testLtrns0(self):
        """Create greyscale image with tRNS chunk."""
        return self.helperLtrns(0)

    def testLtrns1(self):
        """Using 1-tuple for transparent arg."""
        return self.helperLtrns((0,))

    def helperLtrns(self, transparent):
        """Helper used by :meth:`testLtrns*`."""
        pixels = zip([0x00, 0x38, 0x4c, 0x54, 0x5c, 0x40, 0x38, 0x00])
        o = BytesIO()
        w = png.Writer(8, 8, greyscale=True, bitdepth=1, transparent=transparent)
        w.write_packed(o, pixels)
        r = png.Reader(bytes=o.getvalue())
        meta = r.asDirect()[3]
        self.assertEqual(meta['alpha'], True)
        self.assertEqual(meta['greyscale'], True)
        self.assertEqual(meta['bitdepth'], 1)

    def testPhyAspect(self):
        """
        Test that resolution is read and could be correctly applied

        The first (cdf) image is an example of flat (horizontal) pixels,
        where the pHYS chunk (x is 1 per unit, y = 4 per unit) must take
        care of the correction. The second is just the other way round.
        """
        pngsuite.png['cdfn2c08'].seek(0)
        r = png.Reader(pngsuite.png['cdfn2c08'])
        x, y, pixels, info = r.read()
        self.assertEqual('resolution' in info, True)
        self.assertEqual(x / info['resolution'][0][0],
                         y / info['resolution'][0][1])

        pngsuite.png['cdhn2c08'].seek(0)
        r = png.Reader(pngsuite.png['cdhn2c08'])
        x, y, pixels, info = r.read()
        self.assertEqual('resolution' in info, True)
        self.assertEqual(x / info['resolution'][0][0],
                         y / info['resolution'][0][1])

    def testPhyResolution(self):
        """
        Test that resolutions is read and represent printing size

        This should result in a picture of 3.2 cm square.
        """
        pngsuite.png['cdun2c08'].seek(0)
        r = png.Reader(pngsuite.png['cdun2c08'])
        x, y, _, info = r.read()
        self.assertEqual('resolution' in info, True)
        self.assertEqual(info['resolution'][1], 1)  # unit is meter
        self.assertEqual(float(x) / info['resolution'][0][0], 0.032)
        self.assertEqual(float(y) / info['resolution'][0][1], 0.032)

    def testPhyWrite(self):
        """
        Test that resolution is correctly written

        This should result in a picture of 3.2 cm square.
        """
        pngsuite.png['basn0g16'].seek(0)
        r = png.Reader(pngsuite.png['basn0g16'])
        x, y, pixels, info = r.read()
        info['resolution'] = (10, 'cm')  # 10 pixel per cm
        test_phy = topngbytes('test_phy.png', pixels, x, y, **info)
        x, y, pixels, info_r = png.Reader(bytes=test_phy).read()
        self.assertEqual('resolution' in info_r, True)
        self.assertEqual(info_r['resolution'][1], 1)  # unit is meter
        self.assertEqual(float(x) / info_r['resolution'][0][0], 0.032)
        self.assertEqual(float(y) / info_r['resolution'][0][1], 0.032)

        # Another way of encoding
        pngsuite.png['basn0g16'].seek(0)
        r = png.Reader(pngsuite.png['basn0g16'])
        x, y, pixels, info = r.read()
        info['resolution'] = (1000, 1000, 'm')  # 10 pixel per cm
        test_phy = topngbytes('test_phy.png', pixels, x, y, **info)
        x, y, pixels, info_r = png.Reader(bytes=test_phy).read()
        self.assertEqual('resolution' in info_r, True)
        self.assertEqual(info_r['resolution'][1], 1)  # unit is meter
        self.assertEqual(float(x) / info_r['resolution'][0][0], 0.032)
        self.assertEqual(float(y) / info_r['resolution'][0][1], 0.032)

    def testWinfo(self):
        """
        Test the dictionary returned by a `read` method can be used
        as args for :meth:`Writer`.
        """
        pngsuite.png['basn2c16'].seek(0)
        r = png.Reader(file=pngsuite.png['basn2c16'])
        info = r.read()[3]
        png.Writer(**info)

    def testText(self):
        """Test text information saving and retrieving"""
        # Use image as core for text
        pngsuite.png['basn2c16'].seek(0)
        r = png.Reader(file=pngsuite.png['basn2c16'])
        x, y, pixels, info = r.read()

        text = {'Software': 'PurePNG library',
                'Source': 'PNGSuite',
                'Comment': 'Text information test'}
        # Simple unicode test
        try:
            unic = unichr
        except NameError:
            unic = chr
        # Unicode only by type should be saved to tEXt
        text['Author'] = strtobytes('Pavel Zlatovratskii').decode('latin-1')
        # Non-latin unicode should go to iTXt
        # 'Be careful with unicode!' in russian.
        text['Warning'] = reduce(lambda x, y: x + unic(y),
                                 (1054, 1089, 1090, 1086, 1088, 1086, 1078,
                                  1085, 1077, 1081, 32, 1089, 32, 1102, 1085,
                                  1080, 1082, 1086, 1076, 1086, 1084, 33),
                                 '')
        # Embedded keyword test
        info_e = dict(info)  # copy
        info_e.update(text)
        test_e = topngbytes('text_e.png', pixels, x, y, **info_e)
        x, y, pixels, info_r = png.Reader(bytes=test_e).read()
        self.assertEqual(text, info_r.get('text'))

        # Separate argument test
        info_a = dict(info)
        info_a['text'] = text
        # Here we can use any keyword, not only registered
        info_a['text']['Goddamn'] = 'I can do ANYTHING!'
        test_a = topngbytes('text_a.png', pixels, x, y, **info_a)
        x, y, pixels, info_r = png.Reader(bytes=test_a).read()
        self.assertEqual(text, info_r.get('text'))

    def testCreateTime(self):
        """Test text of creation time (with data conversion from datetime)"""
        # Use image as core for text
        pngsuite.png['basn2c16'].seek(0)
        r = png.Reader(file=pngsuite.png['basn2c16'])
        x, y, pixels, info = r.read()
        info1 = dict(info)
        # In fact this is 4004 B.C. ;)
        info1["Creation Time"] = datetime.datetime(4004, 10, 21, 9, 13)
        test = topngbytes('text_cr-tim.png', pixels, x, y, **info1)
        x, y, pixels, info_r = png.Reader(bytes=test).read()
        txt = info_r.get('text')
        if txt is not None:
            self.assertEqual("4004-10-21T09:13:00", txt.get("Creation Time"))
        else:
            raise AssertionError("No text with Creation Time")

    def testCreateTimeTu(self):
        """Test text of creation time (with data conversion from tuple)"""
        # Use image as core for text
        pngsuite.png['basn2c16'].seek(0)
        r = png.Reader(file=pngsuite.png['basn2c16'])
        x, y, pixels, info = r.read()
        info1 = dict(info)
        # In fact this is 4004 B.C. ;)
        info1["Creation Time"] = (4004, 10, 21, 9, 13)
        test = topngbytes('text_cr-tim.png', pixels, x, y, **info1)
        x, y, pixels, info_r = png.Reader(bytes=test).read()
        txt = info_r.get('text')
        if txt is not None:
            self.assertEqual("4004-10-21T09:13:00", txt.get("Creation Time"))
        else:
            raise AssertionError("No text with Creation Time")

    def testTIMEChunkIO(self):
        """Consistency write/read test of tIME chunk"""
        pixels = [range(0, 8)] * 8
        io = BytesIO()
        p = dict(size=(len(pixels[0]), len(pixels)), modification_time=True)
        w = png.Writer(**p)
        w.write(io, pixels)
        io.seek(0)
        r = png.Reader(file=io)
        r.read()
        # Trim milliseconds, timezone, etc.
        self.assertEqual(w.modification_time[:6],
                         r.last_mod_time[:6])

    def testcHRM(self):
        """Test reading chrome chunk for colour correction"""
        pngsuite.png['Arc-cHRM-rgswap'].seek(0)
        r = png.Reader(pngsuite.png['Arc-cHRM-rgswap'])
        info = r.read()[3]
        self.assertEqual(info['white_point'], (0.31270, 0.32900))
        self.assertEqual(info['rgb_points'], ((0.30000, 0.60000),
                                              (0.64000, 0.33000),
                                              (0.15000, 0.06000)))

    def testcHRMwrite(self):
        """Test writing (and re-reading) chrome chunk for colour correction"""
        pixels = [range(0, 8)] * 8
        io = BytesIO()
        w = png.Writer(size=(len(pixels[0]), len(pixels)))
        w.set_white_point(0.31270, 0.32900)
        w.set_rgb_points(0.30000, 0.60000, 0.64000, 0.33000, 0.15000, 0.06000)
        w.write(io, pixels)
        io.seek(0)
        r = png.Reader(file=io)
        info = r.read()[3]
        self.assertEqual(info['white_point'], (0.31270, 0.32900))
        self.assertEqual(info['rgb_points'], ((0.30000, 0.60000),
                                              (0.64000, 0.33000),
                                              (0.15000, 0.06000)))

    def testsRGB(self):
        """Test reading sRGB chunk for colour correction"""
        pngsuite.png['ff99ff_sRGB'].seek(0)
        r = png.Reader(pngsuite.png['ff99ff_sRGB'])
        info = r.read()[3]
        self.assertEqual(info['rendering_intent'], png.ABSOLUTE_COLORIMETRIC)

    def testsRGBwrite(self):
        """Test writing (and re-reading) sRGB chunk for colour correction"""
        pixels = [range(0, 8)] * 8
        io = BytesIO()
        w = png.Writer(size=(len(pixels[0]), len(pixels)),
                       rendering_intent=png.PERCEPTUAL)
        w.write(io, pixels)
        io.seek(0)
        r = png.Reader(file=io)
        info = r.read()[3]
        self.assertEqual(info['rendering_intent'], png.PERCEPTUAL)

    def testPackedIter(self):
        """Test iterator for row when using write_packed."""
        w = png.Writer(16, 2, greyscale=True, alpha=False, bitdepth=1)
        o = BytesIO()
        w.write_packed(o, [itertools.chain([0x0a], [0xaa]),
                           itertools.chain([0x0f], [0xff])])
        r = png.Reader(bytes=o.getvalue())
        x,y,pixels,info = r.asDirect()
        pixels = list(pixels)
        self.assertEqual(len(pixels), 2)
        self.assertEqual(len(pixels[0]), 16)

    def testPaletteForcealpha(self):
        """Test forcing alpha channel for palette"""
        pngsuite.png['basn3p04'].seek(0)
        r = png.Reader(pngsuite.png['basn3p04'])
        r.preamble()
        r.palette(alpha='force')

    def testInterlacedBuffer(self):
        """
        Test buffer compatibility for interlace

        Test that reading an interlaced PNG yields each row as
        buffer-compatible type.
        """
        pngsuite.basi0g08.seek(0)
        r = png.Reader(pngsuite.basi0g08)
        buffer(list(r.read()[2])[0])

    def testTrnsBuffer(self):
        """
        Test buffer compatibility

        Test that reading a type 2 PNG with tRNS chunk yields each
        row as buffer-compatible type (using asDirect).
        """
        pngsuite.tbrn2c08.seek(0)
        r = png.Reader(pngsuite.tbrn2c08)
        buffer(list(r.asDirect()[2])[0])

    # Invalid file format tests.  These construct various badly
    # formatted PNG files, then feed them into a Reader.  When
    # everything is working properly, we should get FormatError
    # exceptions raised.
    def testEmpty(self):
        """Test empty file."""
        r = png.Reader(bytes='')
        self.assertRaises(png.FormatError, r.asDirect)

    def testSigOnly(self):
        """Test file containing just signature bytes."""
        pngsuite.png['basi0g01'].seek(0)
        r = png.Reader(bytes=pngsuite.png['basi0g01'].read(8))
        self.assertRaises(png.FormatError, r.asDirect)

    def testExtraPixels(self):
        """Test file that contains too many pixels."""
        def eachchunk(chunk):
            if chunk[0] != 'IDAT':
                return chunk
            data = zlib.decompress(chunk[1])
            data += strtobytes('\x00garbage')
            data = zlib.compress(data)
            chunk = (chunk[0], data)
            return chunk
        self.assertRaises(png.FormatError, self.helperFormat, eachchunk)

    def testNotEnoughPixels(self):
        """Test file without sufficient data"""
        def eachchunk(chunk):
            if chunk[0] != 'IDAT':
                return chunk
            # Remove last byte.
            data = zlib.decompress(chunk[1])
            data = data[:-1]
            data = zlib.compress(data)
            return (chunk[0], data)
        self.assertRaises(png.FormatError, self.helperFormat, eachchunk)

    def testBadChecksum(self):
        """Incorrect checksum"""
        # header
        pngsuite.png['xhdn0g08'].seek(0)
        r = png.Reader(pngsuite.png['xhdn0g08'])
        self.assertRaises(png.ChunkError, r.asDirect)
        # IDAT
        pngsuite.png['xcsn0g01'].seek(0)
        r = png.Reader(pngsuite.png['xcsn0g01'])
        pixels = r.asDirect()[2]
        self.assertRaises(png.FormatError, list, pixels)

    def testBadSignature(self):
        """Tests for bad signature"""
        # signature byte 1 MSBit reset to zero
        pngsuite.png['xs1n0g01'].seek(0)
        r = png.Reader(pngsuite.png['xs1n0g01'])
        self.assertRaises(png.FormatError, r.asDirect)
        # signature byte 2 is a 'Q'
        pngsuite.png['xs2n0g01'].seek(0)
        r = png.Reader(pngsuite.png['xs2n0g01'])
        self.assertRaises(png.FormatError, r.asDirect)
        # signature byte 4 lowercase
        pngsuite.png['xs4n0g01'].seek(0)
        r = png.Reader(pngsuite.png['xs4n0g01'])
        self.assertRaises(png.FormatError, r.asDirect)
        # 7th byte a space instead of control-Z
        pngsuite.png['xs7n0g01'].seek(0)
        r = png.Reader(pngsuite.png['xs7n0g01'])
        self.assertRaises(png.FormatError, r.asDirect)

    def testBadColour(self):
        """Tests for incorrect colour"""
        # colour type 1
        pngsuite.png['xc1n0g08'].seek(0)
        r = png.Reader(pngsuite.png['xc1n0g08'])
        self.assertRaises(png.FormatError, r.asDirect)
        # colour type 9
        pngsuite.png['xc9n2c08'].seek(0)
        r = png.Reader(pngsuite.png['xc9n2c08'])
        self.assertRaises(png.FormatError, r.asDirect)

    def testBadDepth(self):
        """Test incorrect bitdepth"""
        # bit-depth 0
        pngsuite.png['xd0n2c08'].seek(0)
        r = png.Reader(pngsuite.png['xd0n2c08'])
        self.assertRaises(png.FormatError, r.asDirect)
        # bit-depth 3
        pngsuite.png['xd3n2c08'].seek(0)
        r = png.Reader(pngsuite.png['xd3n2c08'])
        self.assertRaises(png.FormatError, r.asDirect)
        # bit-depth 99
        pngsuite.png['xd9n2c08'].seek(0)
        r = png.Reader(pngsuite.png['xd9n2c08'])
        self.assertRaises(png.FormatError, r.asDirect)

    def helperFormat(self, f):
        """
        Helper for format tests

        call `f` function to change chunks
        """
        pngsuite.basn0g01.seek(0)
        r = png.Reader(pngsuite.basn0g01)
        o = BytesIO()

        def newchunks():
            """chunks conversion"""
            for chunk in r.chunks():
                yield f(chunk)
        png.write_chunks(o, newchunks())
        r = png.Reader(bytes=o.getvalue())
        return list(r.asDirect()[2])

    def testBadFilter(self):
        def eachchunk(chunk):
            if chunk[0] != 'IDAT':
                return chunk
            data = zlib.decompress(chunk[1])
            # Corrupt the first filter byte
            data = strtobytes('\x99') + data[1:]
            data = zlib.compress(data)
            return (chunk[0], data)
        self.assertRaises(png.FormatError, self.helperFormat, eachchunk)

    def testChun(self):
        """Chunk doesn't have length and type."""
        pngsuite.png['basi0g01'].seek(0)
        r = png.Reader(bytes=pngsuite.png['basi0g01'].read()[:13])
        try:
            r.asDirect()
        except Exception:
            e = sys.exc_info()[1]
            self.assertEqual(isinstance(e, png.FormatError), True)
            self.assertEqual('chunk length' in str(e), True)

    def testChunkShort(self):
        """Chunk that is too short."""
        pngsuite.png['basi0g01'].seek(0)
        r = png.Reader(bytes=pngsuite.png['basi0g01'].read()[:21])
        try:
            r.asDirect()
        except Exception:
            e = sys.exc_info()[1]
            self.assertEqual(isinstance(e, png.ChunkError), True)
            self.assertEqual('too short' in str(e), True)

    def testNoChecksum(self):
        """Chunk that's too small to contain a checksum."""
        pngsuite.png['basi0g01'].seek(0)
        r = png.Reader(bytes=pngsuite.png['basi0g01'].read()[:29])
        try:
            r.asDirect()
        except Exception:
            e = sys.exc_info()[1]
            self.assertEqual(isinstance(e, png.ChunkError), True)
            self.assertEqual('checksum' in str(e), True)

    def testFlat(self):
        """Test read_flat."""
        try:
            from hashlib import md5
        except ImportError:
            # On Python 2.4 there is no hashlib,
            # but there is special module for md5
            from md5 import md5
        pngsuite.png['basn0g02'].seek(0)
        r = png.Reader(pngsuite.png['basn0g02'])
        pixel = r.read_flat()[2]
        d = md5(seqtobytes(pixel)).hexdigest()
        self.assertEqual(d, '255cd971ab8cd9e7275ff906e5041aa0')

    def testfromarray(self):
        """Test writing files from array"""
        img = png.from_array([[0, 0x33, 0x66], [0xff, 0xcc, 0x99]], 'L')
        img.save(BytesIO())

    def testfromarrayL16(self):
        """Test writing 16-bit files from array"""
        img = png.from_array(group(range(2**16), 256), 'L;16')
        img.save(BytesIO())

    def testfromarrayRGB(self):
        """Test 1-bit RGB files from array"""
        img = png.from_array([[0,0,0, 0,0,1, 0,1,0, 0,1,1],
                              [1,0,0, 1,0,1, 1,1,0, 1,1,1]], 'RGB;1')
        o = BytesIO()
        img.save(o)

    def testfromarrayIter(self):
        """Test writing from iterator"""
        i = itertools.islice(itertools.count(10), 20)
        i = [[x, x, x] for x in i]
        img = png.from_array(i, 'RGB;5', dict(height=20))
        f = BytesIO()
        img.save(f)

    def testfromarrayWrong(self):
        """Test incorrect mode handling"""
        try:
            png.from_array([[1]], 'gray')
        except png.Error:
            return
        assert 0, "Expected from_array() to raise png.Error exception"

    def testfromarrayShortMode(self):
        """Test saving with shortened mode (no ';')"""
        png.from_array([[0,1],[2,3]], 'L2').save(BytesIO())
        # TODO: read to check

    def paeth(self, x, a, b, c):
        """Paeth reference code"""
        p = a + b - c
        pa = abs(p - a)
        pb = abs(p - b)
        pc = abs(p - c)
        if pa <= pb and pa <= pc:
            pr = a
        elif pb <= pc:
            pr = b
        else:
            pr = c
        return x - pr

    # test filters and unfilters
    def testFilterScanlineFirstLine(self):
        """Test filter without previous line"""
        line = array('B', [30, 31, 32, 230, 231, 232])
        filter_ = png.Filter(24, prev=None)
        res = filter_.filter_all(line)

        # none
        self.assertEqual(list(res[0]), [0, 30, 31, 32, 230, 231, 232])
        # sub
        self.assertEqual(list(res[1]), [1, 30, 31, 32, 200, 200, 200])
        # up
        self.assertEqual(list(res[2]), [2, 30, 31, 32, 230, 231, 232])
        # average
        self.assertEqual(list(res[3]), [3, 30, 31, 32, 215, 216, 216])
        # paeth
        self.assertEqual(list(res[4]),
            [4, self.paeth(30, 0, 0, 0), self.paeth(31, 0, 0, 0),
            self.paeth(32, 0, 0, 0), self.paeth(230, 30, 0, 0),
            self.paeth(231, 31, 0, 0), self.paeth(232, 32, 0, 0)])

    def testFilterScanline(self):
        """Test filtering with previous line"""
        prev = array('B', [20, 21, 22, 210, 211, 212])
        line = array('B', [30, 32, 34, 230, 233, 236])
        filter_ = png.Filter(24, prev=prev)
        res = filter_.filter_all(line)
        # None
        self.assertEqual(list(res[0]), [0, 30, 32, 34, 230, 233, 236])
        # sub
        self.assertEqual(list(res[1]), [1, 30, 32, 34, 200, 201, 202])
        # up
        self.assertEqual(list(res[2]), [2, 10, 11, 12, 20, 22, 24])
        # average
        self.assertEqual(list(res[3]), [3, 20, 22, 23, 110, 112, 113])
        # paeth
        self.assertEqual(list(res[4]),
            [4, self.paeth(30, 0, 20, 0), self.paeth(32, 0, 21, 0),
            self.paeth(34, 0, 22, 0), self.paeth(230, 30, 210, 20),
            self.paeth(233, 32, 211, 21), self.paeth(236, 34, 212, 22)])

    def testUnfilterScanline(self):
        """Test unfiltering"""
        scanprev = array('B', [20, 21, 22, 210, 211, 212])
        scanline = array('B', [30, 32, 34, 230, 233, 236])

        def undo_filter(filter_type, line, prev):
            """undoing filter"""
            filter_ = png.Filter(24, prev=prev)
            line = array('B', line)
            return filter_.undo_filter(filter_type, line)

        out = undo_filter(0, scanline, scanprev)
        self.assertEqual(list(out), list(scanline))  # none
        out = undo_filter(1, scanline, scanprev)
        self.assertEqual(list(out), [30, 32, 34, 4, 9, 14])  # sub
        out = undo_filter(2, scanline, scanprev)
        self.assertEqual(list(out), [50, 53, 56, 184, 188, 192])  # up
        out = undo_filter(3, scanline, scanprev)
        self.assertEqual(list(out), [40, 42, 45, 99, 103, 108])  # average
        out = undo_filter(4, scanline, scanprev)
        self.assertEqual(list(out), [50, 53, 56, 184, 188, 192])  # paeth

    def testUnfilterScanlinePaeth(self):
        """This tests more edge cases in the paeth unfilter"""
        scanprev = array('B', [2, 0, 0, 0, 9, 11])
        scanline = array('B', [4, 6, 10, 9, 100, 101, 102])
        filter_ = png.Filter(24, prev=scanprev)

        out = filter_.undo_filter(scanline[0], scanline[1:])
        self.assertEqual(list(out), [8, 10, 9, 108, 111, 113])  # paeth

    def testModifyRows(self):
        """
        Tests that the rows yielded by the pixels generator
        can be safely modified.
        """
        k = 'f02n0g08'
        pngsuite.png[k].seek(0)
        r1 = png.Reader(bytes=pngsuite.png[k].read())
        pngsuite.png[k].seek(0)
        r2 = png.Reader(bytes=pngsuite.png[k].read())
        pixels1 = r1.asDirect()[2]
        pixels2 = r2.asDirect()[2]
        for row1, row2 in zip(pixels1, pixels2):
            self.assertEqual(row1, row2)
            for i in range(len(row1)):
                row1[i] = 11117 % (i + 1)


extra_file = tarfile.open(os.path.join(os.path.dirname(__file__),
                                       "Misc.tgz"))


# Cli tests work only with package
class CliTest(unittest.TestCase):
    """Test for command-line utility"""
    def testPBMin(self):
        """Test that the command line tool can read PBM files."""
        s = extra_file.extractfile('feep.pbm')
        s.seek(0)
        o = BytesIO()
        _redirect_io(s, o, lambda: png.pnm2png.main(['testPBMin']))
        r = png.Reader(bytes=o.getvalue())
        r.read()
        self.assertEqual(r.greyscale, True)
        self.assertEqual(r.bitdepth, 1)

    def testPGMin(self):
        """Test that the command line tool can read PGM files."""
        s = BytesIO()
        s.write(strtobytes('P5 2 2 3\n'))
        s.write(strtobytes('\x00\x01\x02\x03'))
        s.flush()
        s.seek(0)
        o = BytesIO()
        _redirect_io(s, o, lambda: png.pnm2png.main(['testPGMin']))
        r = png.Reader(bytes=o.getvalue())
        r.read()
        self.assertEqual(r.greyscale, True)
        self.assertEqual(r.bitdepth, 2)

    def testPAMin(self):
        """Test that the command line tool can read PAM file."""
        s = BytesIO()
        s.write(strtobytes('P7\nWIDTH 3\nHEIGHT 1\nDEPTH 4\nMAXVAL 255\n'
                'TUPLTYPE RGB_ALPHA\nENDHDR\n'))
        # The pixels in flat row flat pixel format
        flat = [255,0,0,255, 0,255,0,120, 0,0,255,30]
        asbytes = seqtobytes(flat)
        s.write(asbytes)
        s.flush()
        s.seek(0)
        o = BytesIO()
        _redirect_io(s, o, lambda: png.pnm2png.main(['testPAMin']))
        r = png.Reader(bytes=o.getvalue())
        pixels = r.read()[2]
        self.assertEqual(r.alpha, True)
        self.assertEqual(not r.greyscale, True)
        self.assertEqual(list(itertools.chain(*pixels)), flat)

    def testPNMsbit(self):
        """Test that PNM files can generates sBIT chunk."""
        s = BytesIO()
        s.write(strtobytes('P6 8 1 1\n'))
        for pixel in range(8):
            s.write(struct.pack('<I', (0x4081 * pixel) & 0x10101)[:3])
        s.flush()
        s.seek(0)
        o = BytesIO()
        _redirect_io(s, o, lambda: png.pnm2png.main(['testPNMsbit']))
        r = png.Reader(bytes=o.getvalue())
        sbit = r.chunk('sBIT')[1]
        self.assertEqual(sbit, strtobytes('\x01\x01\x01'))

    def testPNMWrite(self):
        """Test writing of 'pnm' file"""
        o = BytesIO()
        pixels = [[0, 1, 2],
                  [3, 0, 1],
                  [2, 3, 0]]
        meta = dict(alpha=False, greyscale=True, bitdepth=2, planes=1)
        png.pnm2png.write_pnm(o, 3, 3, pixels, meta)

try:
    import numpy

    class NumPyTest(unittest.TestCase):

        """
        NumPy dependent tests.

        These are skipped (with a warning message) if numpy cannot be imported.
        """

        def testNumpyuint16(self):
            """numpy uint16."""
            rows = [[numpy.uint16(it) for it in range(0, 0x10000, 0x5555)]]
            topngbytes('numpyuint16.png', rows, 4, 1,
                       greyscale=True, alpha=False, bitdepth=16)

        def testNumpyuint8(self):
            """numpy uint8."""
            rows = [[numpy.uint8(it) for it in range(0, 0x100, 0x55)]]
            topngbytes('numpyuint8.png', rows, 4, 1,
                       greyscale=True, alpha=False, bitdepth=8)

        def testNumpybool(self):
            """numpy bool."""
            rows = [[numpy.bool(it) for it in (0, 1)]]
            topngbytes('numpybool.png', rows, 2, 1,
                       greyscale=True, alpha=False, bitdepth=1)

        def testNumpyarray(self):
            """numpy array."""
            pixels = numpy.array([[0, 0x5555],
                                  [0x5555, 0xaaaa]], numpy.uint16)
            img = png.from_array(pixels, 'L')
            img.save(BytesIO())

        def testPalette(self):
            """Palette as NumPy array"""
            s = ['110010010011',
                 '101011010100',
                 '110010110101',
                 '100010010011']
            s = list(map(lambda x: list(map(int, x)), s))
            palette = [(0x55, 0x55, 0x55), (0xff, 0x99, 0x99)]
            palette_np = numpy.array(palette)  # creates a 2x3 array

            png.Writer(len(s[0]), len(s), palette=palette_np, bitdepth=1)

except ImportError:
    logging.warn("skipping numpy test")

if __name__ == "__main__":
    unittest.main()
