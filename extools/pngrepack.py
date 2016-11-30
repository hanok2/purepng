#!/usr/bin/env python
# $URL$
# $Rev$
# pngrepack
# Recompression idat

import sys
import png
import zlib


def comp_idat(idat, level):
    compressor = zlib.compressobj(level)
    for dat in idat:
        compressed = compressor.compress(dat)
        if compressed:
            yield compressed
    flushed = compressor.flush()
    if flushed:
        yield flushed


def Recompress(inp, out, level=6, filt='keep'):
    p = png.Reader(file=inp)
    if filt == 'keep':
        p.preamble()
        wr = png.Writer(size=(p.width, p.height),
                        greyscale=p.greyscale, alpha=p.alpha,
                        bitdepth=p.bitdepth,
                        palette=p.palette() if p.plte else None,
                        transparent=getattr(p, 'transparent', None),
                        background=getattr(p, 'background', None),
                        gamma=getattr(p, 'gamma', None),
                        compression=level,
                        interlace=p.interlace)
        wr.color_type = p.color_type  # just to be sure. Check if needed?
        wr.write_idat(out, comp_idat(p.idatdecomp(), level))
    else:
        pix, meta = p.read()[2:]
        meta['filter_type'] = filt
        meta['compression'] = level
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
    p.add_argument("input", help="Input file", type=argparse.FileType("rb"))
    p.add_argument("output", help="Output file", type=argparse.FileType("wb"))
    a = p.parse_args(argv[1:])

    Recompress(a.input, a.output, a.level, a.filter)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
