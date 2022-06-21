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

    ttsprech --help
    usage: ttsprech [-h] [-t TETX | -f FILE] [-m FILE] [-l LANGUAGE] [-s SPEAKER] [-r RATE] [-p] [-o FILE]

    Text to Speech

    optional arguments:
      -h, --help            show this help message and exit
      -t TETX, --text TETX  Convert TEXT to wav
      -f FILE, --file FILE  Convert content of FILE to wav
      -m FILE, --model FILE
                            Model file to use
      -l LANGUAGE, --lang LANGUAGE
                            Use language LANGUAGE
      -s SPEAKER, --speaker SPEAKER
                            Speaker to use
      -r RATE, --rate RATE  Sample rate
      -p, --play            Play the generated wav
      -o FILE, --output FILE
                            Write wave to FILE


Legal
-----

Note that even so this software is covered under the GPLv3+, the
silero-models used are under [Creative Common
Attribution-NonCommercial-ShareAlike 4.0
International](https://github.com/snakers4/silero-models/blob/master/LICENSE).
