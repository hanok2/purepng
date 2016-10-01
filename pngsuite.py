"""
PngSuite Test PNGs.

After you import this module with "import pngsuite" use
``pngsuite.bai0g01`` to get the bytes for a particular PNG image, or
use ``pngsuite.png`` to get a dict() of them all.
"""

import sys
import tarfile
import os.path
from os.path import splitext
suite_file = tarfile.open(os.path.join(os.path.dirname(__file__),
                                       "PngSuite-2013jan13.tgz"))
png = dict([(splitext(f)[0], suite_file.extractfile(f))
            for f in suite_file.getnames()])
# Extra png test by drj
# Gamma test from libpng.org (single colour)
extra_file = tarfile.open(os.path.join(os.path.dirname(__file__),
                                       "ExtraSuite.tgz"))
extra_png = dict([(splitext(f)[0], extra_file.extractfile(f))
            for f in extra_file.getnames()])
png.update(extra_png)
# test one file like this:
# png = {'tesst': suite_file.extractfile('ctzn0g04.png')}

sys.modules[__name__].__dict__.update(png)
