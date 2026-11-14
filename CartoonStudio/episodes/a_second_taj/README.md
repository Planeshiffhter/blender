# A Second Taj

A 20-second English conversation between Tara and Maya in the Taj Mahal gardens. Tara finds a second monument in the reflecting pool. Maya gets out her phone.

## Open the scene

Open **A_Second_Taj.blend** in the standard desktop release of Blender 4.3.2. Press **Numpad 0** to enter camera view if needed and **Space** to play. The scene contains eight camera shots, two animated characters, a moving water surface and a packed stereo soundtrack. The 24 fps timeline runs from frame 1 through 480. The supplied MP4 presents character motion on twos, with English captions and a final camera-shutter effect.

The two characters and the original Taj Mahal are from the three Tripo archives supplied with the project. Maya’s upper-body rig, the two speech shapes, the reflecting pool, the phone, the camera moves and the finished soundtrack were created for this scene.

## Change the dialogue

Use Python 3.12. The scripts use ONNX Runtime on the CPU. On the first synthesis run, the script downloads the pinned ONNX model and voice bank into **models** and verifies both SHA-256 checksums. Python packages are installed when you first set up the virtual environment.

From this folder in Windows PowerShell, run the following commands.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe rebuild.py --blender "C:\Program Files\Blender Foundation\Blender 4.3\blender.exe"
```

On Linux or macOS, use these commands. If Blender is outside your PATH, pass its executable using the same `--blender` option.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python rebuild.py
```

Edit **dialogue.json** before running the final command. The six turns alternate between Tara and Maya. Tara uses **af_heart** in American English. Maya uses **bf_emma** in British English. Each line has a speed control. The script fits the reaction pauses to the 20-second timeline and reports lines that exceed the available time.

**rebuild.py** writes **audio/Conversation.wav**, **audio/timing.json**, and **A_Second_Taj_Remix.blend**. The new scene contains the updated audio and speech shapes. The gestures and shot cuts follow the original story. Adjust them in Blender when the action changes. To regenerate audio alone, run **make_audio.py**. To repack existing audio without synthesizing the voices, use **rebuild.py --reuse-audio**.

Use **Render → Render Animation** in Blender to make an H.264 movie from the camera timeline with its packed audio. To reproduce the captions, opening title and shutter flash, run the following command with an FFmpeg build that includes libass and libx264. The original English captions are also supplied as **English.srt**.

```bash
python finish_video.py path/to/blender-export.mp4 A_Second_Taj_Finished.mp4
```

## Review the original export

[Download the 20-second film](final/A_Second_Taj.mp4?raw=true). The **Check A Second Taj** workflow checks the published picture and its six voice cues against the original WAV, mouth timing and captions. Download **original-taj-camera-review** from the workflow run to see a frame with an active mouth from each line. Read the frames left to right, using the speaker names and timestamps in **speakers.txt** to review the camera choices. To run the same export check locally, install FFmpeg and run `python verify_export.py review` from this directory.

The **Compare Blender cameras with the finished film** job opens the editable scene in Blender 4.3.2, checks its packed soundtrack, and renders one small preview per camera cut. Download **original-taj-blender-cameras** and open **camera-comparison.jpg**. Each row pairs the camera render with the same timestamp from the published film and names the active speaker or pause. Use it to judge the silhouettes, background detail, lighting and eyelines. The source column uses 40% resolution and includes the scene before titles and captions.

## Asset credits

The source models retain their original terms. Tripo source pages are listed in the order Tara, Maya, garden.

- https://studio.tripo3d.ai/3d-model/0dd9240e-82d2-4885-b44b-657bba4c9b3a
- https://studio.tripo3d.ai/3d-model/0a9ccba6-9c5a-4e66-a61c-98aaec95d257
- https://studio.tripo3d.ai/3d-model/e3bca070-3984-4aa3-8d54-1192acc9da1e

Kokoro model weights and voice bank are from the v1.0 ONNX release. The Apache 2.0 license is under **licenses**. The scripts verify the downloaded model and voice bank by SHA-256 if either file needs to be restored.

- https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0
- https://huggingface.co/hexgrad/Kokoro-82M
