"""
This is a command-line utility to convert
`Netpbm <http://netpbm.sourceforge.net/>`_ PNM files to PNG, and the
reverse conversion from PNG to PNM. The interface is similar to that
of the ``pnmtopng`` program from Netpbm.  Type ``python pnm2png.py --help``
at the shell prompt for usage and a list of options.
"""
import sys
import struct
try:
    exec("from . import png", globals(), locals())
    exec("from .png import array", globals(), locals())
except (SyntaxError, ValueError):
    # On Python < 2.5 relative import cause syntax error
    import png
    from png import array
try:
    bytearray
    bytes
except NameError:
    # bytearray missed on Python < 2.6 where ralative import supported
    from png import bytearray
    bytes = str


def read_int_tokens(infile, n, allow_eof=False):
    """
    Read ASCII integers separated with whitespaces as list of length `n`

    Skip comments started with '#' to the end of line
    If comment starts right after digit and newline starts with digit
    these digits form single number.
    """
    result = []
    EOF = [False]  # Hack to allow modification in nested function

    # We may consume less or more than one line, so characters read one by one
    def getc():
        c = infile.read(1)
        if not c:
            if not allow_eof or EOF[0]:
                raise png.Error('premature End of file')
            else:
                # small hack to simulate trailing whitespace at the end of file
                EOF[0] = True   # but only once
                return ' '
        return c
    token = bytes()
    while True:
        c = getc()
        if c.isspace():
            if token:
                # post-token whitespace, save token
                result.append(int(token))
                if len(result) == n:
                    # we get here on last whitespace
                    break
                # and clean for new token
                token = bytes()
            # Skip whitespace that precedes a token or between tokens.
        elif c == png.strtobytes('#'):
            # Skip comments to the end of line.
            infile.readline()
            # If there is no whitespaces after conventional newline
            # continue reading token
        elif c.isdigit():
            token += c
        else:
            raise png.Error('unexpected character %s found ' % c)
    return result


def ascii_scanlines(infile, width, height, planes, bitdepth):
    """
    Generates boxed rows in flat pixel format, from the input file.

    It assumes that the input file is in a "Netpbm-like"
    ASCII format, and is positioned at the beginning of the first
    pixel.  The number of pixels to read is taken from the image
    dimensions (`width`, `height`, `planes`) and the number of bytes
    per value is implied by the image `bitdepth`.
    """
    # Values per row
    vpr = width * planes
    if bitdepth > 8:
        assert bitdepth == 16
        typecode = 'H'
    else:
        typecode = 'B'
    for _ in range(height):
        line = read_int_tokens(infile, vpr, True)
        yield array(typecode, line)


def pbmb_scanlines(infile, width, height):
    """
    Generates boxed rows in flat pixel format, from the PBM input file.

    It assumes that the input file is in a "Netpbm-like"
    binary format, and is positioned at the beginning of the first
    pixel.  The number of pixels to read is taken from the image
    dimensions (`width`, `height`).
    """
    def int2bitseq(byte):
        """Crude but simple way to unpack byte to bits"""
        if isinstance(byte, (str, bytes)):
            byte = ord(byte)
        res = bytearray()
        for _ in range(8):
            (byte, bit) = divmod(byte, 2)
            res.append(bit)
        return res

    tail = bytearray()
    for _ in range(height):
        while len(tail) < width:
            byte = infile.read(1)
            tail.extend(int2bitseq(byte))
        yield bytearray(tail[:width])
        tail = tail[width:]


def file_scanlines(infile, width, height, planes, bitdepth):
    """
    Generates boxed rows in flat pixel format, from the input file.

    It assumes that the input file is in a "Netpbm-like"
    binary format, and is positioned at the beginning of the first
    pixel.  The number of pixels to read is taken from the image
    dimensions (`width`, `height`, `planes`) and the number of bytes
    per value is implied by the image `bitdepth`.
    """
    # Values per row
    vpr = width * planes
    row_bytes = vpr
    if bitdepth > 8:
        assert bitdepth == 16
        row_bytes *= 2
        fmt = '>%dH' % vpr

        def line():
            return array('H', struct.unpack(fmt, infile.read(row_bytes)))
    else:
        def line():
            return bytearray(infile.read(row_bytes))
    for _ in range(height):
        yield line()


