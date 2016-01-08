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
import logging
from os.path import dirname, join

try:
    # http://peak.telecommunity.com/DevCenter/setuptools#basic-use
    from setuptools import setup
except ImportError:
    # http://docs.python.org/release/2.4.4/dist/setup-script.html
    from distutils.core import setup

try:
    from Cython.Build import cythonize
except ImportError:
    cythonize = False  # just to be sure

from distutils.command.build_ext import build_ext
from distutils.errors import DistutilsError, CCompilerError, CompileError


class build_ext_opt(build_ext):
    """
    This is a version of the build_ext command that allow to fail build.

    As there is no reqired extension(only acceleration) with failed
    build_ext package still be usable.
    With `force` option this behavior disabled.
    """

    command_name = 'build_ext'

    def build_extension(self, ext):
        try:
            build_ext.build_extension(self, ext)
        except (CCompilerError, DistutilsError, CompileError) as e:
            if self.force:
                raise
            logging.warn('building optional extension "%s" failed: %s' %
                     (ext.name, e))


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
    author='Pavel Zlatovratskii',
    author_email='scondo@mail.ru',
    url='https://github.com/scondo/purepng',
    package_dir={'png': join('code', 'png')},
    packages=['png'],
    classifiers=[
      'Topic :: Multimedia :: Graphics',
      'Topic :: Software Development :: Libraries :: Python Modules',
      'Programming Language :: Python',
      'Programming Language :: Python :: 2.3',
      'Programming Language :: Python :: 2.4',
      'Programming Language :: Python :: 2.5',
      'Programming Language :: Python :: 2.6',
      'Programming Language :: Python :: 2.7',
      'Programming Language :: Python :: 3.1',
      'Programming Language :: Python :: 3.2',
      'Programming Language :: Python :: 3.3',
      'Programming Language :: Python :: 3.4',
      'Programming Language :: Python :: Implementation :: CPython',
      'Programming Language :: Python :: Implementation :: Jython',
      'Programming Language :: Python :: Implementation :: PyPy',
      'License :: OSI Approved :: MIT License',
      'Operating System :: OS Independent',
      'Development Status :: 4 - Beta',
      ],
    )

if __name__ == '__main__':
    if '--no-cython' in sys.argv:
        cythonize = False
        sys.argv.remove('--no-cython')
    # Crude but simple check to disable cython when it's not needed
    if '--help' in sys.argv[1:]:
        cythonize = False
    commands = [it for it in sys.argv[1:] if not it.startswith('-')]
    no_c_need = ('check', 'upload', 'register', 'upload_docs', 'build_sphinx',
                 'saveopts', 'setopt', 'clean', 'develop', 'install_egg_info',
                 'egg_info', 'alias', )
    if not bool([it for it in commands if it not in no_c_need]):
        cythonize = False

    pre_cythonized = join(conf['package_dir']['png'], 'pngfilters.c')
    if cythonize:
        from unimport import do_unimport
        cyth_ext = do_unimport(conf['package_dir']['png'])
        conf['ext_modules'] = cythonize(cyth_ext)
        os.remove(cyth_ext)
    elif os.access(pre_cythonized, os.F_OK):
        from distutils.extension import Extension
        conf['ext_modules'] = [Extension('pngfilters',
                                         [pre_cythonized])]

    # cythonized filters clean
    if 'clean' in sys.argv:
        if os.access(pre_cythonized, os.F_OK):
            os.remove(pre_cythonized)

    setup(**conf)
