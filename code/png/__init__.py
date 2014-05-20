try:
    from png import *
    #  Following methods are not parts of API and imports only for unittest
    from png import _main
    from png import strtobytes
    from png import array
    from png import itertools
except ImportError:
    _png = __import__(__name__ + '.png')
    _to_import = _png.png.__all__
    _to_import.extend(('_main', 'strtobytes'))
    for it in _to_import:
        locals()[it] = eval('_png.png.' + it)