def write_pnm(fileobj, width, height, pixels, meta):
    """Write a Netpbm PNM/PAM file."""
    bitdepth = meta['bitdepth']
    maxval = 2**bitdepth - 1
    # Rudely, the number of image planes can be used to determine
    # whether we are L (PGM), LA (PAM), RGB (PPM), or RGBA (PAM).
    planes = meta['planes']
    # Can be an assert as long as we assume that pixels and meta came
    # from a PNG file.
    assert planes in (1, 2, 3, 4)
    if planes in (1, 3):
        if 1 == planes:
            # PGM
            # Could generate PBM if maxval is 1, but we don't (for one
            # thing, we'd have to convert the data, not just blat it
            # out).
            fmt = 'P5'
        else:
            # PPM
            fmt = 'P6'
        header = '%s %d %d %d\n' % (fmt, width, height, maxval)
    if planes in (2, 4):
        # PAM
        # See http://netpbm.sourceforge.net/doc/pam.html
        if 2 == planes:
            tupltype = 'GRAYSCALE_ALPHA'
        else:
            tupltype = 'RGB_ALPHA'
        header = ('P7\nWIDTH %d\nHEIGHT %d\nDEPTH %d\nMAXVAL %d\n'
                  'TUPLTYPE %s\nENDHDR\n' %
                  (width, height, planes, maxval, tupltype))
    fileobj.write(png.strtobytes(header))
    # Values per row
    vpr = planes * width
    # struct format
    fmt = '>%d' % vpr
    if maxval > 0xff:
        fmt = fmt + 'H'
    else:
        fmt = fmt + 'B'
    for row in pixels:
        fileobj.write(struct.pack(fmt, *row))
    fileobj.flush()


def read_pam_header(infile):
    """
    Read (the rest of a) PAM header.

    `infile` should be positioned
    immediately after the initial 'P7' line (at the beginning of the
    second line).  Returns are as for `read_pnm_header`.
    """
    # Unlike PBM, PGM, and PPM, we can read the header a line at a time.
    header = dict()
    while True:
        l = infile.readline().strip()
        if l == png.strtobytes('ENDHDR'):
            break
        if not l:
            raise EOFError('PAM ended prematurely')
        if l[0] == png.strtobytes('#'):
            continue
        l = l.split(None, 1)
        if l[0] not in header:
            header[l[0]] = l[1]
        else:
            header[l[0]] += png.strtobytes(' ') + l[1]

    required = ['WIDTH', 'HEIGHT', 'DEPTH', 'MAXVAL']
    required = [png.strtobytes(x) for x in required]
    WIDTH, HEIGHT, DEPTH, MAXVAL = required
    present = [x for x in required if x in header]
    if len(present) != len(required):
        raise png.Error('PAM file must specify '
                        'WIDTH, HEIGHT, DEPTH, and MAXVAL')
    width = int(header[WIDTH])
    height = int(header[HEIGHT])
    depth = int(header[DEPTH])
    maxval = int(header[MAXVAL])
    if (width <= 0 or height <= 0 or depth <= 0 or maxval <= 0):
        raise png.Error(
          'WIDTH, HEIGHT, DEPTH, MAXVAL must all be positive integers')
    return 'P7', width, height, depth, maxval


def read_pnm_header(infile, supported=('P5', 'P6')):
    """
    Read a PNM header, returning (format, width, height, depth, maxval).

    `width` and `height` are in pixels.  `depth` is the number of
    channels in the image; for PBM and PGM it is synthesized as 1, for
    PPM as 3; for PAM images it is read from the header.  `maxval` is
    synthesized (as 1) for PBM images.
    """
    # Generally, see http://netpbm.sourceforge.net/doc/ppm.html
    # and http://netpbm.sourceforge.net/doc/pam.html
    supported = [png.strtobytes(x) for x in supported]

    # Technically 'P7' must be followed by a newline, so by using
    # rstrip() we are being liberal in what we accept.  I think this
    # is acceptable.
    mode = infile.read(3).rstrip()
    if mode not in supported:
        raise NotImplementedError('file format %s not supported' % mode)
    if mode == png.strtobytes('P7'):
        # PAM header parsing is completely different.
        return read_pam_header(infile)
    # Expected number of tokens in header (3 for P4, 4 for P6)
    expected = 4
    if mode in (png.strtobytes('P1'), png.strtobytes('P4')):
        expected = 3
    header = [mode]
    header.extend(read_int_tokens(infile, expected - 1, False))
    if len(header) == 3:
        # synthesize a MAXVAL
        header.append(1)

    depth = (1, 3)[mode in (png.strtobytes('P3'), png.strtobytes('P6'))]
    return header[0], header[1], header[2], depth, header[3]


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


