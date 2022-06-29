ttsprech
========

A simple text to speech tool for the command line using
[silero-models](https://github.com/snakers4/silero-models) or
[coqui-ai/tts](https://github.com/coqui-ai/TTS).

Output is either provided in the form of `.wav` files or directly as
audio to the speakers. Generation is fast enough for real time use
(e.g. narrating longer text), but it will take a couple of seconds
before the first words are said, making it unsuitable for fast
responding interactive use.

It runs locally on the CPU. Neither a GPU or any kind of cloud
services are required. Language models, other than the default, will
however be downloaded on demand when requested.

Required language model files are downloaded on demand and stored in
`~/.cache/ttspeech/`.


Installation
------------

ttsprech is distributed as Nix flake and can be run directly from the
git repository:

    $ nix run github:Grumbel/ttsprech

Nix flakes are still an experimental feature, so a reasonably new
version of Nix and some configuration might be required. See [Nix
Flakes, Part 1: An Introduction And
Tutorial](https://www.tweag.io/blog/2020-05-25-flakes/).

NixOS is not required, the Nix package manager can be installed on
other Linux distributions.


TTS Engines
------------

* [silero-models](https://github.com/snakers4/silero-models) provides
  high quality and reliable voice output, much better than the robotic
  sounding [espeak](http://espeak.sourceforge.net/). It is the default.

* [coqui-ai/tts](https://github.com/coqui-ai/TTS) provides even better
  sounding output than silero, but is much less reliable and a bit
  slower. Overly complex sentence structure will cause it to fail.
  Glitches at the end of the audio output are common.


Usage
-----

    usage: ttsprech [-h] [-v] [-f FILE] [-e ENGINE] [--ssml] [-m FILE] [-l LANGUAGE] [-s SPEAKER]
                    [-r RATE] [-S NUM] [-E NUM] [-T NUM] [-O DIR]
                    [TEXT ...]

    Text to Speech

    positional arguments:
      TEXT

    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbose         Be more verbose
      -f FILE, --file FILE  Convert content of FILE to wav
      -e ENGINE, --engine ENGINE
                            Select the TTS engine to use (coqui, silero)
      --ssml                Interpret text input as SSML
      -m FILE, --model FILE
                            Model file to use
      -l LANGUAGE, --lang LANGUAGE
                            Use language LANGUAGE (default: auto)
      -s SPEAKER, --speaker SPEAKER
                            Speaker to use
      -r RATE, --rate RATE  Sample rate
      -S NUM, --start NUM   Start at sentence NUM
      -E NUM, --end NUM     Stop at sentence NUM
      -T NUM, --threads NUM
                            Number of threads to use
      -O DIR, --output-dir DIR
                            Write .wav files to DIR



Legal
-----

Note that even so this software is covered under the GPLv3+, the
silero-models used are under [Creative Common
Attribution-NonCommercial-ShareAlike 4.0
International](https://github.com/snakers4/silero-models/blob/master/LICENSE).
