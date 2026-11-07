#!/usr/bin/env bash
# Check the headless Character 01 toolchain; install signed distro packages on request.
set -euo pipefail

install_packages=false
with_xvfb=false
for argument in "$@"; do
    case "$argument" in
        --install) install_packages=true ;;
        --with-xvfb) with_xvfb=true ;;
        --check) ;;
        *) printf 'Usage: bash pipeline/setup_c01.sh [--check] [--install] [--with-xvfb]\n' >&2; exit 2 ;;
    esac
done

packages=(blender ffmpeg python3)
commands=(blender ffmpeg ffprobe python3)
if "$with_xvfb"; then
    packages+=(xvfb xauth)
    commands+=(Xvfb xvfb-run xauth)
fi

if "$install_packages"; then
    if [[ "$(id -u)" == 0 ]]; then
        privilege=()
    elif command -v sudo >/dev/null 2>&1; then
        privilege=(sudo -n)
    else
        printf 'Installation requires a root shell or noninteractive sudo. Checks need no elevated access.\n' >&2
        exit 1
    fi
    # Preserve configured repositories, proxy, CA trust, and normal package signatures.
    "${privilege[@]}" apt-get update
    "${privilege[@]}" env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "${packages[@]}"
fi

missing=false
for executable in "${commands[@]}"; do
    if ! command -v "$executable" >/dev/null 2>&1; then
        printf 'Missing command: %s\n' "$executable" >&2
        missing=true
    fi
done
if "$missing"; then
    printf 'Install with: bash pipeline/setup_c01.sh --install%s\n' "$(if "$with_xvfb"; then printf ' --with-xvfb'; fi)" >&2
    exit 1
fi

blender --version
python3 --version
ffmpeg -version
ffprobe -version
printf '\nHeadless toolchain commands are available. Scene/rig/render validation is a separate step.\n'
