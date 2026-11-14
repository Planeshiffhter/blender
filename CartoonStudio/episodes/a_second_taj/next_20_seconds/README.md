# A Second Taj — Next 20 Seconds (Episode 2: Palace in the Sky)

This is the next **20 seconds of AUDIO** after the existing `A_Second_Taj.mp4`, continuing Tara and Maya's conversation just after Maya takes their picture. It deliberately does not replace Episode 1 or claim to contain an animated MP4.

## Same voices and audio style

- Tara: Kokoro ONNX `af_heart`, US English, speed 0.95
- Maya: Kokoro ONNX `bf_emma`, UK English, speed 0.94
- Shares the parent episode's exact `make_audio.py` implementation, verified Kokoro model/voice weights, stereo panning, outdoor ambience, shutter sound and timing format.
- Deliverables generated: `audio/Conversation.wav` (20.000 sec, stereo, 24 kHz/16-bit PCM), `audio/timing.json` (mouth-curve animation data for Blender at 24 fps), and `English.srt`.

## Download

After the generation action completes, the WAV is committed to this folder: [audio/Conversation.wav](audio/Conversation.wav). A downloadable GitHub Actions artifact is also provided.

## Regenerate using Python 3.12

From the **parent** folder `CartoonStudio/episodes/a_second_taj`, run:

```bash
python -m pip install -r requirements.txt
python next_20_seconds/make_audio.py
python next_20_seconds/verify_audio.py
```

The generator downloads the original Kokoro ONNX model and voice bank to `models/` on the first run, checking the hashes from the original source. You can adjust `next_20_seconds/dialogue.json` for a new scene. Keep six alternating short lines so the original timing logic fits within exactly 20 seconds.

The workflow `.github/workflows/next-20-seconds.yml` generates the audio on GitHub Actions and commits the generated media, timing and captions. It can be manually rerun with the Actions tab.
