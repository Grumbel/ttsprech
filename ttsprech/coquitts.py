# ttsprech - Simple text to wav for the command line
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


from typing import Any, List, Tuple, Optional, TYPE_CHECKING

import time
from threading import Lock
from pathlib import Path

if TYPE_CHECKING:
    from TTS.utils.synthesizer import Synthesizer


class CoquittsModel:

    def __init__(self, synthesizers: List[Any]) -> None:
        self._synthesizers = synthesizers
        self._locks = [Lock() for _ in range(len(self._synthesizers))]

    @property
    def speakers(self) -> List[str]:
        return [""]  # self._synthesizer.tts_model.speaker_manager.ids

    @property
    def languages(self) -> List[str]:
        return [""]  # cast(List[str], self._synthesizer.tts_model.language_manager.ids)

    def save_wav(self, outfile: str, text: str, speaker: str, sample_rate: int, ssml: bool) -> None:
        lock, synthesizer = self._find_synth()

        with lock:
            wav: List[int] = synthesizer.tts(
                text=text,
                speaker_name="",
                language_name="",
            )
            synthesizer.save_wav(wav, outfile)

    def _find_synth(self) -> Tuple[Lock, 'Synthesizer']:
        while True:
            for lock, synthesizer in zip(self._locks, self._synthesizers):
                if not lock.locked():
                    return lock, synthesizer
            time.sleep(0.1)


def coquitts_model_from_language(language: str) -> CoquittsModel:
    # this takes a considerable amount of time to load, so load it
    # only when coquitts is actually used
    import TTS
    from TTS.utils.manage import ModelManager
    from TTS.utils.synthesizer import Synthesizer

    models_json = Path(TTS.__file__).parent / ".models.json"
    manager = ModelManager(models_json)
    manager.list_models()

    model_name = "tts_models/en/ljspeech/tacotron2-DDC"

    model_path, config_path, model_item = manager.download_model(model_name)
    vocoder_name = model_item["default_vocoder"]
    vocoder_path, vocoder_config_path, _ = manager.download_model(vocoder_name)

    speakers_file_path: Optional[str] = None
    language_ids_file_path: Optional[str] = None
    encoder_path: Optional[str] = None
    encoder_config_path: Optional[str] = None
    use_cuda = False

    # Synthesizer is not thread safe, so we need to create multiple
    synthesizers = [Synthesizer(model_path,
                                config_path,
                                speakers_file_path,
                                language_ids_file_path,
                                vocoder_path,
                                vocoder_config_path,
                                encoder_path,
                                encoder_config_path,
                                use_cuda)
                    for _ in range(4)]

    return CoquittsModel(synthesizers)


# EOF #
