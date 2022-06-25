import numpy as np
import TTS
from TTS.utils.manage import ModelManager
from TTS.utils.synthesizer import Synthesizer
from TTS.tts.utils.synthesis import synthesis
from TTS.config import load_config
from TTS.tts.models import setup_model as setup_tts_model
from TTS.utils.audio import AudioProcessor
from TTS.vocoder.models import setup_model as setup_vocoder_model
import torch

manager = ModelManager("/nix/store/ys9q1vxqhw5kvixb8fwy93c6lkbi2025-tts-0.6.1/lib/python3.9/site-packages/TTS/.models.json")

tts_name = "tts_models/en/ljspeech/tacotron2-DDC"
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

outputs = synthesis(model=tts_model, text="This is a test of a text to speech system.", CONFIG=tts_config, use_cuda=False)

mel_postnet_spec = outputs["outputs"]["model_outputs"][0].detach().cpu().numpy()
mel_postnet_spec = tts_model.ap.denormalize(mel_postnet_spec.T).T
vocoder_input = vocoder_ap.normalize(mel_postnet_spec.T)
scale_factor = [ 1, vocoder_config["audio"]["sample_rate"] / tts_model.ap.sample_rate ]
if scale_factor[1] != 1:
    vocoder_input = interpolate_vocoder_input(scale_factor, vocoder_input)
else:
    vocoder_input = torch.tensor(vocoder_input).unsqueeze(0)
    waveform = vocoder_model.inference(vocoder_input.to("cpu"))

waveform = vocoder_model.inference(vocoder_input.to("cpu"))
wav = np.array(waveform)
tts_model.ap.save_wav(wav, "/tmp/foo.wav", tts_config.audio["sample_rate"])

# EOF #
