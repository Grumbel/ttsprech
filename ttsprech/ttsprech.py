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


from typing import Any, List, Optional, Tuple

import argparse
import logging
import nltk
import os
import sys
import tempfile
import torch
from concurrent.futures import ThreadPoolExecutor, Future
from xdg.BaseDirectory import xdg_cache_home

from ttsprech.player import Player


logger = logging.getLogger(__name__)


LANGUAGE_MODEL_URLS = {
    'en': "https://models.silero.ai/models/tts/en/v3_en.pt",
    'de': "https://models.silero.ai/models/tts/de/v3_de.pt",
    'pt': "https://models.silero.ai/models/tts/es/v3_es.pt",
    'fr': "https://models.silero.ai/models/tts/fr/v3_fr.pt",
    'ua': "https://models.silero.ai/models/tts/ua/v3_ua.pt",
    'uz': "https://models.silero.ai/models/tts/uz/v3_uz.pt",
    'xal': "https://models.silero.ai/models/tts/xal/v3_xal.pt",
    'indic': "https://models.silero.ai/models/tts/indic/v3_indic.pt",
}

NLTK_DATA_PUNKT_DIR = "NLTK_DATA_PUNKT_DIR_PLACEHOLDER"


def parse_args(args: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Text to Speech")
    parser.add_argument("TEXT", nargs='*')
    parser.add_argument("-v", "--verbose", action='store_true', default=False,
                        help="Be more verbose")
    parser.add_argument("-f", "--file", metavar="FILE", type=str, default=None,
                        help="Convert content of FILE to wav")
    parser.add_argument("-m", "--model", metavar="FILE", type=str, default=None,
                        help="Model file to use ")
    parser.add_argument("-l", "--lang", metavar="LANGUAGE", type=str, default='en',
                        help="Use language LANGUAGE")
    parser.add_argument("-s", "--speaker", metavar="SPEAKER", type=str, default=None,
                        help="Speaker to use")
    parser.add_argument("-r", "--rate", metavar="RATE", type=int, default=48000,
                        help="Sample rate")
    parser.add_argument("-S", "--start", metavar="NUM", type=int, default=0,
                        help="Start at sentence NUM")
    parser.add_argument("-T", "--threads", metavar="NUM", type=int, default=None,
                        help="Number of threads to use")
    parser.add_argument("-O", "--output-dir", metavar="DIR", type=str, default=None,
                        help="Write .wav files to DIR")
    return parser.parse_args(args)


def setup_cachedir() -> str:
    cache_dir = os.path.join(xdg_cache_home, "ttsprech")

    if not os.path.isdir(cache_dir):
        os.makedirs(os.path.join(cache_dir))

    return cache_dir


def setup_output_dir(opts: argparse.Namespace) -> str:
    output_dir: str

    if opts.output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="ttsprech-audio-")
    else:
        output_dir = opts.output_dir
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)

    return output_dir


def setup_text(opts: argparse.Namespace) -> str:
    text: str

    if opts.file:
        with open(opts.file) as fin:
            text = fin.read()
    else:
        if not opts.TEXT:
            raise RuntimeError("no text given")

        text = " ".join(opts.TEXT)

    if text is None:
        raise RuntimeError("no text given, use --text TEXT or --file PATH")

    return text


def setup_model(opts: argparse.Namespace, cache_dir: str) -> Any:
    model_file: str

    if opts.model is not None:
        model_file = opts.model
    else:
        if opts.lang not in LANGUAGE_MODEL_URLS:
            raise RuntimeError(f"unknown language '{opts.lang}', must be one of:\n"
                               f"{' '.join(LANGUAGE_MODEL_URLS.keys())}")

        model_url = LANGUAGE_MODEL_URLS[opts.lang]
        model_file = os.path.join(cache_dir, f"{opts.lang}.pt")
        if not os.path.isfile(model_file):
            print(f"Downloading {model_url} to {model_file}", file=sys.stderr)
            torch.hub.download_url_to_file(model_url, dst=model_file, progress=True)

    device = torch.device('cpu')
    torch.set_num_threads(4)  # more than 4 does not provide a speedup

    # model
    logger.info(f"loading silero model: {model_file}")
    model = torch.package.PackageImporter(model_file).load_pickle("tts_models", "model")
    model.to(device)

    logger.info(f"Model: {model_file}")
    logger.info(f"Languages: {' '.join(LANGUAGE_MODEL_URLS.keys())}")
    logger.info(f"Speakers: {' '.join(model.speakers)}")

    return model


