'''
Created on 27 may 2014

@author: Scondo
'''
import unittest
import pngsuite
from PIL import Image
from io import BytesIO

from PIL import PngImagePlugin as pilpng
from png import PngImagePlugin as purepng


class PilImageToPyPngAdapter:
    def __init__(self, im):
        self.im = im

    def __len__(self):
        return self.im.size[1]

    def __getitem__(self, row):
        out = []
        for col in range(self.im.size[0]):
            px = self.im.getpixel((col, row))
            if hasattr(px, '__iter__'):
                #Multi-channel image
                out.extend(px)
            else:
                #Single channel image
                out.append(px)
        return out


class BaseTest(unittest.TestCase):
    test_ = None

    def compareImages(self, im1, im2):
        if 'gamma' in im1.info:
            self.assertEqual(im1.info['gamma'], im2.info.get('gamma'))
        if im1.mode != im2.mode or im1.mode == 'P':
            im1 = im1.convert('RGBA')
            im2 = im2.convert('RGBA')
        pix1 = list(PilImageToPyPngAdapter(im1))
        pix2 = list(PilImageToPyPngAdapter(im2))
        if im1.mode == 'RGBA':
            self.assertEqual(pix1[0][3::4], pix2[0][3::4])  # alpha fast check
        self.assertEqual(pix1[0], pix2[0])  # fast check
        self.assertEqual(pix1, pix2)  # complete check


class ReadTest(BaseTest):
    def runTest(self):
        if self.test_ is None:
            return
        test_file = BytesIO(self.test_)
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
        test_file = BytesIO(self.test_)
        # Load via PIL default plugin
        reload(pilpng)
        im_orig = Image.open(test_file)
        # Save via PurePNG
        reload(purepng)
        pure_file = BytesIO()
        im_orig.save(pure_file, 'PNG')
        # Load again, plugin unimportant after read test
        pure_file.seek(0)
        im_new = Image.open(pure_file)
        self.compareImages(im_orig, im_new)

# Generate tests for each suite file
# Except known cases when fail caused by PIL
testsuite = pngsuite.png
del testsuite['tbbn1g04']
# grayscale + transparency does not provide alpha
del testsuite['Basn0g03']
# PIL ignore sBIT on 4bit greyscale, PurePNG provide more accuracy
for tname_, test_ in (testsuite.items()):
    globals()[tname_ + '_rtest'] = type(tname_ + '_rtest', (ReadTest,),
                                       {'test_': test_})
    globals()[tname_ + '_wtest'] = type(tname_ + '_wtest', (WriteTest,),
                                       {'test_': test_})

if __name__ == "__main__":
    unittest.main()
