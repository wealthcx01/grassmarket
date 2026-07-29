#!/usr/bin/env bash
# Compile and render every course diagram (GRS-0225).
#
#   RIVE_CLI=/path/to/rive-cli design/motion/render.sh
#
# For each scene: generate the .riv, validate the binary, render a still, and REFUSE A BLANK FRAME.
# The blank check is the one that matters. `validate` only checks binary structure, and the
# toolchain's own guidance is explicit that a file can validate and still be rejected by the
# runtime or draw nothing at all.
#
# Chromium note: rive-cli launches Chromium without --no-sandbox, which is the right default. On a
# host with unprivileged user namespaces restricted (Ubuntu 23.10+ AppArmor) Chromium aborts with
# "No usable sandbox!". Point RIVE_CHROME at a shim that adds the flag rather than changing the
# tool. See docs/adr/ADR-0049-motion-system.md.
set -euo pipefail

RIVE_CLI="${RIVE_CLI:-rive-cli}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${HERE}/build"

command -v "$RIVE_CLI" >/dev/null 2>&1 || [ -x "$RIVE_CLI" ] || {
  echo "rive-cli not found. Set RIVE_CLI to the built binary." >&2
  exit 1
}

mkdir -p "$OUT"
failures=0

for scene in "${HERE}"/courses/*/*.json; do
  name="$(basename "${scene%.json}")"
  course="$(basename "$(dirname "$scene")")"
  riv="${OUT}/${course}/${name}.riv"
  frames="${OUT}/${course}/${name}"
  mkdir -p "$(dirname "$riv")"

  echo "--- ${course}/${name}"
  "$RIVE_CLI" generate "$scene" -o "$riv" >/dev/null
  "$RIVE_CLI" validate "$riv" >/dev/null

  # Read the artboard size back out of the scene so a diagram is never rendered at the wrong
  # aspect and quietly cropped.
  read -r w h < <(python3 -c "
import json,sys
a=json.load(open('$scene'))['artboard']
print(int(a['width']), int(a['height']))
")
  # An animated scene is sampled across its loop; a static one needs one frame. Reading the
  # duration out of the scene rather than guessing keeps the samples inside the animation.
  spread="$(python3 -c "
import json
a = json.load(open('$scene'))['artboard']
anims = a.get('animations') or []
if not anims:
    print('0')
else:
    d = anims[0].get('duration', 60)
    print(','.join(str(int(d * f)) for f in (0, 0.2, 0.4, 0.55, 0.7, 0.9)))
")"

  out="$("$RIVE_CLI" render "$riv" --frames "$spread" --width "$w" --height "$h" --background '#F7F5EF' -o "$frames/" 2>&1)"
  echo "$out" | tail -3

  if echo "$out" | grep -qi "BLANK"; then
    echo "  FAIL: rendered blank" >&2
    failures=$((failures + 1))
  fi
  colours="$(echo "$out" | awk '/frame_00000/ {print $NF}')"
  if [ -n "$colours" ] && [ "$colours" -lt 20 ]; then
    echo "  FAIL: only ${colours} distinct colours, the frame is almost certainly empty" >&2
    failures=$((failures + 1))
  fi

  # For an animated scene, prove it MOVES. Distinct colour counts are the documented false
  # negative here: they can be identical frame to frame while the picture changes, and identical
  # while it does not. Hashes are the honest check, and rendering is deterministic so they are
  # stable. Every frame the same hash means nothing is animating, whatever the table says.
  if [ "$spread" != "0" ]; then
    distinct="$(sha256sum "$frames"/*.png | awk '{print $1}' | sort -u | wc -l)"
    total="$(ls "$frames"/*.png | wc -l)"
    if [ "$distinct" -lt 2 ]; then
      echo "  FAIL: ${total} frames, all byte-identical — the animation is not animating" >&2
      failures=$((failures + 1))
    else
      echo "  motion: ${distinct}/${total} frames distinct"
    fi
  fi
done

if [ "$failures" -gt 0 ]; then
  echo "${failures} diagram(s) failed" >&2
  exit 1
fi
echo "all diagrams generated, validated and rendered non-blank"
