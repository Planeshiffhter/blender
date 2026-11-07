# CartoonStudio

Character 01 is being investigated using an existing rigged Blender asset.
**The preferred Rain asset has not been obtained, and no approved Character 01
master is currently available.** Characters 02–04 remain scaffold placeholders.

## Current status

- Blender 4.3.2 and FFmpeg 7.1.5 are installed. Actual CPU create/save/reopen/render
  tests pass; no GPU or AWS resources are needed for the current checks.
- The environment proxy currently blocks `studio.blender.org`. The domain was
  added to the environment configuration draft; review/save and publication are
  required to apply it. This denial does not show whether Blender Studio requires
  a login or paid access.
- The GitHub fallback opens and its body rig animates. It has no hair, clothes,
  facial bones, or expression shape keys; it is a prototype base, not a finished
  shopping-cartoon heroine. Diagnostic outputs are labelled as candidate reviews.
- Earlier procedural C01 work is preserved under `prototypes/C01_procedural/`.
  It is unapproved, unrelated to Rain, and is not the current deliverable.

Read [the asset investigation](docs/EXISTING_ASSET_INVESTIGATION.md),
[the reference change plan](docs/C01_REFERENCE_CHANGE_PLAN.md), and
[the environment audit](docs/C01_ENVIRONMENT.md).

## Rain intake

After enabling the required network destination, retry the supplied official
[Rain v3 page](https://studio.blender.org/characters/rain/v3/). Follow its actual
license and download process; no authentication bypass is permitted. Alternatively,
download the original asset normally in your own browser and attach its ZIP or
`.blend`, all textures/dependencies, and included license to the chat. Do not send
passwords, login cookies, or access tokens.

The original will be preserved under `assets/characters/C01/source/`; edits must
use a separate working copy. Only after the asset, rig and modifications have been
verified should the resulting approved-base character be saved as
`assets/characters/C01/C01_MASTER.blend`. That path is currently intentionally
absent. `config/character_01.json` records the blocked status and intended target.

## Verified tools and commands

Run from `CartoonStudio/` in the existing checkout. Do not create an extra branch
or worktree for this task. Changes are intended for the repository's `main` branch.

```sh
bash pipeline/setup_c01.sh --check
blender --background --factory-startup --threads 5 --python-exit-code 1 --python pipeline/smoke_c01_environment.py
python3 pipeline/validate_assets.py
```

The last check validates the original four scaffold placeholders only; it does
not certify a Rain-based Character 01. Blender's direct `bpy` workflow is available;
no Blender MCP tool is installed or verified. The installed distribution build
lacks OpenImageDenoise, so CPU smoke/preview scripts disable that denoiser.

Optional fresh Debian/Ubuntu installation through signed distro repositories:
`bash pipeline/setup_c01.sh --install`. Xvfb is optional (`--with-xvfb`) and is not
needed by the tested headless workflow. Installation was unnecessary in this
instance; consult the environment audit for tested versions and observed failures.

## Candidate review

`assets/characters/C01/source/Game-Human-Rig.original.blend` is a byte-identical
copy of the inspected upstream fallback. Its MIT notice is preserved beside it.
`Game-Human-Rig.working.blend` and `proofs/asset_candidates/Game-Human-Rig/` are
candidate diagnostics, not final C01. The review script documents changes made
only to its working copy. Do not present those views as Rain or as a finished C01.

Reproduce the inspected fallback inventory and diagnostic outputs:

```sh
blender --background --disable-autoexec --python-exit-code 1 --python pipeline/inspect_existing_asset.py -- --asset assets/characters/C01/source/Game-Human-Rig.original.blend --report proofs/asset_candidates/Game-Human-Rig/inventory.json
blender --background --disable-autoexec --python-exit-code 1 --python pipeline/review_fallback_asset.py -- --mode all --force
```

The second command explicitly replaces the diagnostic working copy and proofs;
use another filename for manual production edits.

Reusable project assets belong in `assets/`, episode work in `episodes/`, and
review evidence in `proofs/`. Intermediate frames and Python caches are ignored.
The next character remains C01; do not develop C02, C03 or C04 before approval.
