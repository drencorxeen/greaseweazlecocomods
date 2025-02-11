# greaseweazle/codec/bitcell.py
#
# Written & released by Keir Fraser <keir.xen@gmail.com>
#
# This is free and unencumbered software released into the public domain.
# See the file COPYING for more details, or visit <http://unlicense.org>.

from typing import List, Optional, Tuple

import struct
from bitarray import bitarray

from greaseweazle import error
from greaseweazle import optimised
from greaseweazle.track import MasterTrack, RawTrack
from greaseweazle.flux import Flux

default_revs = 1

class BitcellTrack:

    def __init__(self, cyl: int, head: int, config):
        self.cyl, self.head = cyl, head
        self.config = config
        self.clock = config.clock
        self.nsec = 0
        self.time_per_rev = config.time_per_rev
        self.raw: Optional[RawTrack] = None

    def summary_string(self) -> str:
        if self.raw is None:
            s = "Raw Bitcell (empty)"
        else:
            bits, _ = self.raw.get_revolution(0)
            s = ("Raw Bitcell (%d bits, %.2fms)"
                 % (len(bits), self.raw.time_per_rev*1000))
        return s

    def has_sec(self, sec_id) -> bool:
        return False

    def nr_missing(self) -> int:
        return 0

    def get_img_track(self) -> bytearray:
        return bytearray()

    def set_img_track(self, tdat: bytearray) -> int:
        return 0

    def flux(self, *args, **kwargs) -> Flux:
        return self.raw_track().flux(*args, **kwargs)

    def decode_raw(self, track, pll=None) -> None:
        flux = track.flux()
        flux.cue_at_index()
        time_per_rev = self.time_per_rev
        if time_per_rev is None:
            time_per_rev = flux.time_per_rev
        self.raw = RawTrack(time_per_rev = time_per_rev,
                            clock = self.clock, data = flux, pll = pll)

    def raw_track(self) -> MasterTrack:
        if self.raw is None:
            time_per_rev = self.time_per_rev
            if time_per_rev is None:
                time_per_rev = 0.2
            nbytes = int(time_per_rev / self.clock) // 8
            track = MasterTrack(bits = bytes(nbytes),
                                time_per_rev = time_per_rev,
                                weak = [(0,nbytes*8)])
            track.force_random_weak = True
            return track
        bits, _ = self.raw.get_revolution(0)
        track = MasterTrack(bits = bits, time_per_rev = self.raw.time_per_rev)
        return track


class BitcellTrackFormat:

    default_revs = default_revs

    def __init__(self, format_name: str):
        self.clock: Optional[float] = None
        self.time_per_rev: Optional[float] = None
        self.finalised = False

    def add_param(self, key: str, val) -> None:
        if key == 'secs':
            val = int(val)
            self.secs = val
        elif key == 'clock':
            val = float(val)
            self.clock = val * 1e-6
        elif key == 'time_per_rev':
            val = float(val)
            self.time_per_rev = val
        else:
            raise error.Fatal('unrecognised track option %s' % key)

    def finalise(self) -> None:
        if self.finalised:
            return
        error.check(self.clock is not None,
                    'clock period not specified')
        self.finalised = True

    def mk_track(self, cyl: int, head: int) -> BitcellTrack:
        return BitcellTrack(cyl, head, self)


# Local variables:
# python-indent: 4
# End:
