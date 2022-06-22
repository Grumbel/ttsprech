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

import logging
import os
import sys
import torch


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


def silero_languages() -> List[str]:
    return list(LANGUAGE_MODEL_URLS.keys())


def silero_model_from_file(model_file: str) -> Any:
    device = torch.device('cpu')
    torch.set_num_threads(4)  # more than 4 does not provide a speedup

    logger.info(f"loading silero model: {model_file}")
    model = torch.package.PackageImporter(model_file).load_pickle("tts_models", "model")
    model.to(device)

    logger.info(f"    Model: {model_file}")
    logger.info(f"Languages: {' '.join(LANGUAGE_MODEL_URLS.keys())}")
    logger.info(f"  peakers: {' '.join(model.speakers)}")

    return model


def silero_model_from_language(language: str, cache_dir: str) -> Any:
    if language not in LANGUAGE_MODEL_URLS:
        raise RuntimeError(f"unknown language '{language}', must be one of:\n  "
                           f"{' '.join(LANGUAGE_MODEL_URLS.keys())}")

    model_url = LANGUAGE_MODEL_URLS[language]
    model_file = os.path.join(cache_dir, f"{language}.pt")

    if not os.path.isfile(model_file):
        print(f"Downloading {model_url} to {model_file}", file=sys.stderr)
        torch.hub.download_url_to_file(model_url, dst=model_file, progress=True)

    return silero_model_from_file(model_file)


# EOF #
