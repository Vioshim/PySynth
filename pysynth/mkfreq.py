##########################################################################
# Compute and print piano key frequency table
##########################################################################

import numpy as np

__all__ = ("getfreq", "getfn")

keys_s = np.array(["a", "a#", "b", "c", "c#", "d", "d#", "e", "f", "f#", "g", "g#"])
keys_f = np.array(["a", "bb", "b", "c", "db", "d", "eb", "e", "f", "gb", "g", "ab"])
keys_e = np.array(["a", "bb", "cb", "b#", "db", "d", "eb", "fb", "e#", "gb", "g", "ab"])


def getfreq(pr: bool = False):
    pitchhz, keynum = {}, {}

    if pr:
        print("Piano key frequencies (for equal temperament):")
        print("Key number\tScientific name\tFrequency (Hz)")

    k = np.arange(88)
    freq = 27.5 * 2.0 ** (k / 12.0)
    oct = (k + 9) // 12
    for idx in range(88):
        note = "%s%u" % (keys_s[idx % 12], oct[idx])
        keynum[note], pitchhz[note] = idx, freq[idx]
        note = "%s%u" % (keys_f[idx % 12], oct[idx])
        keynum[note], pitchhz[note] = idx, freq[idx]
        note = "%s%u" % (keys_e[idx % 12], oct[idx])
        keynum[note], pitchhz[note] = idx, freq[idx]

    if pr:
        for idx in range(88):
            note = "%s%u" % (keys_s[idx % 12], oct[idx])
            print("%10u\t%15s\t%14.2f" % (idx + 1, note.upper(), pitchhz[note]))

    return pitchhz, keynum


# construct filenames for Salamander piano samples
facs = np.exp2(np.arange(3) / 12)
nam = ["A", "C", "D#", "F#"]


def getfn(layer: int):
    return {
        k: ("%s%uv%u.wav" % (nam[(k // 3) % 4], ((k + 9) // 12), layer), facs[k % 3])
        for k in range(88)
    }
