# PurePNG setup.py
# This is the setup.py script used by distutils.

# You can install the png module into your Python distribution with:
# python setup.py install
# You can also do other standard distutil type things, but you can refer
# to the distutil documentation for that.

# This script is also imported as a module by the Sphinx conf.py script
# in the man directory, so that this file forms a single source for
# metadata.

# http://docs.python.org/release/2.4.4/lib/module-sys.html
import sys
import os
from os.path import dirname, join

try:
    # http://peak.telecommunity.com/DevCenter/setuptools#basic-use
    from setuptools import setup
except ImportError:
    # http://docs.python.org/release/2.4.4/dist/setup-script.html
    from distutils.core import setup

cythonize = False
try:
    from Cython.Build import cythonize
except ImportError:
    cythonize = False  # just to be sure

def get_version():
    for line in open(join(dirname(__file__), 'code', 'png', 'png.py')):
        if '__version__' in line:
            version = line.split('"')[1]
            break
    return version

conf = dict(
    name='purepng',
    version=get_version(),
    description='Pure Python PNG image encoder/decoder',
    long_description="""
PurePNG allows PNG image files to be read and written using pure Python.

It's available from github.com
https://github.com/scondo/purepng
""",
    author='Pavel Zlatovratsky',
    author_email='scondo@mail.ru',
    url='https://github.com/scondo/purepng',
    package_dir={'png':join('code', 'png')},
    py_packages=['png'],
    classifiers=[
      'Topic :: Multimedia :: Graphics',
      'Topic :: Software Development :: Libraries :: Python Modules',
      'Programming Language :: Python',
      'Programming Language :: Python :: 2.3',
      'Programming Language :: Python :: 3',
      'License :: OSI Approved :: MIT License',
      'Operating System :: OS Independent',
      ],
    )

if __name__ == '__main__':
    if '--no-cython' in sys.argv:
        cythonize = False
        sys.argv.remove('--no-cython')

    if cythonize:
        from unimport import do_unimport
        cyth_ext = do_unimport(conf['package_dir']['png'])
        conf['ext_modules'] = cythonize(cyth_ext)

    setup(**conf)
    if cythonize:
        os.remove(cyth_ext)
