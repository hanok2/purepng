#!/usr/bin/env python
"""
Simple tool to repack png file using purepng
"""
import sys
import png


def buf_emu(not_buffer):
    """Buffer emulation, mostly for `array` object"""
    if hasattr(not_buffer, 'tostring'):
        return not_buffer.tostring()
    else:
        try:
            return bytes(not_buffer)
        except NameError:
            return str(not_buffer)


try:
    buffer
except NameError:
    try:
        buffer = memoryview
    except NameError:
        buffer = buf_emu

if sys.platform.startswith('java'):
    # buffer object in Jython is not compatible with zlib
    oldbuf = buffer

    def buffer(src):
        return str(oldbuf(src))


def simple_recompress(reader, outfile, level):
    """Simple recompress of IDAT chunk without other processing"""
    reader.preamble()
    # Python 2.3 doesn' work with inline if
    if reader.plte:
        palette = reader.palette()
    else:
        palette = None
    wr = png.Writer(size=(reader.width, reader.height),
                    greyscale=reader.greyscale, alpha=reader.alpha,
                    bitdepth=reader.bitdepth,
                    palette=palette,
                    transparent=getattr(reader, 'transparent', None),
                    background=getattr(reader, 'background', None),
                    gamma=getattr(reader, 'gamma', None),
                    compression=level,
                    interlace=reader.interlace)
    wr.write_idat(outfile, wr.comp_idat(map(buffer, reader.idatdecomp())))


def repack(p, out, args):
    """Main repack funtion"""
    p.preamble()
    if args.greyscale == 'no':
        if p.alpha or p.trns:
            pix, meta = p.asRGBA()()[2:]
        else:
            pix, meta = p.asRGB()[2:]
    else:
        pix, meta = p.read()[2:]
    meta['filter_type'] = args.filter
    meta['compression'] = args.level
    if not meta['greyscale'] and args.greyscale == 'try':
        meta['greyscale'] = 'try'
    wr = png.Writer(**meta)
    wr.write(out, pix)


def main(argv=None):
    """Main CLI function: parse args and call repack"""
    import argparse
    p = argparse.ArgumentParser(description="Recompress image data"
                                " in PNG file")
    p.add_argument("-l", "--level", help="Compression level", type=int)
    p.add_argument("-f", "--filter", help="Filter type",
                   choices=['0', '1', '2', '3', '4', 'sum', 'entropy', 'keep'],
                   default='keep')
    p.add_argument("-g", "--greyscale", help="Try convert to greyscale",
                   choices=['try', 'keep', 'no'],
                   default='try')
    p.add_argument("input", help="Input file", type=argparse.FileType("rb"))
    p.add_argument("output", help="Output file", type=argparse.FileType("wb"))
    a = p.parse_args(argv[1:])
    r = png.Reader(file=a.input)
    if a.filter == 'keep':
        simple_recompress(r, a.output, a.level)
    else:
        repack(r, a.output, a)
    a.input.close()
    a.output.flush()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
