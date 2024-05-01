#!/usr/bin/env python

# print "*** KARPLUS-STRONG STRING ***"

"""
##########################################################################
#                       * * *  PySynth  * * *
#       A very basic audio synthesizer in Python (www.python.org)
#
#          Martin C. Doege, 2009-06-13 (mdoege@compuserve.com)
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


def make_wav(
    song: Iterable[tuple[str, float]],
    bpm: float = 120.0,
    transpose: float = 0.0,
    pause: float = 0,
    boost: float = 1.0,
    repeat: int = 0,
    fn: str | BytesIO = "out.wav",
):
    data = []

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

    def render2(a, b, vol, pos, knum, note, endamp=0.25, sm=10):
        b2 = (1.0 - pause) * b
        l = waves2(a, b2)
        q = int(l[0] * l[1])

        lf = np.log(a)
        t = (lf - 3.0) / (8.5 - 3.0)
        volfac = 1.0 + 0.8 * t * np.cos(np.pi / 5.3 * (lf - 3.0))
        snd_len = int((10.0 - lf) * q)
        if lf < 4:
            snd_len *= 2

        kp_len = int(l[0])
        kps1 = np.zeros(snd_len)
        kps2 = np.zeros(snd_len)
        kps1[:kp_len] = np.random.normal(size=kp_len)

        for t in range(kp_len):
            kps2[t] = kps1[t : t + sm].mean()

        delt = float(l[0])
        li = int(np.floor(delt))
        hi = int(np.ceil(delt))
        ifac = delt % 1
        delt2 = delt * (np.floor(delt) - 1) / np.floor(delt)
        ifac2 = delt2 % 1
        falloff = (4.0 / lf * endamp) ** (1.0 / l[1])
        for t in range(hi, snd_len):
            v1 = ifac * kps2[t - hi] + (1.0 - ifac) * kps2[t - li]
            v2 = ifac2 * kps2[t - hi + 1] + (1.0 - ifac2) * kps2[t - li + 1]
            kps2[t] += 0.5 * (v1 + v2) * falloff
        data[pos : pos + snd_len] += kps2 * vol * volfac

    ex_pos = 0.0
    t_len = 0
    for y, x in song:
        if x < 0:
            t_len += length(-2.0 * x / 3.0)
        else:
            t_len += length(x)
    data = np.zeros(int((repeat + 1) * t_len + 20 * 44100))

    # print len(data)/44100., "s allocated"

    for x, y in np.tile(song, (repeat + 1, 1)):  # type: ignore
        y = float(y)
        if x == "r":
            b = length(y)
            ex_pos += b
            continue

        if x[-1] == "*":
            vol, note = boost, x[:-1]
        else:
            vol, note = 1.0, x

        if not note[-1].isdigit():
            note += "4"  # default to fourth octave

        a = pitchhz[note] * np.exp2(transpose)
        kn = keynum[note]

        if y < 0:
            b = length(-2.0 * y / 3.0)
        else:
            b = length(y)

        render2(a, b, vol, int(ex_pos), kn, note)
        ex_pos += b

    ##########################################################################
    # Write to output file (in WAV format)
    ##########################################################################

    data /= data.max() * 2.0
    out_len = int(2.0 * 44100.0 + ex_pos + 0.5)
    data2 = np.zeros(out_len, np.short)
    data2[:] = 32767.0 * data[:out_len]
    f.writeframes(data2.tobytes())
    f.close()


##########################################################################
# Synthesize demo songs
##########################################################################

if __name__ == "__main__":
    from .demosongs import *
    from .mixfiles import mix_files

    print("*** KARPLUS-STRONG STRING ***")
    print()
    print("Creating Demo Songs... (this might take a few minutes)")
    print()

    # make_wav((('c2', 4), ('e2', 4), ('g2', 4), ('c3', 1)))
    # make_wav(song1, fn = "pysynth_scale.wav")
    # make_wav((('c1', 1), ('r', 1),('c2', 1), ('r', 1),('c3', 1), ('r', 1), ('c4', 1), ('r', 1),('c5', 1), ('r', 1),('c6', 1), ('r', 1),('c7', 1), ('r', 1),('c8', 1), ('r', 1), ('r', 1), ('r', 1), ('c4', 1),('r', 1), ('c4*', 1), ('r', 1), ('r', 1), ('r', 1), ('c4', 16), ('r', 1), ('c4', 8), ('r', 1),('c4', 4), ('r', 1),('c4', 1), ('r', 1),('c4', 1), ('r', 1)), fn = "all_cs.wav")
    make_wav(
        song4_rh, bpm=130, transpose=1, boost=1.15, repeat=1, fn="pysynth_bach_rh.wav"
    )
    make_wav(
        song4_lh, bpm=130, transpose=1, boost=1.15, repeat=1, fn="pysynth_bach_lh.wav"
    )
    mix_files("pysynth_bach_rh.wav", "pysynth_bach_lh.wav", "pysynth_bach.wav")

    # make_wav(song3, bpm = 132/2, pause = 0., boost = 1.1, fn = "pysynth_chopin.wav")
    # make_wav(song2, bpm = 95, boost = 1.2, fn = "pysynth_anthem.wav")
