ttsprech
========

Simple text to speech for the command line using
[silero-models](https://github.com/snakers4/silero-models) and
[NLTK](https://www.nltk.org/).

This runs locally on the CPU, without a need for a GPU.

Output is either provided in the form of `.wav` files or directly as
audio to the speakers. Generation is fast enough for real time use.

Required language model files are downloaded on demand and stored in `~/.cache/ttspeech/`.


Usage
-----

    usage: ttsprech [-h] [-f FILE] [-m FILE] [-l LANGUAGE] [-s SPEAKER] [-r RATE] [-o FILE] [-v] [TEXT ...]

    Text to Speech

    positional arguments:
      TEXT

    optional arguments:
      -h, --help            show this help message and exit
      -f FILE, --file FILE  Convert content of FILE to wav
      -m FILE, --model FILE
                            Model file to use
      -l LANGUAGE, --lang LANGUAGE
                            Use language LANGUAGE
      -s SPEAKER, --speaker SPEAKER
                            Speaker to use
      -r RATE, --rate RATE  Sample rate
      -o FILE, --output FILE
                            Write wave to FILE
      -v, --verbose         Be more verbose


Legal
-----

Note that even so this software is covered under the GPLv3+, the
silero-models used are under [Creative Common
Attribution-NonCommercial-ShareAlike 4.0
International](https://github.com/snakers4/silero-models/blob/master/LICENSE).
