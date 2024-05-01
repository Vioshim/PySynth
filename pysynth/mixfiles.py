#!/usr/bin/env python

# Mix two mono files to get a stereo file

import struct
import sys
import wave
from io import BytesIO

__all__ = ("mix_files", "append_files")


def mix_files(a, b, c, chann=2, phase=-1.0):
    f1 = wave.open(a, "r")
    f2 = wave.open(b, "r")

    r1, r2 = f1.getframerate(), f2.getframerate()
    if r1 != r2:
        print("Error: frame rates must be the same!")
        sys.exit(1)

    f3 = wave.open(c, "w")
    f3.setnchannels(chann)
    f3.setsampwidth(2)
    f3.setframerate(r1)
    f3.setcomptype("NONE", "Not Compressed")
    frames = min(f1.getnframes(), f2.getnframes())

    print("Mixing files, total length %.2f s..." % (frames / float(r1)))
    d1 = f1.readframes(frames)
    d2 = f2.readframes(frames)
    for n in range(frames):
        if not n % (5 * r1):
            print(n // r1, "s")
        if chann < 2:
            d3 = struct.pack(
                "h",
                int(
                    0.5
                    * (
                        struct.unpack("h", d1[2 * n : 2 * n + 2])[0]
                        + struct.unpack("h", d2[2 * n : 2 * n + 2])[0]
                    )
                ),
            )
        else:
            d3 = struct.pack(
                "h",
                int(
                    phase * 0.3 * struct.unpack("h", d1[2 * n : 2 * n + 2])[0]
                    + 0.7 * struct.unpack("h", d2[2 * n : 2 * n + 2])[0]
                ),
            ) + struct.pack(
                "h",
                int(
                    0.7 * struct.unpack("h", d1[2 * n : 2 * n + 2])[0]
                    + phase * 0.3 * struct.unpack("h", d2[2 * n : 2 * n + 2])[0]
                ),
            )
        f3.writeframesraw(d3)
    f3.close()


def append_files(output: str | BytesIO = "output.wav", *files: str | BytesIO):
    f3 = wave.open(output, "w")

    f3.setnchannels(1)
    f3.setsampwidth(2)
    f3.setframerate(44100)
    f3.setcomptype("NONE", "Not Compressed")

    for file in files:
        file.seek(0) if isinstance(file, BytesIO) else None
        f = wave.open(file, "r")
        f3.writeframes(f.readframes(f.getnframes()))
        f.close()

    f3.close()


if __name__ == "__main__":
    if len(sys.argv) == 4:
        a, b, c = sys.argv[1:]
        print("Mixing %s and %s, output will be %s" % (a, b, c))
        mix_files(a, b, c)
