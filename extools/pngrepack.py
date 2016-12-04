#!/usr/bin/env python
# $URL$
# $Rev$
# pngrepack
# Recompression idat

import sys
import png
import zlib


def buf_emu(not_buffer):
    if hasattr(not_buffer, 'tostring'):
        return not_buffer.tostring()
    else:
        return bytes(not_buffer)


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


def comp_idat(idat, level):
    compressor = zlib.compressobj(level)
    for dat in idat:
        compressed = compressor.compress(buffer(dat))
        if compressed:
            yield compressed
    flushed = compressor.flush()
    if flushed:
        yield flushed


def Recompress(inp, out, args):
    p = png.Reader(file=inp)
    if args.filter == 'keep':
        p.preamble()
        # Python 2.3 doesn' work with inline if
        if p.plte:
            palette = p.palette()
        else:
            palette = None
        wr = png.Writer(size=(p.width, p.height),
                        greyscale=p.greyscale, alpha=p.alpha,
                        bitdepth=p.bitdepth,
                        palette=palette,
                        transparent=getattr(p, 'transparent', None),
                        background=getattr(p, 'background', None),
                        gamma=getattr(p, 'gamma', None),
                        compression=args.level,
                        interlace=p.interlace)
        wr.write_idat(out, comp_idat(p.idatdecomp(), args.level))
    else:
        pix, meta = p.read()[2:]
        meta['filter_type'] = args.filter
        meta['compression'] = args.level
        if not meta['greyscale'] and args.greyscale == 'try':
            meta['greyscale'] = 'try'
        wr = png.Writer(**meta)
        wr.write(out, pix)


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description="Recompress image data"
                                " in PNG file")
    p.add_argument("-l", "--level", help="Compression level", type=int)
    p.add_argument("-f", "--filter", help="Filter type",
                   choices=['0', '1', '2', '3', '4', 'sum', 'entropy', 'keep'],
                   default='keep')
    p.add_argument("-g", "--greyscale", help="Try convert to greyscale",
                   choices=['try', 'keep'],
                   default='try')
    p.add_argument("input", help="Input file", type=argparse.FileType("rb"))
    p.add_argument("output", help="Output file", type=argparse.FileType("wb"))
    a = p.parse_args(argv[1:])

    Recompress(a.input, a.output, a)
    a.input.close()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