def parse_options(args):
    """Parse command line arguments"""
    from optparse import OptionParser
    version = '%prog ' + png.__version__
    parser = OptionParser(version=version)
    parser.set_usage("%prog [options] [imagefile]")
    parser.add_option('-r', '--read-png', default=False,
                      action='store_true',
                      help='Read PNG, write PNM')
    parser.add_option("-a", "--alpha",
                      action="store", type="string", metavar="pgmfile",
                      help="alpha channel transparency (RGBA)")
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
    (options, args) = parser.parse_args(args=args)
    # Convert options
    if options.transparent is not None:
        options.transparent = color_triple(options.transparent)
    if options.background is not None:
        options.background = color_triple(options.background)

    # Prepare input and output files
    if len(args) == 0:
        infilename = '-'
        infile = sys.stdin
    elif len(args) == 1:
        infilename = args[0]
        infile = open(infilename, 'rb')
    else:
        parser.error("more than one input file")
    outfile = sys.stdout
    if sys.platform == "win32":
        import msvcrt, os
        try:
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
        except:
            pass
    return (options, infilename, infile, outfile)


def main(argv):
    """Run the PNG encoder with options from the command line."""
    (options, infilename, infile, outfile) = parse_options(argv[1:])

    if options.read_png:
        # Encode PNG to PPM
        pngObj = png.Reader(file=infile)
        width, height, pixels, meta = pngObj.asDirect()
        write_pnm(outfile, width, height, pixels, meta)
    else:
        # Encode PNM to PNG
        mode, width, height, depth, maxval = \
          read_pnm_header(infile, ('P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7'))
        # When it comes to the variety of input formats, we do something
        # rather rude.  Observe that L, LA, RGB, RGBA are the 4 colour
        # types supported by PNG and that they correspond to 1, 2, 3, 4
        # channels respectively.  So we use the number of channels in
        # the source image to determine which one we have.  We do not
        # care about TUPLTYPE.
        greyscale = depth <= 2
        pamalpha = depth in (2, 4)
        supported = [2 ** x - 1 for x in range(1, 17)]
        try:
            bitdepth = supported.index(maxval) + 1
        except ValueError:
            raise NotImplementedError(
              'your maxval (%s) not in supported list %s' %
              (maxval, str(supported)))
        writer = png.Writer(width, height,
                        greyscale=greyscale,
                        bitdepth=bitdepth,
                        interlace=options.interlace,
                        transparent=options.transparent,
                        background=options.background,
                        alpha=bool(pamalpha or options.alpha),
                        gamma=options.gamma,
                        compression=options.compression)
        if mode == png.strtobytes('P4'):
            rows = pbmb_scanlines(infile, width, height)
        elif mode in (png.strtobytes('P1'),
                      png.strtobytes('P2'),
                      png.strtobytes('P3')):
            rows = ascii_scanlines(infile, width, height, depth, bitdepth)
        else:
            rows = file_scanlines(infile, width, height, depth, bitdepth)
        if options.alpha:
            apgmfile = open(options.alpha, 'rb')
            _, awidth, aheight, adepth, amaxval = \
                read_pnm_header(apgmfile, ('P5', ))
            if amaxval != maxval:
                raise NotImplementedError(
                  'maxval %s of alpha channel mismatch %s maxval %s'
                  % (amaxval, infilename, maxval))
            if adepth != 1:
                raise ValueError("alpha image should have 1 channel")
            if (awidth, aheight) != (width, height):
                raise ValueError("alpha channel image size mismatch"
                                 " (%s has %sx%s but %s has %sx%s)"
                                 % (infilename, width, height,
                                    options.alpha, awidth, aheight))
            arows = file_scanlines(apgmfile, width, height, 1, bitdepth)
            merged = png.MergedPlanes(rows, depth, arows, 1, bitdepth, width)
            writer.write(outfile, merged)
        else:
            writer.write(outfile, rows)

if __name__ == '__main__':
    main(sys.argv)
