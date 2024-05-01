#!/usr/bin/env python

# print "*** FM PIANO VERSION WITH NOTE CACHING ***"

"""
##########################################################################
#                       * * *  PySynth  * * *
#       A very basic audio synthesizer in Python (www.python.org)
#
#          Martin C. Doege, 2012-11-29 (mdoege@compuserve.com)
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

# Harmonic intensities (dB) for selected piano keys,
# measured with output from a Yamaha P-85
harmo = np.array(
    [
        [1, -15.8, -3.0, -15.3, -22.8, -40.7],
        [16, -15.8, -3.0, -15.3, -22.8, -40.7],
        [28, -5.7, -4.4, -17.7, -16.0, -38.7],
        [40, -6.8, -17.2, -22.4, -16.8, -75.6],
        [52, -8.4, -19.7, -23.5, -21.6, -76.8],
        [64, -9.3, -20.8, -37.2, -36.3, -76.4],
        [76, -18.0, -64.5, -74.4, -77.3, -80.8],
        [88, -24.8, -53.8, -77.2, -80.8, -90.0],
    ]
)


# Interpolate harmonics linearly
def linint(arr, x):
    xvals = arr[:, 0]
    yvals = arr[:, 1]
    return np.interp(x, xvals, yvals)


# Precompute harmonic table
harmtab = np.zeros((88, 20))
for h in range(1, len(harmo[0])):
    dat = harmo[:, [0, h]]
    for h2 in range(88):
        harmtab[h2, h] = linint(dat, h2 + 1)

# Normalize harmonic table
ref = harmtab[:, 1]
harmtab = 10.0 ** ((harmtab - ref[:, np.newaxis]) / 20.0)

decay = np.exp(
    np.interp(
        np.linspace(0, 1, 1000),
        np.array([0, 3, 5, 6, 9]),
        [np.log(3), np.log(5), np.log(1.0), np.log(0.8), np.log(0.1)],
    )
)
# print harmtab[keynum['c4'],:]

##########################################################################
#### Main program starts below
##########################################################################
# Some parameters:

# Beats (quarters) per minute
# e.g. bpm = 95

# Octave shift (neg. integer -> lower; pos. integer -> higher)
# e.g. transpose = 0

# Playing style (e.g., 0.8 = very legato and e.g., 0.3 = very staccato)
# e.g. leg_stac = 0.6

# Volume boost for asterisk notes (1. = no boost)
# e.g. boost = 1.2

# Output file name
# fn = 'pysynth_output.wav'

# Other parameters:

# Influences the decay of harmonics over frequency. Lowering the
# value eliminates even more harmonics at high frequencies.
# Suggested range: between 3. and 5., depending on the frequency response
#  of speakers/headphones used
harm_max = 5.0
##########################################################################


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
    closing: bool = True,
):
    data = []
    note_cache = {}
    cache_this = {}

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

    def render2(a, b, vol, pos, knum, note):
        l = waves2(a, b)
        q = int(l[0] * l[1])
        lf = np.log(a)
        snd_len = max(int(3.1 * q), rate)

        raw_note = 12 * rate
        if note not in list(note_cache.keys()):
            x2 = np.arange(raw_note)
            sina = 2.0 * np.pi * x2 / float(l[0])
            sina14 = 14.0 * 2.0 * np.pi * x2 / float(l[0])
            amp1 = 1.0 - (x2 / snd_len)
            amp1[amp1 < 0] = 0
            amp2 = 1.0 - (4 * x2 / snd_len)
            amp2[amp2 < 0] = 0
            amp_3to6 = 1.0 - (0.25 * x2 / snd_len)
            amp_3to6[amp_3to6 < 0] = 0
            new = (
                amp1 * np.sin(sina + 0.58 * amp2 * np.sin(sina14))
                + amp_3to6 * np.sin(sina + 0.89 * amp_3to6 * np.sin(sina))
                + amp_3to6 * np.sin(sina + 0.79 * amp_3to6 * np.sin(sina))
            )
            new *= np.exp(-x2 / decay[int(lf * 100)] / rate)
            if cache_this[note] > 1:
                note_cache[note] = new.copy()
        else:
            new = note_cache[note].copy()
        dec_ind = int(leg_stac * q)
        new[dec_ind:] *= np.exp(-np.arange(raw_note - dec_ind) / 3000.0)
        if snd_len > raw_note:
            snd_len = raw_note
        data[pos : pos + snd_len] += new[:snd_len] * vol

    ex_pos = 0.0
    t_len = 0
    for y, x in song:
        if x < 0:
            t_len += length(-2.0 * x / 3.0)
        else:
            t_len += length(x)
        if y[-1] == "*":
            y = y[:-1]
        if not y[-1].isdigit():
            y += "4"
        cache_this[y] = cache_this.get(y, 0) + 1
    # print "Note frequencies in song:", cache_this
    data = np.zeros(int((repeat + 1) * t_len + 10 * rate))
    # print len(data)/44100., "s allocated"

    for x, y in np.tile(song, (repeat + 1, 1)):  # type: ignore
        y = float(y)
        if x == "r":
            ex_pos += length(y)
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

    data /= data.max() * 2.0
    out_len = int(2.0 * rate + ex_pos + 0.5)
    data2 = np.zeros(out_len, np.short)
    data2[:] = 32767.0 * data[:out_len]
    f.writeframes(data2.tobytes())
    if closing:
        f.close()


##########################################################################
# Synthesize demo songs
##########################################################################

if __name__ == "__main__":
    from .demosongs import *
    from .mixfiles import mix_files

    print("*** FM PIANO VERSION WITH NOTE CACHING ***")
    print()
    print("Creating Demo Songs... (this might take about a minute)")
    print()

    # make_wav((('c', 4), ('e', 4), ('g', 4), ('c5', 1)))
    # make_wav(song1, fn = "pysynth_scale.wav")
    make_wav(
        (
            ("c1", 1),
            ("r", 1),
            ("c2", 1),
            ("r", 1),
            ("c3", 1),
            ("r", 1),
            ("c4", 1),
            ("r", 1),
            ("c5", 1),
            ("r", 1),
            ("c6", 1),
            ("r", 1),
            ("c7", 1),
            ("r", 1),
            ("c8", 1),
            ("r", 1),
            ("r", 1),
            ("r", 1),
            ("c4", 1),
            ("r", 1),
            ("c4*", 1),
            ("r", 1),
            ("r", 1),
            ("r", 1),
            ("c4", 16),
            ("r", 1),
            ("c4", 8),
            ("r", 1),
            ("c4", 4),
            ("r", 1),
            ("c4", 1),
            ("r", 1),
            ("c4", 1),
            ("r", 1),
        ),
        fn="all_cs.wav",
    )

    make_wav(
        song4_rh, bpm=130, transpose=1, boost=1.15, repeat=1, fn="pysynth_bach_rh.wav"
    )
    make_wav(
        song4_lh, bpm=130, transpose=1, boost=1.15, repeat=1, fn="pysynth_bach_lh.wav"
    )
    mix_files("pysynth_bach_rh.wav", "pysynth_bach_lh.wav", "pysynth_bach.wav")

    make_wav(song3, bpm=132 / 2, leg_stac=0.9, boost=1.1, fn="pysynth_chopin.wav")
