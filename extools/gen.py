#!/usr/bin/env python
# gen

"""gen [options] [pngsuitename]

Generate a PNG test image on stdout.
"""

from array import array
import math
import sys

import png


def test_radial_tl(x, y):
    return max(1 - math.sqrt(x * x + y * y), 0.0)


def test_stripe(x, n):
    return float(int(x * n) & 1)


def test_checker(x, y, n):
    return float((int(x * n) & 1) ^ (int(y * n) & 1))


PATTERN = {
    'GLR': lambda x, y: x,
    'GRL': lambda x, y: 1 - x,
    'GTB': lambda x, y: y,
    'GBT': lambda x, y: 1 - y,
    'RTL': test_radial_tl,
    'RTR': lambda x, y: test_radial_tl(1 - x, y),
    'RBL': lambda x, y: test_radial_tl(x, 1 - y),
    'RBR': lambda x, y: test_radial_tl(1 - x, 1 - y),
    'RCTR': lambda x, y: test_radial_tl(x - 0.5, y - 0.5),
    'HS2': lambda x, y: test_stripe(x, 2),
    'HS4': lambda x, y: test_stripe(x, 4),
    'HS10': lambda x, y: test_stripe(x, 10),
    'VS2': lambda x, y: test_stripe(y, 2),
    'VS4': lambda x, y: test_stripe(y, 4),
    'VS10': lambda x, y: test_stripe(y, 10),
    'LRS': lambda x, y: test_stripe(x + y, 10),
    'RLS': lambda x, y: test_stripe(1 + x - y, 10),
    'CK8': lambda x, y: test_checker(x, y, 8),
    'CK15': lambda x, y: test_checker(x, y, 15),
    'ZERO': lambda x, y: 0,
    'ONE': lambda x, y: 1,
}


def generate(options):
    """
    Create a PNG test image and write the file to stdout.
    """

    import re

    def test_pattern(width, height, bitdepth, pattern):
        """Create a single plane (monochrome) test pattern.  Returns a
        flat row flat pixel array.
        """

        maxval = 2**bitdepth - 1
        if maxval > 255:
            a = array('H')
        else:
            a = array('B')
        fw = float(width - 1)  # This compensate 0 element
        fh = float(height - 1)
        pfun = PATTERN[pattern]
        for y in range(height):
            fy = float(y) / fh
            for x in range(width):
                a.append(int(round(pfun(float(x) / fw, fy) * maxval)))
        return a

    def test_rgba(size=(256, 256), bitdepth=8,
                  red=None, green=None, blue=None, alpha=None):
        """
        Create a test image.  Each channel is generated from the
        specified pattern; any channel apart from red can be set to
        None, which will cause it not to be in the image.  It
        is possible to create all PNG channel types (L, RGB, LA, RGBA),
        as well as non PNG channel types (RGA, and so on).
        *size* is a pair: (*width*,*height).
        """

        i = test_pattern(size[0], size[1], bitdepth, red)
        psize = 1
        for channel in (green, blue, alpha):
            if channel:
                c = test_pattern(size[0], size[1], bitdepth, channel)
                i = png.MergedPlanes([i], psize, [c], 1).next()
                psize += 1
        return i

    # The body of test_suite()
    size = (256, 256)
    # Expect option of the form '64,40'.
    if options.size:
        size = re.findall(r'\d+', options.size)
        if len(size) not in [1, 2]:
            raise ValueError(
              'size should be one or two numbers, separated by punctuation')
        if len(size) == 1:
            size *= 2
        assert len(size) == 2
        size = map(int, size)
    options.bitdepth = options.depth
    options.greyscale = bool(options.black)

    kwargs = {}
    if options.red:
        kwargs["red"] = options.red
    if options.green:
        kwargs["green"] = options.green
    if options.blue:
        kwargs["blue"] = options.blue
    if options.alpha:
        kwargs["alpha"] = options.alpha
    if options.greyscale:
        if options.red or options.green or options.blue:
            raise ValueError("cannot specify colours (R, G, B) when "
                             "greyscale image (black channel, K) is specified")
        kwargs["red"] = options.black
        kwargs["green"] = None
        kwargs["blue"] = None
    options.alpha = bool(options.alpha)
    pixels = test_rgba(size, options.bitdepth, **kwargs)

    writer = png.Writer(size[0], size[1],
                    bitdepth=options.bitdepth,
                    transparent=options.transparent,
                    background=options.background,
                    gamma=options.gamma,
                    greyscale=options.greyscale,
                    alpha=options.alpha,
                    compression=options.compression,
                    interlace=options.interlace)
    if sys.platform == "win32":
        import msvcrt, os
        try:
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
        except:
            pass
    outfile = sys.stdout
    if hasattr(outfile, 'buffer'):
        outfile = outfile.buffer
    writer.write_array(outfile, pixels)


