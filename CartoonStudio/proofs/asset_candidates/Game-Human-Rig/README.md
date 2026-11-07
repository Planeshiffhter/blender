# Game-Human-Rig diagnostic candidate — not final C01

These are genuine Blender CPU renders of the downloaded `Female_Prototype`
mesh, not reference artwork and not the requested finished cartoon character.
The source has a reusable body rig and existing animation actions, but no facial
rig, expression shape keys, hair, clothing, or the approved C01 design. Visible
surface breaks in the segmented mannequin remain. It is a fallback candidate for
inspection, not a production-quality character or an approved substitute for Rain.
The source mesh has 54 disconnected components and 1,802 boundary/nonmanifold
edges. Freestyle is disabled, and a separate diagnostic render clearing custom
split normals retained the same bands: the breaks belong to the source geometry.

## Evidence

- `front.png`, `side.png`, `back.png`, `three_quarter.png`: real rest-pose renders,
  384 × 512, Cycles CPU, 12 samples.
- `turntable.mp4`: a complete 360-degree camera orbit around the actual 3D mesh,
  48 rendered frames, 256 × 384, 24 fps, 2 seconds.
- `walk_5s.mp4`: the actual `Human_Walk` action on `CTRL-Rig` deforms the female
  mesh; source frames 1–33 repeat in place for 120 rendered frames, 24 fps,
  256 × 384, 5 seconds. It does not demonstrate facial animation or C01 gestures.
- `diagnostics.json`: successful FFprobe decoded frame counts, durations, driver
  changes, source hash, mesh statistics, and measured vertex deformation. At source
  frame 9, all 11,664 vertices moved over 0.001 m compared with frame 1, with a
  maximum displacement of about 0.273 m.
- `inventory.json`: independent source asset inspection.

Video encoding is H.264 with yuv420p. Preview frames used Cycles CPU, 8 samples,
3 threads, and no denoising because this Blender build lacks OpenImageDenoise.
Intermediate PNG sequences live in ignored `.cache/asset_candidates/Game-Human-Rig/`.
The saved evidence was inspected visually, including the animated mesh at frame 18.

## Source preservation and working copy

The immutable downloaded source is
`assets/characters/C01/source/Game-Human-Rig.original.blend` with SHA256:

```text
4ffb5cf29e8e89f9a948d937b69512bba49849fdfa6a44825912daf396f2af45
```

The separate `Game-Human-Rig.working.blend` hides the male mannequin and render
widgets, includes diagnostic lights/camera, and has `Human_Walk` active in pose
mode. Four orphan driver curves targeting already absent bones were removed in
that working copy only; the exact paths are recorded in `diagnostics.json`.
All remaining drivers validated during the recorded run. No missing bone was
invented and the original file's hash remained unchanged. Downloaded scripts and
text blocks were not executed. Upstream licensing is retained alongside the source.

## Reproduce

From `CartoonStudio/`, using Blender 4.3.2 and FFmpeg/FFprobe:

```sh
blender --background --disable-autoexec --python-exit-code 1 \
  --python pipeline/review_fallback_asset.py -- --mode all --force
```

`--force` deliberately replaces the existing working copy and selected previews.
Preserve any manual working-copy edits before using it. First creation can omit
`--force`; reruns without it stop before changing files. Use `--mode all` to
recreate the complete evidence. Single-mode reruns write their own
`diagnostics.<mode>.json` and preserve the complete-run report.
