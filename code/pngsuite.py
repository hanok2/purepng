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

# Suite by names, but skip error tests and size(unsupported yet)
# Also skip national encoding
suite_files_b = [(splitext(f)[0], suite_file.extractfile(f))
               for f in suite_file.getnames() if
               not (f.startswith('x') or f.startswith('ctf') or
                    f.startswith('cth') or f.startswith('ctj') or
                    f.startswith('ctg'))]
png = dict(suite_files_b)
# test one file like this:
# png = {'tesst': suite_file.extractfile('ctzn0g04.png')}
# Extra png test by drj
suite_file = tarfile.open(os.path.join(os.path.dirname(__file__),
                                       "DrjExtraSuite.tgz"))
drj_png = dict([(splitext(f)[0], suite_file.extractfile(f))
            for f in suite_file.getnames()])

png.update(drj_png)
sys.modules[__name__].__dict__.update(png)
