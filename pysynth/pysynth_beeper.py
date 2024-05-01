import logging
import struct
import wave
from io import BytesIO
from typing import Iterable

import numpy as np

__all__ = ("make_wav",)

keys_s = ("a", "a#", "b", "c", "c#", "d", "d#", "e", "f", "f#", "g", "g#")
PITCHHZ = {
    f"{keys_s[k % 12]}{(k + 9) // 12}": 27.5 * np.exp2(k / 12.0) for k in range(88)
}
# Format:  [(start, end, start_level, end_level), ...]
waveform = [
    (0.0, 0.3, 1.0, -1.0),
    (0.3, 0.5, -1.0, 0.0),
    (0.5, 0.6, 0.0, -0.5),
    (0.6, 1.0, -0.5, 1.0),
]


def make_wav(
    song: Iterable[tuple[str, float]],
    bpm: float = 120.0,  # tempo
    transpose: float = 0.0,
    rate: int = 44100,
    leg_stac: float = 0.9,
    pause: float = 0.05,
    boost: float = 1.0,
    repeat: int = 0,
    fn: str | BytesIO = "out.wav",
):
    # def make_wav(song, tempo=120, transpose=0, fn="out.wav"):
    f = wave.open(fn, "w")

    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(rate)
    f.setcomptype("NONE", "Not Compressed")

    # Define a waveform that looks something like this
    #  \        /
    # __\_____ /__
    #    \  /\/
    #     \/

    # BPM is "quarter notes per minute"
    full_notes_per_second = float(bpm) / 60 / 4
    full_note_in_samples = rate / full_notes_per_second

    def sixteenbit(sample):
        return struct.pack("h", round(32767 * sample))

    def beep_single_period(period, volume: float = 1.0):
        period_waveform = []
        for x in range(period):
            # Position inside current period, 0..1
            pos = float(x) / period
            asin = lambda x: np.sin(2.0 * np.pi * x)

            # Synth 1, using sine waves
            level1 = (asin(pos) + asin(pos * 2)) / 2
            level2 = 0

            # Synth 2, discrete, using waveform definition
            for start, finish, start_level, finish_level in waveform:
                if pos >= start and pos <= finish:
                    localpos = (pos - start) / (finish - start)
                    level2 = (finish_level - start_level) * localpos + start_level
                    break

            # Put both samples together, apply fadein/fadeout
            level = (level1 + level2) / 2
            period_waveform.append(level * volume)
            # period_waveform_packed.append(sixteenbit(level))

        return period_waveform, b"".join(sixteenbit(l) for l in period_waveform)

    def beep(freq, duration, sink, volume):
        ow = b""

        period = int(rate / 4 / freq)
        period_waveform, period_waveform_packed = beep_single_period(period, volume)

        x = 0
        while x < duration:
            if x < 100 or duration - x < 100:
                # At borders we do fade in and fade out
                fade_multiplier = min(x, duration - x) / 100.0
                ow += sixteenbit(period_waveform[x % period] * fade_multiplier)
            else:
                if x % period == 0:
                    # Optimization:
                    # We're aligned with waveform, can fill ow in batches!
                    while x + period + 100 < duration:
                        ow += period_waveform_packed
                        x += period

                # Go sample-by-sample
                ow += sixteenbit(period_waveform[x % period])
            x += 1

        sink.writeframesraw(ow)

    def silence(duration, sink):
        sink.writeframesraw(sixteenbit(0) * int(duration))

    for note_pitch, note_duration in np.tile(song, (repeat + 1, 1)):  # type: ignore
        note_duration = float(note_duration)
        duration = int(full_note_in_samples / note_duration)

        if note_pitch == "r":
            silence(duration, f)
        else:
            if note_pitch[-1] == "*":
                note_pitch = note_pitch[:-1]
                volume = boost
            else:
                volume = 1.0

            freq = PITCHHZ[note_pitch]
            freq *= np.exp2(transpose)
            beep(freq, duration, f, volume)

    f.close()


if __name__ == "__main__":
    song = [
        ("c4*", 4),
        ("d4*", 4),
        ("e4*", 4),
    ]
    make_wav(song, fn="pysynth_beeper.wav", boost=1)
