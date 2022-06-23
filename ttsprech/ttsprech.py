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
import os
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, Future
from xdg.BaseDirectory import xdg_cache_home

import langdetect
import nltk

from ttsprech.player import Player
from ttsprech.tokenize import replace_numbers_with_words
from ttsprech.silero import (silero_model_from_file, silero_model_from_language,
                             silero_languages)

logger = logging.getLogger(__name__)


NLTK_DATA_PUNKT_DIR = "NLTK_DATA_PUNKT_DIR_PLACEHOLDER"


def parse_args(args: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Text to Speech")
    parser.add_argument("TEXT", nargs='*')
    parser.add_argument("-v", "--verbose", action='store_true', default=False,
                        help="Be more verbose")
    parser.add_argument("-f", "--file", metavar="FILE", type=str, default=None,
                        help="Convert content of FILE to wav")
    parser.add_argument("--ssml", action='store_true', default=False,
                        help="Interpret text input as SSML")
    parser.add_argument("-m", "--model", metavar="FILE", type=str, default=None,
                        help="Model file to use ")
    parser.add_argument("-l", "--lang", metavar="LANGUAGE", type=str, default=None,
                        help="Use language LANGUAGE (default: auto)")
    parser.add_argument("-s", "--speaker", metavar="SPEAKER", type=str, default=None,
                        help="Speaker to use")
    parser.add_argument("-r", "--rate", metavar="RATE", type=int, default=48000,
                        help="Sample rate")
    parser.add_argument("-S", "--start", metavar="NUM", type=int, default=0,
                        help="Start at sentence NUM")
    parser.add_argument("-E", "--end", metavar="NUM", type=int, default=None,
                        help="Stop at sentence NUM")
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


def setup_nltk_tokenize(opts: argparse.Namespace) -> Any:
    if os.path.isdir(NLTK_DATA_PUNKT_DIR):
        nltk_data_punkt_file = os.path.join(NLTK_DATA_PUNKT_DIR, 'PY3/english.pickle')
    else:
        logging.info("NLTK_DATA_PUNKT_DIR not set, downloading it instead")
        download_dir = os.path.join(xdg_cache_home, "ttsprech", "nltk")
        nltk.download(download_dir=download_dir, quiet=not opts.verbose,
                      info_or_id="punkt", raise_on_error=True)
        nltk_data_punkt_file = os.path.join(download_dir, 'tokenizers/punkt/PY3/english.pickle')

    logger.info(f"loading NLTK model: {nltk_data_punkt_file}")
    tokenize = nltk.data.load(nltk_data_punkt_file)

    return tokenize


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


def setup_language(text: str, opts: argparse.Namespace) -> str:
    language: str

    if opts.lang is None:
        language = langdetect.detect(text)
        logger.info(f"autodetected language: '{language}'")
        if language not in silero_languages():
            logger.warning(f"autodetected '{language}' not available, fallback to 'en'")
            language = "en"
    else:
        language = opts.lang

    return language


def setup_model(opts: argparse.Namespace, language: str, cache_dir: str) -> Any:
    model: Any

    if opts.model is not None:
        model = silero_model_from_file(opts.model)
    else:
        model = silero_model_from_language(language, cache_dir)

    return model


def setup_speaker(opts: argparse.Namespace, model: Any) -> str:
    speaker: str

    if opts.speaker is None:
        speaker = model.speakers[0]
    else:
        if opts.speaker in model.speakers:
            speaker = opts.speaker
        else:
            raise RuntimeError(f"unknown speaker: '{opts.speaker}', must be one of:\n  "
                               f"{' '.join(model.speakers)}")

    return speaker


def setup_sentences(opts: argparse.Namespace, nltk_tokenize: Any, text: str) -> List[str]:
    if opts.ssml:
        return [text]

    sentences: List[str] = nltk_tokenize.sentences_from_text(text)
    sentences = [replace_numbers_with_words(sentence) for sentence in sentences]

    return sentences


def setup_max_workers(opts: argparse.Namespace) -> int:
    # Each silero-model is using 4 threads, but doesn't fully utilize
    # them, so divide by 2 instead of 4, to approximate the thread
    # count.
    max_workers: int

    if opts.threads is not None:
        max_workers = max(1, opts.threads // 2)
    else:
        max_workers = max(1, (os.cpu_count() or 1) // 2)

    return max_workers


def run(opts: argparse.Namespace, model: Any, speaker: str, sentences: List[str],
        output_dir: str, max_workers: int) -> None:
    use_player = opts.output_dir is None

    def generate_wave(text: str, outfile: str) -> Optional[str]:
        logger.info(f"Processing {outfile}: {text!r}")
        try:
            if opts.ssml:
                audio_path = model.save_wav(audio_path=outfile,
                                            ssml_text=text,
                                            speaker=speaker,
                                            sample_rate=opts.rate)
            else:
                audio_path = model.save_wav(audio_path=outfile,
                                            text=text,
                                            speaker=speaker,
                                            sample_rate=opts.rate)
            logger.info(f"Written: {audio_path}")
        except ValueError as err:
            # ValueError() is thrown when the text only contains numbers
            logger.error(f"failed to process {text!r}: {err!r}")
            return None

        return outfile

    with ThreadPoolExecutor(max_workers) as executor:
        output_files: List[Tuple[str, Future[Optional[str]]]] = []

        for idx, sentence in enumerate(sentences):
            skip_sentence = (((idx + 1) < opts.start) or
                             (opts.end is not None and (idx + 1) >= opts.end))
            if skip_sentence:
                future: Future[Optional[str]] = Future()
                future.set_result(None)
                output_files.append((sentence, future))
            else:
                outfile = os.path.join(output_dir, f"{idx + 1:06d}.wav")
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
    nltk_tokenize = setup_nltk_tokenize(opts)
    output_dir = setup_output_dir(opts)
    text = setup_text(opts)
    language = setup_language(text, opts)
    model = setup_model(opts, language, cache_dir)
    speaker = setup_speaker(opts, model)
    sentences = setup_sentences(opts, nltk_tokenize, text)
    max_workers = setup_max_workers(opts)

    run(opts, model, speaker, sentences, output_dir, max_workers)


def main_entrypoint() -> None:
    try:
        main(sys.argv)
    except RuntimeError as err:
        print(f"error: {err}", file=sys.stderr)


if __name__ == "__main__":
    main_entrypoint()


# EOF #