def setup_speaker(opts: argparse.Namespace, model: Any) -> str:
    speaker: str

    if opts.speaker is None:
        speaker = model.speakers[0]
    else:
        if opts.speaker in model.speakers:
            speaker = opts.speaker
        else:
            raise RuntimeError(f"unknown speaker: '{opts.speaker}', must be one of:\n{' '.join(model.speakers)}")

    return speaker


def setup_sentences(opts: argparse.Namespace, text: str) -> List[str]:
    if os.path.isdir(NLTK_DATA_PUNKT_DIR):
        nltk_data_punkt_file = os.path.join(NLTK_DATA_PUNKT_DIR, 'PY3/english.pickle')
    else:
        logging.info("NLTK_DATA_PUNKT_DIR not set, downloading it instead")
        download_dir = os.path.join(xdg_cache_home, "ttsprech", "nltk")
        nltk.download(download_dir=download_dir, quiet=(not opts.verbose),
                      info_or_id="punkt", raise_on_error=True)
        nltk_data_punkt_file = os.path.join(download_dir, 'tokenizers/punkt/PY3/english.pickle')

    logger.info(f"loading NLTK model: {nltk_data_punkt_file}")
    tokenize = nltk.data.load(nltk_data_punkt_file)
    sentences: List[str] = tokenize.sentences_from_text(text)

    return sentences


def run(opts: argparse.Namespace, model: Any, speaker: str, sentences: List[str], output_dir: str) -> None:
    use_player = opts.output_dir is None

    def generate_wave(text: str, outfile: str) -> Optional[str]:
        logger.info(f"Processing {outfile}: {text!r}")
        try:
            audio_path = model.save_wav(audio_path=outfile,
                                        text=text,
                                        speaker=speaker,
                                        sample_rate=opts.rate)
            logger.info(f"Written: {audio_path}")
        except Exception as err:
            # ValueError() is thrown when the text only contains numbers
            logger.error(f"failed to process {text!r}: {err!r}")
            return None
        finally:
            return outfile

    # Each silero-model is using 4 threads, but doesn't fully utilize
    # them, so divide by 2 instead of 4, to approximate the thread
    # count.
    max_workers: int
    if opts.threads is not None:
        max_workers = max(1, opts.threads // 2)
    else:
        max_workers = max(1, (os.cpu_count() or 1) // 2)

    with ThreadPoolExecutor(max_workers) as executor:
        output_files: List[Tuple[str, Future[Optional[str]]]] = []

        for idx, sentence in enumerate(sentences):
            if (idx + 1) < opts.start:
                future: Future[Optional[str]] = Future()
                future.set_result(None)
                output_files.append((sentence, future))
            else:
                outfile = os.path.join(output_dir, f"{idx:06d}.wav")
                output_files.append((sentence, executor.submit(generate_wave, sentence, outfile)))

        if use_player:
            files_to_cleanup: List[str] = []

            with Player(len(output_files)) as player:
                for text, outfile_future in output_files:
                    maybe_wavfile = outfile_future.result()
                    if maybe_wavfile:
                        files_to_cleanup.append(maybe_wavfile)
                    player.add(text, maybe_wavfile)

            # cleanup
            logger.info("cleaning up generated files")
            for file in files_to_cleanup:
                logger.info(f"removing file '{file}'")
                os.remove(file)
            logger.info(f"removing directory '{output_dir}'")
            os.rmdir(output_dir)


def main(argv: List[str]) -> None:
    opts = parse_args(argv[1:])

    if opts.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    cache_dir = setup_cachedir()
    output_dir = setup_output_dir(opts)
    text = setup_text(opts)
    model = setup_model(opts, cache_dir)
    speaker = setup_speaker(opts, model)
    sentences = setup_sentences(opts, text)

    run(opts, model, speaker, sentences, output_dir)


def main_entrypoint() -> None:
    try:
        main(sys.argv)
    except RuntimeError as err:
        print(f"error: {err}", file=sys.stderr)


if __name__ == "__main__":
    main_entrypoint()


# EOF #