def color_triple(color):
    """
    Convert a command line colour value to a RGB triple of integers.
    FIXME: Somewhere we need support for greyscale backgrounds etc.
    """
    if color.startswith('#') and len(color) == 4:
        return (int(color[1], 16),
                int(color[2], 16),
                int(color[3], 16))
    if color.startswith('#') and len(color) == 7:
        return (int(color[1:3], 16),
                int(color[3:5], 16),
                int(color[5:7], 16))
    elif color.startswith('#') and len(color) == 13:
        return (int(color[1:5], 16),
                int(color[5:9], 16),
                int(color[9:13], 16))


def main(argv=None):
    import logging
    if argv is None:
        argv = sys.argv
    from optparse import OptionParser
    parser = OptionParser()

    parser.add_option('-p', '--patterns',
                      default=False, action='store_true',
                      help="print list of patterns")
    parser.add_option("-R", "--red",
                      action="store", type="string", metavar="pattern",
                      help="test pattern for the red image layer")
    parser.add_option("-G", "--green",
                      action="store", type="string", metavar="pattern",
                      help="test pattern for the green image layer")
    parser.add_option("-B", "--blue",
                      action="store", type="string", metavar="pattern",
                      help="test pattern for the blue image layer")
    parser.add_option("-A", "--alpha",
                      action="store", type="string", metavar="pattern",
                      help="test pattern for the alpha image layer")
    parser.add_option("-K", "--black",
                      action="store", type="string", metavar="pattern",
                      help="test pattern for greyscale image")
    parser.add_option("-d", "--depth",
                      default=8, action="store", type="int",
                      metavar='NBITS',
                      help="create test PNGs that are NBITS bits per channel")
    parser.add_option("-S", "--size",
                      action="store", type="string", metavar="w[,h]",
                      help="width and height of the test image")
    parser.add_option("-i", "--interlace",
                      default=False, action="store_true",
                      help="create an interlaced PNG file (Adam7)")
    parser.add_option("-t", "--transparent",
                      action="store", type="string", metavar="#RRGGBB",
                      help="mark the specified colour as transparent")
    parser.add_option("-b", "--background",
                      action="store", type="string", metavar="#RRGGBB",
                      help="save the specified background colour")
    parser.add_option("-g", "--gamma",
                      action="store", type="float", metavar="value",
                      help="save the specified gamma value")
    parser.add_option("-c", "--compression",
                      action="store", type="int", metavar="level",
                      help="zlib compression level (0-9)")

    (options, args) = parser.parse_args(args=argv[1:])
    if args:
        logging.warn("Args are not supported")

    if options.patterns:
        names = list(PATTERN)
        names.sort()
        for name in names:
            print (name,)
        return

    # Convert options
    if options.transparent is not None:
        options.transparent = color_triple(options.transparent)
    if options.background is not None:
        options.background = color_triple(options.background)

    generate(options)


if __name__ == '__main__':
    main()
