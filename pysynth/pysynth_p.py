#!/usr/bin/env python

"""
##########################################################################
#                       * * *  PySynth  * * *
#       A very basic audio synthesizer in Python (www.python.org)
#
#          Martin C. Doege, 2017-06-20 (mdoege@compuserve.com)
##########################################################################
# Based on a program by Tyler Eaves (tyler at tylereaves.com) found at
#   http://mail.python.org/pipermail/python-list/2000-August/041308.html
##########################################################################

# 'song' is a Python list (or tuple) in which the song is defined,
#   the format is [['note', value]]

# Notes are 'a' through 'g' of course,
# optionally with '#' or 'b' appended for sharps or flats.
# Finally the octave number (defaults to octave 4 if not given).
# An asterisk at the end makes the note a little louder (useful for the beat).
# 'r' is a rest.

# Note value is a number:
# 1=Whole Note; 2=Half Note; 4=Quarter Note, etc.
# Dotted notes can be written in two ways:
# 1.33 = -2 = dotted half
# 2.66 = -4 = dotted quarter
# 5.33 = -8 = dotted eighth
"""

import wave
from io import BytesIO
from typing import Iterable

import numpy as np

from .mkfreq import getfreq

__all__ = ("make_wav",)

pitchhz, keynum = getfreq()


def make_wav(
    song: Iterable[tuple[str, float]],
    bpm: float = 120.0,
    rate: int = 44100,
    transpose: float = 0.0,
    leg_stac: float = 0.9,
    pause: float = 0.05,
    boost: float = 1.0,
    repeat: int = 0,
    fn: str | BytesIO = "out.wav",
):
    f = wave.open(fn, "w")

    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(rate)
    f.setcomptype("NONE", "Not Compressed")

    bpmfac = 120.0 / bpm

    def length(l: float):
        return 2 * rate / l * bpmfac

    def waves2(hz: float, l: float):
        a = rate / hz
        b = float(l) / rate * hz
        return a, round(b)

    def render2(a: float, b: float, vol: float):
        b2 = (1.0 - pause) * b
        l = waves2(a, b2)
        q = int(l[0] * l[1])

        sp, fade = 0, 1
        for x in range(q):
            osc = np.random.random()
            if q - x < 100:
                fade = (q - x) / 100
            sp += (osc - sp) / 10
            yield np.exp(-x / 1000) * fade * vol * sp

    # Keep as list[tuple[str, float]]
    for x, y in np.tile(song, repeat + 1):  # type: ignore
        y = float(y)

        if x == "r":
            b = length(y)
            f.writeframesraw(b"\x00\x00" * int(b))  # Zero padding for rest
        else:
            if x[-1] == "*":
                vol, note = boost, x[:-1]
            else:
                vol, note = 1.0, x

            try:
                a = pitchhz[note]
            except:
                a = pitchhz[note + "4"]  # default to fourth octave

            a *= np.exp2(transpose)

            if y < 0:
                b = length(-2.0 * y / 3.0)
            else:
                b = length(y)

            wave_samples = np.array(list(render2(a, b, vol)))
            f.writeframesraw((wave_samples * 32767).astype(np.int16).tobytes())

    f.writeframes(b"")
    f.close()


if __name__ == "__main__":
    from .demosongs import song3

    make_wav(song3, bpm=132 / 2, pause=0.0, boost=1.1, fn="pysynth_chopin.wav")
