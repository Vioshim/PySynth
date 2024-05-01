import wave
from io import BytesIO
from typing import Iterable

import numpy as np

from .mkfreq import getfreq

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

__all__ = ("make_wav",)


pitchhz, keynum = getfreq()

# Harmonic intensities (dB) for selected piano keys,
# measured with output from a Yamaha P-85
harmo = (
    (1, -15.8, -3.0, -15.3, -22.8, -40.7),
    (16, -15.8, -3.0, -15.3, -22.8, -40.7),
    (28, -5.7, -4.4, -17.7, -16.0, -38.7),
    (40, -6.8, -17.2, -22.4, -16.8, -75.6),
    (52, -8.4, -19.7, -23.5, -21.6, -76.8),
    (64, -9.3, -20.8, -37.2, -36.3, -76.4),
    (76, -18.0, -64.5, -74.4, -77.3, -80.8),
    (88, -24.8, -53.8, -77.2, -80.8, -90.0),
)

harmtab = np.zeros((88, 20))

for h in range(1, len(harmo[0])):
    dat = np.array([(float(harm[0]), harm[h]) for harm in harmo])
    xvals = dat[:, 0]
    ux = np.max(xvals)
    lx = np.min(xvals)
    for h2 in range(88):
        ux_vals = np.where(dat[:, 0] > h2 + 1, dat[:, 0], ux)
        uy = dat[np.argmin(ux_vals), 1]
        lx_vals = np.where(dat[:, 0] < h2 + 1, dat[:, 0], lx)
        ly = dat[np.argmax(lx_vals), 1]
        harmtab[h2, h] = (float(h2 + 1) - lx) / (ux - lx) * (uy - ly) + ly

for h2 in range(88):
    for n in range(20):
        ref = harmtab[h2, 1]
        harmtab[h2, n] = 10.0 ** ((harmtab[h2, n] - ref) / 20.0)

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

att_len = 3000
att_bass = np.array(
    [
        np.interp(
            n,
            [0, 100, 300, 400, 600, 800, 1000, 2000, 3000],
            [0.0, 0.1, 0.2, 0.15, 0.1, 0.9, 1.25, 1.15, 1.0],
        )
        for n in range(att_len)
    ]
)
att_treb = np.array(
    [
        np.interp(
            n,
            [0, 100, 300, 400, 600, 800, 1000, 2000, 3000],
            [0.0, 0.2, 0.7, 0.6, 0.25, 0.9, 1.25, 1.15, 1.0],
        )
        for n in range(att_len)
    ]
)

decay = np.exp(
    np.interp(
        np.linspace(0, 1, 1000),
        np.array([0, 3, 5, 6, 9]),
        [np.log(3), np.log(5), np.log(1.0), np.log(0.8), np.log(0.1)],
    )
)

def make_wav(
    song: Iterable[tuple[str, float]],
    bpm: float = 120.0,
    transpose: float = 0.0,
    leg_stac: float = 0.9,
    pause: float = 0.05,
    boost: float = 1.0,
    repeat: int = 0,
    fn: str | BytesIO = "out.wav",
):
    data = []
    note_cache = {}
    cache_this = {}

    f = wave.open(fn, "w")

    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(44100)
    f.setcomptype("NONE", "Not Compressed")

    bpmfac = 120.0 / bpm

    def length(l):
        return 88200.0 / l * bpmfac

    def waves2(hz, l):
        a = 44100.0 / hz
        b = float(l) / 44100.0 * hz
        return [a, round(b)]

    def render2(a, b, vol, pos, knum, note):
        l = waves2(a, b)
        q = int(l[0] * l[1])

        lf = np.log(a)

        t = (lf - 3.0) / (8.5 - 3.0)
        volfac = 1.0 + 0.8 * t * np.cos(np.pi / 5.3 * (lf - 3.0))
        schweb = waves2(lf * 100.0, b)[0]
        schweb_amp = 0.05 - (lf - 5.0) / 100.0
        att_fac = np.minimum(knum / 87.0 * vol, 1.0)
        snd_len = max(int(3.1 * q), 44100)
        fac = np.ones(snd_len)
        fac[:att_len] = att_fac * att_treb + (1.0 - att_fac) * att_bass

        raw_note = 12 * 44100
        if note not in note_cache:
            x2 = np.arange(raw_note)
            sina = 2.0 * np.pi * x2 / float(l[0])
            ov = np.exp(-x2 / 3.0 / decay[int(lf * 100)] / 44100.0)
            new = (
                np.sin(sina)
                + ov * harmtab[kn, 2] * np.sin(2.0 * sina)
                + ov * harmtab[kn, 3] * np.sin(3.0 * sina)
                + ov * harmtab[kn, 4] * np.sin(4.0 * sina)
                + ov * harmtab[kn, 5] * np.sin(8.0 * sina)
            ) * volfac
            new *= np.exp(-x2 / decay[int(lf * 100)] / 44100.0)
            if cache_this[note] > 1:
                note_cache[note] = new.copy()
        else:
            new = note_cache[note].copy()
        dec_ind = int(leg_stac * q)
        new[dec_ind:] *= np.exp(-np.arange(raw_note - dec_ind) / 3000.0)
        if snd_len > raw_note:
            print("Warning, note too long:", snd_len, raw_note)
            snd_len = raw_note
        data[pos : pos + snd_len] += (
            new[:snd_len]
            * fac
            * vol
            * (
                1.0
                + schweb_amp * np.sin(2.0 * np.pi * np.arange(snd_len) / schweb / 32.0)
            )
        )

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
    data = np.zeros(int((repeat + 1) * t_len + 441000))

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
        ex_pos = ex_pos + b

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

    print("*** EXPERIMENTAL PIANO VERSION WITH NOTE CACHING ***")
    print()
    print("Creating Demo Songs... (this might take about a minute)")
    print()

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
