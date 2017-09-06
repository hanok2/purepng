# PurePNG setup.py
# This is the setup.py script used by distutils.

# You can install the png module into your Python distribution with:
# python setup.py install
# You can also do other standard distutil type things, but you can refer
# to the distutil documentation for that.

# This script is also imported as a module by the Sphinx conf.py script
# in the man directory, so that this file forms a single source for
# metadata.

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

from distutils.command.build_ext import build_ext as build_ext_orig
from distutils.errors import DistutilsError, CCompilerError, CompileError
import distutils


class build_ext_opt(build_ext_orig):
    """
    This is a version of the build_ext command that allow to fail build.

    As there is no reqired extension(only acceleration) with failed
    build_ext package still be usable.
    With `force` option this behavior disabled.
    """

    command_name = 'build_ext'

    def build_extension(self, ext):
        try:
            build_ext_orig.build_extension(self, ext)
        except (CCompilerError, DistutilsError, CompileError,
                Exception):
            e = sys.exc_info()[1]
            if self.force:
                raise
            logging.warn('building optional extension "%s" failed: %s' %
                     (ext.name, e))


distutils.command.build_ext.build_ext = build_ext_opt


try:
    def do_unimport(folder=''):
        """Do extraction of filters etc. into target folder"""
        src = open(join(folder, 'png.py'))
        try:
            os.remove(join(folder, 'pngfilters.py'))
        except:
            pass
        new = open(join(folder, 'pngfilters.py'), 'w')

        # Fixed part
        # Cython directives
        new.write('#cython: boundscheck=False\n')
        new.write('#cython: wraparound=False\n')

        go = False
        for line in src:
            if line.startswith('class') and\
                    (line.startswith('class BaseFilter')):
                go = True
            elif not (line.startswith('   ') or line.strip() == ''):
                go = False
            if go:
                new.write(line)
        new.close()
        return join(folder, 'pngfilters.py')
except BaseException:  # Whatever happens we could work without unimport
    cythonize = False  # at cost of disabled cythonize


def get_version():
    for line in open(join(dirname(__file__), 'png', 'png.py')):
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
PurePNG can read and write all PNG formats.
PNG supports a generous variety of image formats: RGB or greyscale, with or
without an alpha channel; and a choice of bit depths from 1, 2 or 4
(as long as you want greyscale or a pallete),
8, and 16 (but 16 bits is not allowed for palettes).
A pixel can vary in size from 1 to 64 bits: 1/2/4/8/16/24/32/48/64.
In addition a PNG file can be interlaced or not.
An interlaced file allows an incrementally refined display of images being
downloaded over slow links (yet it`s not implemented in PurePNG for now).

PurePNG is written in pure Python(that`s why it`s called Pure).
""",
    author='Pavel Zlatovratskii',
    author_email='scondo@mail.ru',
    url='https://github.com/scondo/purepng',
    package_dir={'png': 'png'},
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
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: Jython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Development Status :: 4 - Beta',
    ],
    license='MIT License',
    keywords=['png', 'Imaging'],
    zip_safe=True,
    install_requires=['argparse'],
    tests_require=['argparse']
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
