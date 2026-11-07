# CartoonStudio instructions

- Work in the existing checkout; do not create a worktree unless requested.
- Read `README.md`, `config/characters.json`, and `config/render.json` before production work.
- Keep character IDs stable. `config/character_01.json` records the pending existing-asset C01 workflow. The older `C01_maya` and C02–C04 scaffold files are geometric placeholders. The canonical C01 master is not yet available.
- Preserve existing `.blend` masters. Do not regenerate or overwrite them without an explicit request.
- Keep reusable assets in `assets/` and episode-specific work in `episodes/<episode_id>/`.
- Save rendered shots to the episode's `renders/` directory and assembled output to `final/`.
- Validate assets with `python3 pipeline/validate_assets.py` from this directory.
- Preserve upstream originals and licenses under `assets/characters/C01/source/`; use separate working copies. Do not bypass site authentication or network access controls.
- Earlier procedural experiments are archived under `prototypes/C01_procedural/`. Do not confuse their validation or previews with an approved Rain-based character.
- Only develop C01 until the user approves its previews. Do not upgrade or generate C02, C03, or C04 during this review.
- Keep diagnostic candidate renders in `proofs/asset_candidates/`; intermediate frame sequences belong in the ignored `.cache/` directory. Only approved-base C01 renders belong in `proofs/C01/`.
- Do not commit credentials, Blender backup files, caches, or temporary renders.
