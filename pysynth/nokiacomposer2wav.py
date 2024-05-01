import logging
import re

from . import pysynth_beeper

__all__ = ("parse_ringtone",)


def parse_ringtone(tune_str):
    return [
        (
            ("r" if pitch == "-" else pitch) + sharp + octave,
            -int(duration) if dotted else int(duration),
        )
        for duration, dotted, sharp, pitch, octave in re.findall(
            r"([0-9]+)(\.?)(#?)([\w-])([0-9]?)", tune_str
        )
    ]


if __name__ == "__main__":
    import os
    import sys

    LOG = logging.getLogger("nokiacomposer2wav")
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    data = []
    data.append(
        (
            "eiffel_65_im_blue.wav",
            160,
            "4a1 4#a1 8g1 8#a1 8c2 8f1 8a1 4#a1 8g1 8#a1 8d2 4#d2 8d2 8c2 4#a1 8g1 8#a1 8c2 8f1 8a1 4#a1 8g1 8#a1 8d2 4#d2 8d2 8c2 4#a1 8g1 8#a1 8c2 8f1 8a1 4#a1 8g1 8#a1 8d2 4#d2 8d2 8c2 4#a1 8g1 8#a1 8a1 8f1 8f1 2g1",
        )
    )
    data.append(
        (
            "eminem_slim_shady.wav",
            160,
            "8c2 8#d2 8g1 8#g1 4c2 8- 8#g1 4g1 8- 8#g1 16g1 16#g1 8g1 8#f1 8g1 8c2 8#d2 8g1 8#g1 4c2 8- 8#g1 4g1 8- 8#g1 16g1 16#g1 8g1 8#f1 8g1 8c2 8#d2 8g1 8#g1 4c2 8- 8#g1 4g1 8- 8#g1 16g1 16#g1 8g1 8#f1 8g1",
        )
    )
    data.append(
        (
            "michael_jackson_smooth_criminal.wav",
            100,
            "8a1 16a1 16a1 16g1 16a1 8b1 8b1 8- 16a1 16b1 8c2 8c2 8- 16b1 16c2 8b1 4g1 8a1 8- 8a1 16a1 16a1 16g1 16a1 8b1 8b1 8- 16a1 16b1 8c2 8c2 8- 16b1 16c2 8b1 4g1",
        )
    )
    data.append(
        (
            "fur_elise.wav",
            160,
            "8e2 8#d2 8e2 8#d2 8e2 8b1 8d2 8c2 4a1 8- 8c1 8e1 8a1 4b1 8- 8e1 8#g1 8b1 4c2 8- 8e1 8e2 8#d2 8e2 8#d2 8e2 8b1 8d2 8c2 4a1 8- 8c1 8e1 8a1 4b1 8- 8e1 8c2 8b1 4a1",
        )
    )
    data.append(
        (
            "southpark_uncle_fucka.wav",
            160,
            "8e2 8e2 8e2 8e2 4e2 8d2 8c2 8a1 2c2 8- 8c2 8d2 8e2 8e2 8e2 8e2 8e2 8e2 8d2 8c2 8a1 2c2 8- 8c2 8c2 8d2 8d2 8d2 8b1 8c2 8d2 8e2 16- 16e2 16f2 16f2 8e2 8d2 8c2 8b1 8c2 8d2",
        )
    )

    if not os.path.exists("out"):
        os.mkdir("out")

    for filename, bpm, tune_str in data:
        tune = parse_ringtone(tune_str)
        filename = os.path.join("out", filename)
        LOG.info("Generating %s" % filename)
        pysynth_beeper.make_wav(tune, fn=filename, bpm=bpm, transpose=3)
