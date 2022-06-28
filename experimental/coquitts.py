from concurrent.futures import ThreadPoolExecutor
import numpy as np
import torch

from TTS.utils.manage import ModelManager
from TTS.tts.utils.synthesis import synthesis
from TTS.config import load_config
from TTS.tts.models import setup_model as setup_tts_model
from TTS.utils.audio import AudioProcessor
from TTS.vocoder.models import setup_model as setup_vocoder_model

# 4 seems to be the fastest
# torch.set_num_threads(6)

model_json_path = "/nix/store/ys9q1vxqhw5kvixb8fwy93c6lkbi2025-tts-0.6.1/lib/python3.9/site-packages/TTS/.models.json"
manager = ModelManager(model_json_path)
manager.list_models()
tts_name = "tts_models/en/ljspeech/tacotron2-DDC"
# tts_name = "tts_models/multilingual/multi-dataset/your_tts"  # doesn't # work
# tts_name = "tts_models/en/ljspeech/speedy-speech"
# tts_name = "tts_models/en/ljspeech/glow-tts"
tts_path, tts_config_path, tts_item = manager.download_model(tts_name)

vocoder_name = tts_item["default_vocoder"]
vocoder_path, vocoder_config_path, _ = manager.download_model(vocoder_name)

tts_config = load_config(tts_config_path)
tts_model = setup_tts_model(config=tts_config)

# if not self.encoder_checkpoint:
#     self._set_speaker_encoder_paths_from_tts_config()

encoder_checkpoint = None
if hasattr(tts_config, "model_args") and \
   hasattr(tts_config.model_args, "speaker_encoder_config_path"):
    encoder_checkpoint = tts_config.model_args.speaker_encoder_model_path
    encoder_config = tts_config.model_args.speaker_encoder_config_path

tts_model.load_checkpoint(tts_config, tts_path, eval=True)

if encoder_checkpoint and \
   hasattr(tts_model, "speaker_manager"):
    tts_model.speaker_manager.init_encoder(encoder_checkpoint, encoder_config, use_cuda=False)

vocoder_config = load_config(vocoder_config_path)
vocoder_ap = AudioProcessor(verbose=False, **vocoder_config.audio)
vocoder_model = setup_vocoder_model(vocoder_config)
vocoder_model.load_checkpoint(vocoder_config, vocoder_path, eval=True)

# print(tts_model.speaker_manager.ids)


def generate(model, text: str):
    outputs = synthesis(model=model, text=text, CONFIG=tts_config, use_cuda=False)
    return outputs


texts = [
    "This is a test of a text to speech system. ",
    "Multithreading is hard, so we test it. ",
    "Another line of text send to the system. ",
    "Yet more text for the system to proccess. ",
    "This is the fifths like of text. ",
    "And now it comes to the last one. ",
]

futures = []
with ThreadPoolExecutor(8) as executor:
    for text in texts:
        future = executor.submit(generate, tts_model, text)
        futures.append(future)

for idx, future in enumerate(futures):
    outputs = future.result()

    mel_postnet_spec = outputs["outputs"]["model_outputs"][0].detach().cpu().numpy()
    mel_postnet_spec = tts_model.ap.denormalize(mel_postnet_spec.T).T
    vocoder_input = vocoder_ap.normalize(mel_postnet_spec.T)
    scale_factor = [1, vocoder_config["audio"]["sample_rate"] / tts_model.ap.sample_rate]

    # if scale_factor[1] != 1:
    #     vocoder_input = interpolate_vocoder_input(scale_factor, vocoder_input)
    # else:
    vocoder_input = torch.tensor(vocoder_input).unsqueeze(0)
    waveform = vocoder_model.inference(vocoder_input.to("cpu"))

    waveform = vocoder_model.inference(vocoder_input.to("cpu"))
    wav = np.array(waveform)
    tts_model.ap.save_wav(wav, f"/tmp/foo{idx:02d}.wav", tts_config.audio["sample_rate"])

# EOF #
