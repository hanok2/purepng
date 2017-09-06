#!/usr/bin/env python
"""Generate a PNG test image."""

from array import array
import math
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
    """Create a PNG test image and write the file to stdout."""
    import re

    def test_pattern(width, height, bitdepth, pattern):
        """
        Create a single plane (monochrome) test pattern.

        Returns a flat row flat pixel array.
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
                  rgb=(None, None, None), alpha=None):
        """
        Create a test image.

        Each channel is generated from the
        specified pattern; any channel apart from red can be set to
        None, which will cause it not to be in the image.  It
        is possible to create all PNG channel types (L, RGB, LA, RGBA),
        as well as non PNG channel types (RGA, and so on).
        *size* is a pair: (*width*,*height).
        """
        i = test_pattern(size[0], size[1], bitdepth, rgb[0])
        psize = 1
        for channel in (rgb[1], rgb[2], alpha):
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
        if len(size) not in (1, 2):
            raise ValueError('size should be one or two numbers, '
                             'separated by punctuation')
        if len(size) == 1:
            size *= 2
        assert len(size) == 2
        size = map(int, size)

    if options.black:
        if options.red or options.green or options.blue:
            raise ValueError("cannot specify colours (R, G, B) when "
                             "greyscale image (black channel, K) is specified")
        rgb = (options.black, None, None)
    else:
        if not options.red or not options.green or not options.blue:
            raise ValueError("all colours (R, G, B) should be specified")

        rgb = (options.red, options.green, options.blue)

    pixels = test_rgba(size, options.depth, rgb, options.alpha)
    writer = png.Writer(size[0], size[1],
                        bitdepth=options.depth,
                        transparent=options.transparent,
                        background=options.background,
                        gamma=options.gamma,
                        greyscale=bool(options.black),
                        alpha=bool(options.alpha),
                        compression=options.compression,
                        interlace=options.interlace)
    writer.write_array(options.outfile, pixels)


def color_triple(color):
    """Convert a command line colour value to a RGB triple of integers."""
    # FIXME: Somewhere we need support for greyscale backgrounds etc.
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


def main(args=None):
    import argparse
    parser = argparse.ArgumentParser(description="Generate a PNG test image.")
    parser.add_argument("-p", "--patterns", action="store_true",
                        help="print list of patterns")
    parser.add_argument("-R", "--red", metavar="pattern",
                        help="test pattern for the red image layer")
    parser.add_argument("-G", "--green", metavar="pattern",
                        help="test pattern for the green image layer")
    parser.add_argument("-B", "--blue", metavar="pattern",
                        help="test pattern for the blue image layer")
    parser.add_argument("-A", "--alpha", metavar="pattern",
                        help="test pattern for the alpha image layer")
    parser.add_argument("-K", "--black", metavar="pattern",
                        help="test pattern for greyscale image")
    parser.add_argument("-d", "--depth", type=int, metavar='NBITS',
                        default=8,
                        help="create test PNGs that are "
                        "NBITS bits per channel")
    parser.add_argument("-S", "--size", metavar="w[,h]",
                        help="width and height of the test image")
    parser.add_argument("-i", "--interlace", action="store_true",
                        help="create an interlaced PNG file (Adam7)")
    parser.add_argument("-t", "--transparent", type=color_triple,
                        metavar="#RRGGBB",
                        help="mark the specified colour as transparent")
    parser.add_argument("-b", "--background", type=color_triple,
                        metavar="#RRGGBB",
                        help="save the specified background colour")
    parser.add_argument("-g", "--gamma", type=float, metavar="value",
                        help="save the specified gamma value")
    parser.add_argument("-c", "--compression", type=int, metavar="level",
                        help="zlib compression level (0-9)")
    parser.add_argument('outfile', type=argparse.FileType(mode='wb'),
                        nargs='?', default='-',
                        help="resulting file")
    arguments = parser.parse_args(args)  # if args is None sys.argv[1:] is used

    if arguments.patterns:
        names = list(PATTERN)
        names.sort()
        for name in names:
            print(name,)
    else:
        generate(arguments)


if __name__ == '__main__':
    main()
