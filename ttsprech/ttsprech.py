# ttsprech - simple text to wav for the command line
# Copyright (C) 2022 Ingo Ruhnke <grumbel@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from typing import List

import argparse
import os
import sys
import torch
import tempfile
from xdg.BaseDirectory import xdg_cache_home

from ttsprech.player import Player


LANGUAGE_MODEL_URLS = {
    'en':  "https://models.silero.ai/models/tts/en/v3_en.pt",
    'de': "https://models.silero.ai/models/tts/de/v3_de.pt",
    'pt': "https://models.silero.ai/models/tts/es/v3_es.pt",
    'fr': "https://models.silero.ai/models/tts/fr/v3_fr.pt",
    'ua': "https://models.silero.ai/models/tts/ua/v3_ua.pt",
    'uz': "https://models.silero.ai/models/tts/uz/v3_uz.pt",
    'xal': "https://models.silero.ai/models/tts/xal/v3_xal.pt",
    'indic': "https://models.silero.ai/models/tts/indic/v3_indic.pt",
}


NLTK_DATA_PUNKT_DIR = "NLTK_DATA_PUNKT_PLACEHOLDER"


def split_sentences(text: str) -> List[str]:
    NLTK_DATA_PUNKT_DIR = "NLTK_DATA_PUNKT_DIR_PLACEHOLDER"
    if os.path.isdir(NLTK_DATA_PUNKT_DIR):
        import nltk
        tokenize = nltk.data.load(os.path.join(NLTK_DATA_PUNKT_DIR, 'PY3/english.pickle'))
        return tokenize.sentences_from_text(text)
    else:
        print("warning: NLTK_DATA_PUNKT_DIR not set, treating text as one sentence", file=sys.stderr)
        return [text]


def parse_args(args: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Text to Speech")
    group_ex = parser.add_mutually_exclusive_group()
    group_ex.add_argument("-t", "--text", metavar="TETX", type=str, default=None,
                        help="Convert TEXT to wav")
    group_ex.add_argument("-f", "--file", metavar="FILE", type=str, default=None,
                          help="Convert content of FILE to wav")
    parser.add_argument("-m", "--model", metavar="FILE", type=str, default=None,
                        help="Model file to use ")
    parser.add_argument("-l", "--lang", metavar="LANGUAGE", type=str, default='en',
                        help="Use language LANGUAGE")
    parser.add_argument("-s", "--speaker", metavar="SPEAKER", type=str, default=None,
                        help="Speaker to use")
    parser.add_argument("-r", "--rate", metavar="RATE", type=int, default=48000,
                        help="Sample rate")
    parser.add_argument("-p", "--play", action='store_true', default=False,
                        help="Play the generated wav")
    parser.add_argument("-o", "--output", metavar="FILE", type=str, default=None,
                        help="Write wave to FILE")
    return parser.parse_args(args)


def main(argv: List[str]) -> None:
    opts = parse_args(argv[1:])

    cache_dir = os.path.join(xdg_cache_home, "ttsprech")
    if not os.path.isdir(cache_dir):
        os.makedirs(os.path.join(cache_dir))

    if opts.output is None:
        if opts.play:
            tmpdir = tempfile.mkdtemp(prefix="ttsprech-audio-")
            outfile_root, outfile_ext = os.path.splitext(os.path.join(tmpdir, "out.wav"))
        else:
            raise RuntimeError("--output PATH required")
    else:
        outfile_root, outfile_ext = os.path.splitext(opts.output)

    model_file: str
    if opts.model is not None:
        model_file = opts.model
    else:
        model_url = LANGUAGE_MODEL_URLS[opts.lang]
        model_file = os.path.join(cache_dir, f"{opts.lang}.pt")
        if not os.path.isfile(model_file):
            print(f"Downloading {model_url} to {model_file}")
            torch.hub.download_url_to_file(model_url, dst=model_file, progress=True)

    device = torch.device('cpu')
    torch.set_num_threads(torch.multiprocessing.cpu_count())

    model = torch.package.PackageImporter(model_file).load_pickle("tts_models", "model")
    model.to(device)

    print(f"Model: {model_file}")
    print(f"Speakers: {' '.join(model.speakers)}")
    print(f"Languages: {' '.join(LANGUAGE_MODEL_URLS.keys())}")

    if opts.speaker is None:
        speaker = model.speakers[0]
    else:
        if opts.speaker in model.speakers:
            speaker = opts.speaker
        else:
            raise RuntimeError("unknown speaker: {opts.speaker}")

    if opts.file:
        with open(opts.file) as fin:
            text = fin.read()
    else:
        text = opts.text

    if text is None:
        raise RuntimeError("no text given")

    sentences = split_sentences(text)

    if opts.play:
        player = Player()
    else:
        player = None

    for idx, sentence in enumerate(sentences):
        outfile = f"{outfile_root}-{idx:06d}{outfile_ext}"
        print(f"Processing {outfile}: {sentence!r}")
        try:
            audio_path = model.save_wav(audio_path=outfile,
                                        text=sentence,
                                        speaker=speaker,
                                        sample_rate=opts.rate)
            if player is not None:
                player.add(audio_path)

            print(f"Written: {audio_path}")
        except Exception as err:
            # ValueError() is thrown when the sentence only contains numbers
            print(f"error: failed to process {sentence!r}: {err!r}")

    if opts.play:
        player.quit()


def main_entrypoint() -> None:
    main(sys.argv)


if __name__ == "__main__":
    main_entrypoint()


# EOF #
