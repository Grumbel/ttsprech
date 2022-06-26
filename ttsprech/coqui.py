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


from typing import Any, Dict, List, Tuple, Optional, TYPE_CHECKING

import time
from threading import Lock
from pathlib import Path

if TYPE_CHECKING:
    from TTS.utils.synthesizer import Synthesizer


class CoquiModel:

    def __init__(self, synthesizer_args: Dict[str, Any]) -> None:
        self._synthesizer_args = synthesizer_args
        self._synthesizers = []
        self._locks = []
        self._self_lock = Lock()

    @property
    def speakers(self) -> List[str]:
        return [""]  # self._synthesizer.tts_model.speaker_manager.ids

    @property
    def languages(self) -> List[str]:
        return [""]  # cast(List[str], self._synthesizer.tts_model.language_manager.ids)

    def save_wav(self, outfile: str, text: str, speaker: str, sample_rate: int, ssml: bool) -> None:
        del sample_rate  # FIXME: ignore sample_rate for now

        if ssml:
            # https://github.com/coqui-ai/TTS/pull/1452
            raise RuntimeError("SSML is not supported by 'conqui'")

        lock, synthesizer = self._find_synth()
        with lock:
            wav: List[int] = synthesizer.tts(
                text=text,
                speaker_name=speaker,
                language_name="",
            )
            synthesizer.save_wav(wav, outfile)

    def _find_synth(self) -> Tuple[Lock, 'Synthesizer']:
        from TTS.utils.synthesizer import Synthesizer

        with self._self_lock:
            for idx, (lock, synthesizer) in enumerate(zip(self._locks, self._synthesizers)):
                if not lock.locked():
                    return lock, synthesizer
            else:
                synthesizer = Synthesizer(**self._synthesizer_args)
                lock = Lock()
                self._synthesizers.append(synthesizer)
                self._locks.append(lock)
                return lock, synthesizer


def coqui_model_from_language(language: str) -> CoquiModel:
    model_name = "tts_models/en/ljspeech/tacotron2-DDC"
    # model_name = "tts_models/en/sam/tacotron-DDC"
    return coqui_model_from_name(model_name)


def coqui_model_from_name(model_name: str) -> CoquiModel:
    # this takes a considerable amount of time to load, so load it
    # only when coqui is actually used
    import TTS
    from TTS.utils.manage import ModelManager

    models_json = Path(TTS.__file__).parent / ".models.json"
    manager = ModelManager(models_json)
    manager.list_models()

    model_path, config_path, model_item = manager.download_model(model_name)
    vocoder_name = model_item["default_vocoder"]
    vocoder_path, vocoder_config_path, _ = manager.download_model(vocoder_name)

    # Synthesizer is not thread safe, so we need to create multiple
    synthesizer_args = {
        "tts_checkpoint": model_path,
        "tts_config_path": config_path,
        "vocoder_checkpoint": vocoder_path,
        "vocoder_config": vocoder_config_path,
    }

    return CoquiModel(synthesizer_args)


# EOF #
