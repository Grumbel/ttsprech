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

import logging
import nltk
from num2words import num2words

logger = logging.getLogger(__name__)


def replace_numbers_with_words(text: str) -> str:
    result: List[str] = []

    tokens: List[str] = nltk.tokenize.regexp_tokenize(text, r'\d+\.\d+|\d+|[^\d]+')
    for token in tokens:
        try:
            result.append(num2words(float(token)))
        except ValueError:
            result.append(token)

    return ' '.join(result)


# EOF #
