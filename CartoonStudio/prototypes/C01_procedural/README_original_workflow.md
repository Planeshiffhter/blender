> Historical workflow, archived before the switch to existing rigged assets. Use the active CartoonStudio README for current status.

# CartoonStudio

Blender cartoon production workspace. **Character 01 / Maya is the only current
character development task.** Its editable master and genuine CPU-rendered proofs
are for artistic review; the supplied reference is a design target, not a claim of
matching production quality. C02–C04 remain the earlier scaffold placeholders.

## Character 01 deliverables

- Master: `assets/characters/C01/C01_MASTER.blend`
- Configuration: `config/character_01.json`
- Linked animation shot: `episodes/EP001/shots/C01_ANIMATION_TEST.blend`
- Independent linked reuse shot: `episodes/EP001/shots/C01_LINK_TEST.blend`
- Four views, facial expressions and MP4 proofs: `proofs/C01/`
- Validation and known gaps: `docs/C01_REVIEW.md`, `proofs/C01/validation.json`
- Environment audit, tested versions and installation: `docs/C01_ENVIRONMENT.md`
- Supplied reference provenance: `reference/SOURCES.md`

## Reproduce and validate

Run commands from `CartoonStudio/` in the existing checkout; no additional branch
or worktree is needed. Blender 4.3.2 and FFmpeg 7.1.5 were used. No Python packages,
GPU, AWS resources, MCP connection, or graphical desktop are required.

```sh
bash pipeline/setup_c01.sh --check
blender --background --factory-startup --threads 5 --python-exit-code 1 --python pipeline/smoke_c01_environment.py
blender --background --factory-startup --threads 5 --python-exit-code 1 --python pipeline/validate_c01.py
```

For a fresh machine, `bash pipeline/setup_c01.sh --install` uses configured signed
Debian/Ubuntu repositories. That optional installation path was not needed in this
cloud instance. See the environment document before installing graphical extras.

To explicitly rebuild the master and regenerate all episode/proof outputs:

```sh
blender --background --factory-startup --threads 5 --python-exit-code 1 --python pipeline/build_c01.py -- --force
blender --background --factory-startup --threads 5 --python-exit-code 1 --python pipeline/preview_c01.py -- --mode all
blender --background --factory-startup --threads 5 --python-exit-code 1 --python pipeline/validate_c01.py
```

`build_c01.py` refuses to replace an existing master without `--force`. Rebuilding
discards manual changes to that master. The preview command replaces its named
test shots and proof outputs. Use a different shot filename for production edits.
The CPU smoke and shared stage disable denoising because this distribution build
does not include OpenImageDenoise. Intermediate frames live in ignored `.cache/`.

To render a subset, choose `--mode stills`, `shots`, `turntable`, `animation`, or
`reuse`. MP4s are encoded by FFmpeg and checked with FFprobe; adjacent JSON records
store measured codec, dimensions, frame count, frame rate, and duration.

## Rig and episode workflow

Open the master in Blender and select `C01_RIG`. Named FK pose bones control the
spine, limbs, hands, fingers, head, and eyes. Custom properties control `Blink`,
`Smile`, `MouthOpen`, `Surprise`, `Sad`, `Angry`, `Viseme_AA`, `Viseme_EE`,
`Viseme_OO`, `LookX`, and `LookY`. Actions include `IDLE`, `WALK`, `WAVE`, `POINT`,
`TALK`, `SURPRISED`, `BLINK`, and an additional `SIT` take. The master opens neutral.

The preview script links the `C01_CHARACTER` collection from the master, creates
editable library overrides, and assigns local shot animation. Relative library
paths preserve portability within this workspace. Episode edits do not rebuild or
modify the master. The walk/talk preview uses procedural mouth movement, without
audio or phoneme alignment. This is not an audio lip-sync system.

Keep reusable assets in `assets/`, episode scripts and shot lists in `episodes/`,
and permanent C01 review outputs in `proofs/C01/`. The old unrigged four-character
scaffold generator remains available for historical setup; do not run it to
replace or expand character assets during C01 approval.
