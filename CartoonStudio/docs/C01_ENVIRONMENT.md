# Character 01 cloud environment

## Observed environment

The audit was performed in the existing Codex Cloud checkout on 7 November 2026.
No additional checkout or worktree was created.

| Component | Observed value |
| --- | --- |
| OS | Debian GNU/Linux 13 (trixie), x86_64 |
| CPU | 5 exposed AMD EPYC 9V74 CPU cores |
| RAM | About 33 GiB total; about 32 GiB available at audit |
| Workspace disk | About 60 GiB available at audit |
| Blender | `/usr/bin/blender`, 4.3.2; Debian package `4.3.2+dfsg-2` |
| Python | 3.12.14; Blender scripts use Blender's bundled `bpy` |
| FFmpeg/FFprobe | 7.1.5; Debian package `7:7.1.5-0+deb13u1` |
| Xvfb | Not found on `PATH` during audit |
| GPU | No GPU is required or selected by this workflow; previews use CPU rendering |

The cloud environment reported `running`, with current observations and restricted
network policy enforced. Existing package-manager/GitHub destination presets are
configured; arbitrary Internet destinations are not implicitly permitted. Inherited
proxy and certificate trust settings are retained. `git ls-remote origin HEAD
refs/heads/main` succeeded using the existing Git authentication. No AWS operation
or paid resource was provisioned.

## Toolchain choice and installation

Blender 4.3.2 is already installed and is the compatible stable version used for
this implementation. The brief permits another compatible stable version in place
of Blender 5.2 LTS. Blender 5.2 was not downloaded or installed; availability and
compatibility of that release were not independently established. Keeping the
installed toolchain avoids a speculative version replacement while character APIs
are tested directly.

FFmpeg and FFprobe are already installed. No third-party Python dependency is
required: scene generation, rigging, checks, and animation run through Blender's
`bpy`; standard Python handles orchestration and JSON.

From `CartoonStudio/`, check the tools without changing the machine:

```sh
bash pipeline/setup_c01.sh --check
```

On a fresh Debian or Ubuntu machine with root or noninteractive sudo available,
install using the distribution's configured, signed repositories:

```sh
bash pipeline/setup_c01.sh --install
```

This executes `apt-get update`, followed by a noninteractive installation of
`blender`, `ffmpeg`, and `python3`, and prints the installed versions. Repository
versions can differ on a fresh machine; the tested version is the one recorded
above. No installation command was executed during the audit because the required
tools were present. TLS and APT signature checks are never disabled.

Xvfb is optional for a later graphical workflow. Headless Cycles CPU rendering does
not need an X server. To install it when a graphical tool actually requires it:

```sh
bash pipeline/setup_c01.sh --install --with-xvfb
```

That additionally installs `xvfb` and `xauth`. This optional installation has not
been executed or validated in the current instance.

## MCP compatibility and fallback

No Blender MCP capability is exposed in the active tool list. The supplied brief
names an “official Blender Lab MCP Server” but supplies no project URL, package
identity, version, or verified installation source. No arbitrary third-party
package was substituted under that name. Installation and MCP-to-Blender
communication were therefore **not tested**, rather than reported as successful
or as a diagnosed server failure.

The selected automation path is Blender's directly executable Python API:

```sh
blender --background --factory-startup --python-exit-code 1 --python path/to/script.py
```

`--python-exit-code 1` preserves Python failures as a nonzero Blender exit status.
This path does not need a graphical Blender session, MCP client, remote desktop,
or network listener. Character build, render, and reuse results are reported
separately with the deliverables; tool presence alone is not a readiness claim.

## CPU scene smoke test

From `CartoonStudio/`, the persistent smoke test creates a Suzanne mesh, camera,
and area light; saves and reopens the scene; then renders a 128 × 128 PNG with
Cycles on the CPU. It verifies the reopened mesh, PNG header, dimensions, and
nonuniform rendered pixels. Files are created under a unique temporary `/tmp`
directory and removed when the test exits.

```sh
blender --background --factory-startup --python-exit-code 1 --python pipeline/smoke_c01_environment.py
```

The first CPU test saved and reopened its scene but failed during rendering with
`Failed to denoise, build has no OpenImageDenoise support`. The installed build
does not provide that denoising backend. The supported correction is
`scene.cycles.use_denoising = False`; CPU rendering remains enabled. The persistent
script applies that correction explicitly. This avoids an unavailable optional
postprocessing feature rather than replacing the rendering check.

The exact command above completed successfully with exit status 0 in the current
instance and printed `CPU_CREATE_SAVE_REOPEN_RENDER_PASS: 128x128 PNG;
nonuniform rendered pixels`. This validates scene creation, persistence, reopening,
and a real CPU render after the correction. It does not certify the character rig
or its visual quality.

## Diagnostics and limits

- `apt-cache policy blender ffmpeg xvfb` could read installed package versions but
  emitted `Unable to read /etc/apt/apt.conf.d/80-applied-apt-retries` due to file
  permissions. No package install or repository change was attempted to conceal
  that warning.
- Earlier placeholder generation emitted a read-only Blender extension-cache
  warning under `/home/agent/.config/blender/4.3/extensions`; it still saved and
  reopened all four scaffold masters. It does not establish extension support.
  Keep user cache/config files in a writable location if an extension needs them.
- No AWS credentials were requested, no AWS account was assumed connected, and no
  GPU resources were launched. Any later paid rendering setup requires the user's
  separate authorization.
- Artistic approval, facial deformation quality, and production readiness require
  inspection of the actual Character 01 renders and tests, beyond this audit.
