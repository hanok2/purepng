try:
    exec("from .png import *", globals(), locals())
    # CLI support
    exec("from .pnm2png import main", globals(), locals())
    #  Following methods are not parts of API and imports only for unittest
    exec("from .png import strtobytes", globals(), locals())
    exec("from .png import array", globals(), locals())
except SyntaxError:
    # On Python < 2.5 relative import cause syntax error
    from png import *
    # CLI support
    from pnm2png import main
    #  Following methods are not parts of API and imports only for unittest
    from png import strtobytes
    from png import array

if __name__ == '__main__':
    import sys
    main(sys.argv)
