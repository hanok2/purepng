"""Extracting part of `png.py` to compile it with Cython"""
from setup import do_unimport

if __name__ == "__main__":
    do_unimport('code/png')
