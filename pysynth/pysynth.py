#!/usr/bin/env python

"""
##########################################################################
#                       * * *  PySynth  * * *
#       A very basic audio synthesizer in Python (www.python.org)
#
#          Martin C. Doege, 2009-04-07 (mdoege@compuserve.com)
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

from io import BytesIO
from typing import Iterable

from .mkfreq import getfreq

__all__ = ("make_wav",)

pitchhz, keynum = getfreq(pr=True)

##########################################################################
#### Main program starts below
##########################################################################
# Some parameters:

# Beats (quarters) per minute
# e.g. bpm = 95

# Octave shift (neg. integer -> lower; pos. integer -> higher)
# e.g. transpose = 0

# Pause between notes as a fraction (0. = legato and e.g., 0.5 = staccato)
# e.g. pause = 0.05

# Volume boost for asterisk notes (1. = no boost)
# e.g. boost = 1.2

# Output file name
# fn = 'pysynth_output.wav'

# Other parameters:

# Influences the decay of harmonics over frequency. Lowering the
# value eliminates even more harmonics at high frequencies.
# Suggested range: between 3. and 5., depending on the frequency response
#  of speakers/headphones used
harm_max = 4.0
##########################################################################

import wave

import numpy as np


def make_wav(
    song: Iterable[tuple[str, float]],
    bpm: float = 120.0,
    transpose: float = 0.0,
    pause: float = 0.05,
    boost: float = 1.0,
    repeat: int = 0,
    fn: str | BytesIO = "out.wav",
):
    f = wave.open(fn, "w")

    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(44100)
    f.setcomptype("NONE", "Not Compressed")

    bpmfac = 120.0 / bpm

    def length(l: float):
        return 88200.0 / l * bpmfac

    def waves2(hz: float, l: float):
        a = 44100.0 / hz
        b = float(l) / 44100.0 * hz
        return a, round(b)

    def asin(x: float):
        return np.sin(2.0 * np.pi * x)

    def render2(a, b, vol):
        b2 = (1.0 - pause) * b
        l = waves2(a, b2)
        q = int(l[0] * l[1])

        # harmonics are frequency-dependent:
        lf = np.log(a)
        lf_fac = (lf - 3.0) / harm_max
        harm = 0 if lf_fac > 1 else 2.0 * (1 - lf_fac)
        decay = 2.0 / lf
        t = (lf - 3.0) / (8.5 - 3.0)
        volfac = 1.0 + 0.8 * t * np.cos(np.pi / 5.3 * (lf - 3.0))

        for x in range(q):
            if x < 100:
                fac = x / 80.0
            elif 100 <= x < 300:
                fac = 1.25 - (x - 100) / 800.0
            elif x > q - 400:
                fac = 1.0 - ((x - q + 400) / 400.0)
            else:
                fac = 1.0

            s = float(x) / float(q)
            dfac = 1.0 - s + s * decay

            yield (
                (
                    asin(float(x) / l[0])
                    + harm * asin(float(x) / (l[0] / 2.0))
                    + 0.5 * harm * asin(float(x) / (l[0] / 4.0))
                )
                / 4.0
                * fac
                * vol
                * dfac
                * volfac
            )

    ##########################################################################
    # Write to output file (in WAV format)
    ##########################################################################

    for x, y in np.tile(song, (repeat + 1, 1)):  # type: ignore
        y = float(y)

        if x == "r":
            b = length(y)
            f.writeframesraw(b"\x00\x00" * int(b))  # Zero padding for rest
            continue

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


##########################################################################
# Synthesize demo songs
##########################################################################


if __name__ == "__main__":
    from .demosongs import *
    from .mixfiles import mix_files

    print()
    print("Creating Demo Songs... (this might take about a minute)")
    print()

    # SONG 1
    make_wav(song1, fn="pysynth_scale.wav")

    # SONG 2
    make_wav(song2, bpm=95, boost=1.2, fn="pysynth_anthem.wav")

    # SONG 3
    make_wav(song3, bpm=132 / 2, pause=0.0, boost=1.1, fn="pysynth_chopin.wav")

    # SONG 4
    #   right hand part
    make_wav(
        song4_rh,
        bpm=130,
        transpose=1,
        pause=0.1,
        boost=1.15,
        repeat=1,
        fn="pysynth_bach_rh.wav",
    )
    #   left hand part
    make_wav(
        song4_lh,
        bpm=130,
        transpose=1,
        pause=0.1,
        boost=1.15,
        repeat=1,
        fn="pysynth_bach_lh.wav",
    )
    #   mix both files together
    mix_files("pysynth_bach_rh.wav", "pysynth_bach_lh.wav", "pysynth_bach.wav")
