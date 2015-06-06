'''
Created on 27 may 2014

@author: Scondo
'''


def safe_repr(obj, short=False):
    _MAX_LENGTH = 80
    try:
        result = repr(obj)
    except Exception:
        result = object.__repr__(obj)
    if not short or len(result) < _MAX_LENGTH:
        return result
    return result[:_MAX_LENGTH] + ' [truncated]...'

try:
    set
except NameError:
    from sets import Set as set

import unittest
import pngsuite
from PIL import Image
from io import BytesIO

from PIL import PngImagePlugin as pilpng
from png import PngImagePlugin as purepng

try:
    reload
except NameError:
    from imp import reload

try:
    unicode
except NameError:
    unicode = str

class PilImageToPyPngAdapter:
    def __init__(self, im):
        self.im = im
        self.nowrow = 0

    def __len__(self):
        return self.im.size[1]

    def __next__(self):
        if self.nowrow >= self.__len__():
            raise StopIteration()
        else:
            self.nowrow += 1
            return self.__getitem__(self.nowrow - 1)
    next = __next__

    def __iter__(self):
        return self

    def __getitem__(self, row):
        out = []
        for col in range(self.im.size[0]):
            px = self.im.getpixel((col, row))
            if hasattr(px, '__iter__'):
                # Multi-channel image
                out.extend(px)
            else:
                # Single channel image
                out.append(px)
        return out


class BaseTest(unittest.TestCase):
    test_ = None
    delta = 0

    def assertAlmostEqual(self, first, second,
                          places=None, msg=None, delta=None):
        """Updated version which can handle iterables

           Fail if the two objects are unequal as determined by their
           difference rounded to the given number of decimal places
           (default 7) and comparing to zero, or by comparing that the
           between the two objects is more than the given delta.

           Note that decimal places (from zero) are usually not the same
           as significant digits (measured from the most signficant digit).

           If the two objects compare equal then they will automatically
           compare almost equal.
        """
        if first == second:
            # shortcut
            return
        if delta is not None and places is not None:
            raise TypeError("specify delta or places not both")
        if delta is not None and places is None:
            places = 7

        def valuecompare(value1, value2):
            if value1 == value2:
                # shortcut
                return

            if delta is not None:
                if abs(value1 - value2) <= delta:
                    return
                standardMsg = '%s != %s within %s delta' % (safe_repr(value1),
                                                        safe_repr(value2),
                                                        safe_repr(delta))
            else:  # if delta is not None:
                if round(abs(value1 - value2), places) == 0:
                    return
                standardMsg = '%s != %s within %r places' % (safe_repr(value1),
                                                          safe_repr(value2),
                                                          places)
            return standardMsg

        def compareIters(first, second):
            passed = []
            errmsg = None
            for v1, v2 in zip(first, second):
                if hasattr(v1, '__iter__') and hasattr(v2, '__iter__'):
                    mymsg = compareIters(v1, v2)
                else:
                    mymsg = valuecompare(v1, v2)

                if mymsg is None:
                    # clean
                    passed.append(v1)
                else:
                    if errmsg is None:
                        errmsg = mymsg + '\n['
                    errmsg = errmsg + ('' if errmsg.endswith('\n') else '\n')
                    errmsg = errmsg + '\n'.join([repr(p) for p in passed])
                    errmsg = errmsg + ('' if errmsg.endswith('\n') else '\n')
                    errmsg = errmsg + ' - ' + repr(v1)
                    errmsg = errmsg + '\n + ' + repr(v2)
                    passed = []

            if errmsg is not None:
                errmsg = errmsg + ']'
            return errmsg

        if hasattr(first, '__iter__') and hasattr(second, '__iter__'):
            standardMsg = compareIters(first, second)
        else:
            standardMsg = valuecompare(first, second)

        if standardMsg is not None:
            msg = self._formatMessage(msg, standardMsg)
            raise self.failureException(msg)

    def assertDictEqual(self, d1, d2, msg=None):
        keys = set(d1.keys())
        keys.union(set(d2.keys()))
        for key_ in keys:
            val1 = d1.get(key_)
            val2 = d2.get(key_)
            if isinstance(val2, unicode) and not isinstance(val1, unicode):
                # try someway
                val2 = val2.encode('utf-8')
            self.assertEqual(val1, val2,
                             'Unequal values for key ' + repr(key_))

    def compareImages(self, im1, im2):
        self.assertEqual(im1.size, im2.size)
        # Copy info before clean it as PIL may rely on this while reading
        info1 = dict(im1.info)
        info2 = dict(im2.info)
        # Transparency will be converted to alpha later
        if 'transparency' in info1:
            del info1['transparency']
        if 'transparency' in info2:
            del info2['transparency']
        # Interlace does not affect image, only way it saved
        if 'interlace' in info1:
            del info1['interlace']
        if 'interlace' in info2:
            del info2['interlace']
        self.longMessage = True
        self.assertDictEqual(info1, info2)
        # compare pixels
        if im1.mode != im2.mode or im1.mode == 'P':
            im1 = im1.convert('RGBA')
            im2 = im2.convert('RGBA')

        pix1 = PilImageToPyPngAdapter(im1)
        pix2 = PilImageToPyPngAdapter(im2)

        if im1.mode == 'RGBA':
            self.assertAlmostEqual(pix1[0][3::4], pix2[0][3::4],
                                   delta=self.delta)  # alpha fast check
        self.assertAlmostEqual(pix1[0], pix2[0],
                               delta=self.delta)  # fast check
        self.assertAlmostEqual(pix1, pix2, delta=self.delta)  # complete check


class ReadTest(BaseTest):
    def runTest(self):
        if self.test_ is None:
            return
        test_file = self.test_
        # Load via PurePNG
        reload(purepng)
        im_pure = Image.open(test_file)
        im_pure.load()
        test_file.seek(0)
        # Load via PIL default plugin
        reload(pilpng)
        im_pil = Image.open(test_file)
        self.compareImages(im_pil, im_pure)


class WriteTest(BaseTest):
    def runTest(self):
        if self.test_ is None:
            return
        test_file = self.test_
        # Load via PIL default plugin
        test_file.seek(0)
        reload(pilpng)
        im_orig = Image.open(test_file)
        # Save via PurePNG
        reload(purepng)
        pure_file = BytesIO()
        pure_file.name = type(self).__name__
        im_orig.save(pure_file, 'PNG')
        # Load again, plugin unimportant after read test
        pure_file.seek(0)
        im_new = Image.open(pure_file)
        self.compareImages(im_orig, im_new)

# Generate tests for each suite file
# Except known cases when fail caused by PIL
testsuite = pngsuite.png

# Greyscale + transparency does not provide alpha
del testsuite['tbbn0g04']
del testsuite['tbwn0g16']


def getdelta(testname):
    if testname.endswith('16'):
        return 1
    elif testname == 'Basn0g03':
        # PIL ignore sBIT on 4bit greyscale, PurePNG provide more accuracy
        return 7
    else:
        return 0

for tname_, test_ in (testsuite.items()):
    globals()[tname_ + '_rtest'] = type(tname_ + '_rtest', (ReadTest,),
                                       {'test_': test_,
                                        'delta': getdelta(tname_)})
    globals()[tname_ + '_wtest'] = type(tname_ + '_wtest', (WriteTest,),
                                       {'test_': test_,
                                        'delta': getdelta(tname_)})

if __name__ == "__main__":
    unittest.main()
