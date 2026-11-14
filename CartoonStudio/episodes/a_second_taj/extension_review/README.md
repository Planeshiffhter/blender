# Second 20 seconds: genuine 3D continuation (review only)

This is a draft proposal for a **new animated 20–40 second segment** of A Second Taj. Do not publish an MP4 on main until it is visually reviewed. The approved original video remains unchanged.

## Comparison with the rejected edit

| Check | Good original 0–20s | Rejected 20–40s | Proposed method |
| --- | --- | --- | --- |
| Character movement | Created in the original Blender scene | Six recycled slices of the finished video | Extend the same editable Blender scene |
| Camera | Eight purpose-built camera shots | Arbitrary reused footage | Six new Blender camera cuts following the speaker |
| Voices and lips | Original audio-driven facial motion | Old facial motion under new WAV | Key new facial poses from Episode 2 mouth arrays |
| Subtitles | Authored, embedded captions | Old captions covered with dark overlay | New, time-shifted subtitles over fresh footage |
| Acting | Story-matched reactions | Repeating previous reactions | Must be hand-reviewed and refined before release |

The structural mismatch can be established from the source code. No complete visual playback has been performed in this chat, and the new source has not yet been rendered or approved.

## Source code on this draft PR

- extend_blender.py prepares an editable 960-frame Blender scene, preserving first 480 frames.
- verify_sources.py checks the improved second audio is exactly 20 seconds, with six alternating dialogue lines and 480 facial-animation samples for each speaker.
- Existing original video and Episode 2 WAV remain on main. The old bad 40-second MP4 was reverted and its history archived separately.

Run from CartoonStudio/episodes/a_second_taj:

~~~sh
python3 extension_review/verify_sources.py
blender --background A_Second_Taj.blend --python extension_review/extend_blender.py
~~~

The Blender command creates the editable scene (not the finished MP4). The next step requires a proper Blender render of frames 481–960, an actual review of six camera angles and gestures, and joining with the original 20-second film. Check that the first half is pixel-identical if stream-copied, that the new dialogue starts at 20.0s, and that the whole film contains 40s of correctly aligned audio/video.

## Audio-to-camera timing on the full timeline

| Video time | Voice | Camera goal |
| --- | --- | --- |
| 20.00–23.68 | Tara | Water reflection / Tara's reaction to photo |
| 23.68–26.92 | Maya | Maya checking her phone |
| 26.92–30.36 | Tara | Tara imagining the upside-down world |
| 30.36–33.72 | Maya | Maya answering about a ladder |
| 33.72–36.60 | Tara | Tara imagining a flying bicycle |
| 36.60–40.00 | Maya | Maya raises phone for another picture |

A passing automatic audio check alone **cannot** prove good camera framing, acting, audio lip-sync or overall visual quality. Keep the PR in draft until a human has watched the rendered output and approved it.
