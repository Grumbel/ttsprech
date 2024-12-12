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


from typing import Any, List

import re
import logging
import nltk
from num2words import num2words

logger = logging.getLogger(__name__)


LETTER2WORD = {
    "a": "aie",
    "b": "bee",
    "c": "see",
    "d": "dee",
    "e": "eee",
    "f": "eff",
    "g": "gee",
    "h": "eigch",
    "i": "I",
    "j": "jei",
    "k": "kay",
    "l": "el",
    "m": "em",
    "n": "en",
    "o": "oe",
    "p": "peee",
    "q": "kjuu",
    "r": "arr",
    "s": "es",
    "t": "tee",
    "u": "yuu",
    "v": "vee",
    "w": "doubl-yuu",
    "x": "eks",
    "y": "why",
    "z": "zed",
}


def prepare_text_for_tts(nltk_tokenize: Any, text: str) -> List[str]:
    text = replace_numbers_with_words(text)

    # FIXME: This causes more problems than it fixes. Need better way
    # to detect acronyms.
    # text = replace_uppercase_with_words(text)

    text = text.replace(",", ".")

    sentences: List[str] = nltk_tokenize.sentences_from_text(text)

    return sentences


def replace_numbers_with_words(text: str) -> str:
    result: List[str] = []

    tokens: List[str] = nltk.tokenize.regexp_tokenize(text, r'\d+\.\d+|\d+|[^\d]+')
    for token in tokens:
        try:
            result.append(num2words(float(token)))
        except ValueError:
            result.append(token)

    return ' '.join(result)


def replace_uppercase_with_words(text: str) -> str:
    words = re.split(r'\s', text)
    result: List[str] = []
    for word in words:
        if re.match(r'^[A-Z]+$', word):  # uppercase
            for character in word:
                result.append(LETTER2WORD[character.lower()])
        else:
            result.append(word)

    return ' '.join(result)


# EOF #
