# Existing rigged character investigation

## Current objective and status

The user's latest direction is to investigate and use an existing rigged asset,
with [Rain v3](https://studio.blender.org/characters/rain/v3/) preferred and
[Game Human Rig](https://github.com/ostef/Game-Human-Rig) as a fallback. This
supersedes the earlier plan to present a newly procedural character as the final
Character 01. Earlier procedural work and previews are not Rain and are not proof
that this new objective is complete.

No Rain-based `C01_MASTER.blend` has been completed or validated. The canonical
`assets/characters/C01/C01_MASTER.blend` is intentionally absent. The earlier
procedural candidate is archived under `prototypes/C01_procedural/`, with its
original relative library layout preserved. Fallback inspection or body-animation
proofs do not establish a finished, clothed cartoon character with facial controls.

## Rain access

The attempted HTTPS request to `studio.blender.org` was blocked by the cloud
egress proxy: curl reported `CONNECT tunnel failed, response 403`. This is a
proxy CONNECT denial, not evidence of a Blender Studio account failure, subscription
requirement, or an invalid download credential. The actual Rain page, download,
appearance, included files, and license were not inspected successfully. No claim
is made about their contents or access requirements.

`studio.blender.org` was added to the saved environment configuration draft.
A draft save does not apply the setting to the running machine or publish an
environment. Review and save the domain addition in environment settings, publish
the environment, then retry the request using the supported proxy route. Network
policy must actually be applied and the request must succeed before access can be
claimed. No proxy bypass, disabled TLS verification, or alternate unverified copy
is part of this workflow.

If supplying the asset directly is easier, download Rain through its legitimate
source using your own browser and attach the original ZIP to this chat. Include
the original `.blend`, all referenced textures or other dependencies, and the
included license and attribution files. If providing an unpacked `.blend`, also
attach its dependencies and license, or provide a ZIP containing them. Do not
send account credentials, session cookies, access tokens, or browser profiles.

Once the asset is available, inspect its license and file inventory, open it with
script execution disabled initially, identify the character collection and rig,
test actual deformation and facial controls, then build and render a separate
linked test scene. Those steps remain outstanding for Rain.

## Fallback source and preservation

| Item | Verified value |
| --- | --- |
| Repository | `https://github.com/ostef/Game-Human-Rig` |
| Inspected commit | `483f7ee62c79849f62b60770d4743e37ce48af09` |
| Commit date | 14 February 2024 |
| Original file | `Game_Human_Rig.blend` |
| Size | 8,369,132 bytes; a real Git blob, not a Git LFS pointer |
| File header | Blender 3.6 |
| Read-only compatibility check | Opened in installed Blender 4.3.2 with `--disable-autoexec` and `use_scripts=False` |
| Preserved copy | `assets/characters/C01/source/Game-Human-Rig.original.blend` |
| SHA-256 | `4ffb5cf29e8e89f9a948d937b69512bba49849fdfa6a44825912daf396f2af45` |

The original file was copied without modifying or resaving its Blender data.
The cache source and preserved copy had the same SHA-256 before and after copying.
The upstream source blob is at
[`Game_Human_Rig.blend`](https://github.com/ostef/Game-Human-Rig/blob/483f7ee62c79849f62b60770d4743e37ce48af09/Game_Human_Rig.blend).

The repository's [LICENSE](https://github.com/ostef/Game-Human-Rig/blob/483f7ee62c79849f62b60770d4743e37ce48af09/LICENSE)
is MIT, copyright © 2024 Stefan. Its complete notice is preserved verbatim in
`assets/characters/C01/source/Game-Human-Rig.LICENSE`. The license permits use,
modification and redistribution subject to retaining its copyright and permission
notice in copies or substantial portions. The
[README](https://github.com/ostef/Game-Human-Rig/blob/483f7ee62c79849f62b60770d4743e37ce48af09/README.md)
identifies the meshes as modifications of the male and female Blender demo
basemeshes and calls them prototyping rigged meshes. No separate upstream
basemesh license or source archive is bundled in this repository; that provenance
note is retained rather than replaced by an independent ownership claim.

## Fallback rig and assets

- `Female_Prototype` contains 11,664 vertices and 10,764 polygons.
- Its Armature modifier targets the 53-bone `DEF-Rig`; the separate `CTRL-Rig`
  contains 128 bones, limb IK/FK controls, finger controls and constraints.
- The file also contains a male prototype. It has not been promoted to a second
  production character.
- Supplied Actions are `Human_Breathing_Additive` (frames 1–200),
  `Human_Idle_Pose` (0–1), `Human_Jog` (1–26), `Human_Run` (1–20),
  `Human_Sprint` (1–18), `Human_Walk` (1–34), `Sample_Run_Pose` (0–1), and
  `Sample_Run_Pose_Inversed` (1).
- No external texture images, linked libraries or embedded text scripts were found.
  The character has a basic Principled material rather than a finished textured look.
- No add-on was installed or executed to inspect it. The repository explicitly says
  its rig was not made with Rigify.

Read-only `Human_Walk` evaluation confirmed real mesh deformation: all 11,664
female vertices moved more than 0.001 m at the sampled frames 9, 18, and 26
relative to the baseline. Maximum measured displacements were approximately
0.273 m, 0.752 m, and 0.574 m respectively. This validates animated deformation
of the existing body rig at those samples; it does not certify every pose or
foot-contact quality.

Four invalid stale drivers were found, referring to missing `MCH-Foot_Lift.L`,
`MCH-Heel_Lift.L`, `DEF_TG-Big_Toe.L` paths and an obsolete `CTRL-Armature`
target. They remain unchanged in the preserved original. These should be
investigated in a separately saved working copy before production use.

The diagnostic working copy now removes only those four orphan driver curves;
the original remains byte-identical. Four CPU views, a two-second 360-degree
turntable and a five-second walk are saved under
`proofs/asset_candidates/Game-Human-Rig/`. FFprobe confirms H.264, 256 × 384,
24 fps, 48 and 120 frames respectively. `diagnostics.json` records the measured
deformation and source hash; `inventory.json` records the asset inventory.

Visible bands in the rendered body correspond to the source's segmented geometry:
54 disconnected mesh components and 1,802 boundary/nonmanifold edges were measured.
Freestyle was disabled; removing custom split normals in a separate unsaved test
did not remove the bands. The saved working copy preserves the original mesh.
This is another reason to reject it as a finished high-quality C01 base.

## Gaps against the requested Character 01

The author's showcase and the inspected data describe a bald, monochrome
prototype mannequin. It lacks the requested shoulder-length wavy brown hair,
light-blue T-shirt, jeans, shoes, finished materials and reference-style design.
The female mesh has no shape keys, and the rig has no jaw, eye, lip or brow bones.
Blinking, eye direction, expressions, speech mouth shapes and lip-sync therefore
remain unimplemented. No required `IDLE`, `WALK`, `WAVE`, `POINT`, `TALK`,
`SURPRISED`, or `BLINK` production Action set is claimed merely because unrelated
sample actions exist.

The existing body rig is useful as an animation and retargeting starting point.
It is not a substitute for the desired finished female cartoon character.
Any fallback proof renders should be identified as fallback evaluation and kept
outside the final C01 deliverable namespace.

## Environment evidence

Blender 4.3.2 and FFmpeg/FFprobe 7.1.5 are available in this CPU-only workflow.
The persistent test below passed with exit status 0, creating a real mesh scene,
saving and reopening its `.blend`, and CPU-rendering a nonblank 128 × 128 PNG:

```sh
cd CartoonStudio
blender --background --factory-startup --python-exit-code 1 --python pipeline/smoke_c01_environment.py
```

The Debian Blender build lacks OpenImageDenoise, so the test explicitly disables
Cycles denoising while retaining CPU rendering. See `C01_ENVIRONMENT.md` for the
audit and correction. No Blender MCP capability is available in the active tool
list; no verified installation source was supplied for the named “Blender Lab MCP
Server”. MCP installation and communication have not been validated. Direct
Blender CLI and `bpy` are the working automation path. No AWS resources were
provisioned.
