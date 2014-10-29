# pngsuite.py

# PngSuite Test PNGs.

"""After you import this module with "import pngsuite" use
``pngsuite.bai0g01`` to get the bytes for a particular PNG image, or
use ``pngsuite.png`` to get a dict() of them all.
"""

import tarfile
import os.path
from os.path import splitext
suite_file = tarfile.open(os.path.join(os.path.dirname(__file__),
                                       "PngSuite-2013jan13.tgz"))

# Suite by names, but skip error tests and size(unsupported yet)
suite_files_b = [(splitext(f)[0], suite_file.extractfile(f))
               for f in suite_file.getnames() if
               (not f.startswith('x'))]
suite_files_b = dict(suite_files_b)

from png import strtobytes
# (For an in-memory binary file IO object) We use BytesIO where
# available, otherwise we use StringIO, but name it BytesIO.
try:
    from io import BytesIO
except ImportError:
    from StringIO import StringIO as BytesIO


def _dehex(s):
    """Liberally convert from hex string to binary string."""
    import re
    import binascii

    # Remove all non-hexadecimal digits
    s = re.sub(r'[^a-fA-F\d]', '', s)
    # binscii.unhexlify works in Python 2 and Python 3 (unlike
    # thing.decode('hex')).
    return BytesIO(binascii.unhexlify(strtobytes(s)))

# Extra png test by drj
png = {
  # A version of basn0g04 dithered down to 3 bits.
  'Basn0g03': _dehex("""
89504e470d0a1a0a0000000d494844520000002000000020040000000093e1c8
2900000001734249540371d88211000000fd49444154789c6d90d18906210c84
c356f22356b2889588604301b112112b11d94a96bb495cf7fe87f32d996f2689
44741cc658e39c0b118f883e1f63cc89dafbc04c0f619d7d898396c54b875517
83f3a2e7ac09a2074430e7f497f00f1138a5444f82839c5206b1f51053cca968
63258821e7f2b5438aac16fbecc052b646e709de45cf18996b29648508728612
952ca606a73566d44612b876845e9a347084ea4868d2907ff06be4436c4b41a3
a3e1774285614c5affb40dbd931a526619d9fa18e4c2be420858de1df0e69893
a0e3e5523461be448561001042b7d4a15309ce2c57aef2ba89d1c13794a109d7
b5880aa27744fc5c4aecb5e7bcef5fe528ec6293a930690000000049454e44ae
426082
"""),
  'Tp2n3p08': _dehex("""
89504e470d0a1a0a0000000d494844520000002000000020080300000044a48a
c60000000467414d41000186a031e8965f00000300504c544502ffff80ff05ff
7f0703ff7f0180ff04ff00ffff06ff000880ff05ff7f07ffff06ff000804ff00
0180ff02ffff03ff7f02ffff80ff0503ff7f0180ffff0008ff7f0704ff00ffff
06ff000802ffffff7f0704ff0003ff7fffff0680ff050180ff04ff000180ffff
0008ffff0603ff7f80ff05ff7f0702ffffff000880ff05ffff0603ff7f02ffff
ff7f070180ff04ff00ffff06ff000880ff050180ffff7f0702ffff04ff0003ff
7fff7f0704ff0003ff7f0180ffffff06ff000880ff0502ffffffff0603ff7fff
7f0702ffff04ff000180ff80ff05ff0008ff7f07ffff0680ff0504ff00ff0008
0180ff03ff7f02ffff02ffffffff0604ff0003ff7f0180ffff000880ff05ff7f
0780ff05ff00080180ff02ffffff7f0703ff7fffff0604ff00ff7f07ff0008ff
ff0680ff0504ff0002ffff0180ff03ff7fff0008ffff0680ff0504ff000180ff
02ffff03ff7fff7f070180ff02ffff04ff00ffff06ff0008ff7f0780ff0503ff
7fffff06ff0008ff7f0780ff0502ffff03ff7f0180ff04ff0002ffffff7f07ff
ff0604ff0003ff7fff00080180ff80ff05ffff0603ff7f0180ffff000804ff00
80ff0502ffffff7f0780ff05ffff0604ff000180ffff000802ffffff7f0703ff
7fff0008ff7f070180ff03ff7f02ffff80ff05ffff0604ff00ff0008ffff0602
ffff0180ff04ff0003ff7f80ff05ff7f070180ff04ff00ff7f0780ff0502ffff
ff000803ff7fffff0602ffffff7f07ffff0680ff05ff000804ff0003ff7f0180
ff02ffff0180ffff7f0703ff7fff000804ff0080ff05ffff0602ffff04ff00ff
ff0603ff7fff7f070180ff80ff05ff000803ff7f0180ffff7f0702ffffff0008
04ff00ffff0680ff0503ff7f0180ff04ff0080ff05ffff06ff000802ffffff7f
0780ff05ff0008ff7f070180ff03ff7f04ff0002ffffffff0604ff00ff7f07ff
000880ff05ffff060180ff02ffff03ff7f80ff05ffff0602ffff0180ff03ff7f
04ff00ff7f07ff00080180ffff000880ff0502ffff04ff00ff7f0703ff7fffff
06ff0008ffff0604ff00ff7f0780ff0502ffff03ff7f0180ffdeb83387000000
f874524e53000000000000000008080808080808081010101010101010181818
1818181818202020202020202029292929292929293131313131313131393939
393939393941414141414141414a4a4a4a4a4a4a4a52525252525252525a5a5a
5a5a5a5a5a62626262626262626a6a6a6a6a6a6a6a73737373737373737b7b7b
7b7b7b7b7b83838383838383838b8b8b8b8b8b8b8b94949494949494949c9c9c
9c9c9c9c9ca4a4a4a4a4a4a4a4acacacacacacacacb4b4b4b4b4b4b4b4bdbdbd
bdbdbdbdbdc5c5c5c5c5c5c5c5cdcdcdcdcdcdcdcdd5d5d5d5d5d5d5d5dedede
dededededee6e6e6e6e6e6e6e6eeeeeeeeeeeeeeeef6f6f6f6f6f6f6f6b98ac5
ca0000012c49444154789c6360e7169150d230b475f7098d4ccc28a96ced9e32
63c1da2d7b8e9fb97af3d1fb8f3f18e8a0808953544a4dd7c4c2c9233c2621bf
b4aab17fdacce5ab36ee3a72eafaad87efbefea68702362e7159652d031b07cf
c0b8a4cce28aa68e89f316aedfb4ffd0b92bf79fbcfcfe931e0a183904e55435
8decdcbcc22292b3caaadb7b27cc5db67af3be63e72fdf78fce2d31f7a2860e5
119356d037b374f10e8a4fc92eaa6fee99347fc9caad7b0f9ebd74f7c1db2fbf
e8a180995f484645dbdccad12f38363dafbcb6a573faeca5ebb6ed3e7ce2c29d
e76fbefda38702063e0149751d537b67ff80e8d4dcc29a86bea97316add9b0e3
c0e96bf79ebdfafc971e0a587885e515f58cad5d7d43a2d2720aeadaba26cf5a
bc62fbcea3272fde7efafac37f3a28000087c0fe101bc2f85f0000000049454e
44ae426082
"""),
}

png.update(suite_files_b)
import sys
sys.modules[__name__].__dict__.update(png)
