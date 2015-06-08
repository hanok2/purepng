# pngsuite.py

# PngSuite Test PNGs.

"""After you import this module with "import pngsuite" use
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
drj_file = tarfile.open(os.path.join(os.path.dirname(__file__),
                                     "DrjExtraSuite.tgz"))
drj_png = dict([(splitext(f)[0], drj_file.extractfile(f))
            for f in drj_file.getnames()])
png.update(drj_png)
# Gamma test from libpng.org (single colour)
gamma_file = tarfile.open(os.path.join(os.path.dirname(__file__),
                                     "gamma.tgz"))
gamma_png = dict([(splitext(f)[0], drj_file.extractfile(f))
            for f in drj_file.getnames()])
png.update(gamma_png)
# test one file like this:
# png = {'tesst': suite_file.extractfile('ctzn0g04.png')}

sys.modules[__name__].__dict__.update(png)
