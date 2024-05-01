#!/usr/bin/env python

"""
##########################################################################
#                       * * *  PySynth  * * *
#       A very basic audio synthesizer in Python (www.python.org)
#
#          Martin C. Doege, 2017-06-25 (mdoege@compuserve.com)
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

import os
import shutil
import struct
import tarfile
import wave
from io import BytesIO
from typing import Iterable

import numpy as np

from .mkfreq import getfn, getfreq

__all__ = ("make_wav",)

# path to Salamander piano samples (http://freepats.zenvoid.org/Piano/acoustic-grand-piano.html),
#       48 kHz version:

patchpath = os.path.join(os.path.dirname(__file__), "48khz24bit/")

if not os.path.exists(patchpath):

    if __name__ != "__main__":
        raise FileNotFoundError(
            "Piano samples not found. Please run this file as a script."
        )

    import requests

    DOWNLOAD_URL = "https://freepats.zenvoid.org/Piano/SalamanderGrandPiano/SalamanderGrandPianoV3+20161209_48khz24bit.tar.xz"

    tar_file = os.path.join(os.path.dirname(__file__), os.path.basename(DOWNLOAD_URL))

    with requests.get(DOWNLOAD_URL, stream=True) as response:
        with open(tar_file, "wb") as f:
            shutil.copyfileobj(response.raw, f)

        with tarfile.open(tar_file, "r:xz") as tar:
            tar.extractall(path=os.path.dirname(__file__))
            extracted_folder = tar.getnames()[0]

        folder_name = os.path.join(os.path.dirname(__file__), extracted_folder)
        correct_folder_name = os.path.join(os.path.dirname(__file__), "48khz24bit")
        shutil.move(os.path.join(folder_name, "48khz24bit"), correct_folder_name)
        os.remove(tar_file)
        shutil.rmtree(folder_name)


pitchhz, keynum = getfreq()

# get filenames for sample layer 10:
fnames = getfn(10)

# Preload all samples

notes_cache: dict[str, np.ndarray] = {}


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

##########################################################################


def make_wav(
    song: Iterable[tuple[str, float]],
    bpm: float = 120.0,
    transpose: float = 0.0,
    leg_stac: float = 0.9,
    pause: float = 0.05,
    boost: float = 1.1,
    repeat: int = 0,
    fn: str | BytesIO = "out.wav",
):
    f = wave.open(fn, "w")
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(48000)
    f.setcomptype("NONE", "Not Compressed")

    bpmfac = 120.0 / bpm

    def length(l: float):
        return 96000.0 / l * bpmfac

    def getval(v: bytes):
        a = struct.unpack("i", v + b"\x00")[0] / 256 - 32768
        if a > 0:
            a = 1 - a / 32768
        else:
            a = -1 - a / 32768
        return a

    def render2(a, b, vol, pos, knum, note):
        snd_len = int(b)
        if note not in notes_cache:
            with wave.open(patchpath + fnames[knum][0], "rb") as wf:
                wl = wf.getnframes()
                wd = wf.readframes(wl)
                notes_cache[note] = np.array(
                    [getval(wd[6 * x : 6 * x + 3]) for x in range(wl // 6)]
                )

        new = notes_cache[note].copy()
        f = fnames[knum][1]
        if f > 1:
            f2 = int(len(new) / f)
            new2 = np.zeros(f2)
            for x in range(f2):
                q = x * f - int(x * f)
                new2[x] = (1 - q) * new[int(x * f)] + q * new[int(x * f) + 1]
        else:
            new2 = new
        raw_note = len(new2)

        dec_ind = int(leg_stac * b)
        new2[dec_ind:] *= np.exp(-np.arange(raw_note - dec_ind) / 3000.0)
        new2[-1001:] *= np.arange(1, -0.001, -0.001)
        if snd_len > raw_note:
            snd_len = raw_note
        data[pos : pos + snd_len] += new2[:snd_len] * vol

    ex_pos = 0.0
    t_len = 0
    for y, x in song:
        if x < 0:
            t_len += length(-2.0 * x / 3.0)
        else:
            t_len += length(x)
    data = np.zeros(int((repeat + 1) * t_len + 480000))

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
            note += "4"

        a = pitchhz[note] * np.exp2(transpose)
        kn = keynum[note]

        if y < 0:
            b = length(-2.0 * y / 3.0)
        else:
            b = length(y)

        render2(a, b, vol, int(ex_pos), kn, note)
        ex_pos += b

    data /= data.max() * 2.0
    out_len = int(2.0 * 48000.0 + ex_pos + 0.5)
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

    print("*** SAMPLER ***")
    print()
    print("Creating Demo Songs... (this might take about a minute)")
    print()

    make_wav(song1, fn="pysynth_scale.wav")

    make_wav(
        song4_rh, bpm=130, transpose=1, boost=1.15, repeat=1, fn="pysynth_bach_rh.wav"
    )
    make_wav(
        song4_lh, bpm=130, transpose=1, boost=1.15, repeat=1, fn="pysynth_bach_lh.wav"
    )
    mix_files("pysynth_bach_rh.wav", "pysynth_bach_lh.wav", "pysynth_bach.wav")

    # make_wav(song3, bpm = 132/2, leg_stac = 0.9, boost = 1.1, fn = "pysynth_chopin.wav")
