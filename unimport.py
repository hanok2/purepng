"""Extracting part of `png.py` to compile it with Cython"""
from os import remove
from os.path import join


def do_unimport(folder=''):
    """Do extraction of filters etc. into target folder"""
    src = open(join(folder, 'png.py'))
    try:
        remove(join(folder, 'pngfilters.py'))
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

if __name__ == "__main__":
    do_unimport('code/png')
