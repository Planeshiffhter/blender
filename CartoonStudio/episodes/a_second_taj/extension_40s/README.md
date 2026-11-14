# A Second Taj — 40-second extended cut

This **40-second MP4** keeps the original 20-second A Second Taj video first and **adds** the next 20 seconds, voiced by Tara (\`af_heart\`) and the improved Maya (\`af_bella\`).

## Output

**\`../final/A_Second_Taj_40s.mp4\`** — one playable MP4 containing both episodes, with English burned-in dialogue captions and AAC audio. The original \`A_Second_Taj.mp4\` stays unchanged.

**\`English_40s.srt\`** — combined subtitles for the full 40 seconds.

**Visual limitation:** The added second half is a new edit of existing animated shots, with a different shot order and the updated conversation. It does **not** create brand-new Blender animation or precise lip synchronization for the second 20 seconds. The lower third hides old captions under the newer captions. The source \`.blend\` scene is retained so a future animator can render unique shots with the supplied \`next_20_seconds/audio/timing.json\` mouth-animation data.

## Regenerate

Requirements: Python 3.10+ and FFmpeg built with libx264 and libass support.

From \`CartoonStudio/episodes/a_second_taj\`:

\`\`\`bash
python extension_40s/build_40s.py
\`\`\`

This reads:

- \`final/A_Second_Taj.mp4\` (original complete 20-second MP4)
- \`next_20_seconds/audio/Conversation.wav\` (upgraded voice, 20 seconds)
- \`next_20_seconds/audio/timing.json\` (new dialogue times)
- \`English.srt\` (original first 20-second transcript)

It assembles a second 20-second re-edit using those same 3D cartoon shots with new captions and the improved dialogue, then joins the segments without re-encoding the original first half.

GitHub Actions runs automatically whenever the build script or the new WAV changes. The result is committed into \`final/\` and uploaded as \`A-Second-Taj-40s-Extended-Video\` for easy download.
