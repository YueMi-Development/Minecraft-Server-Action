#!/usr/bin/env bash
# Install the Minecraft server by replaying the installation steps mcjars
# describes for the resolved build. The steps cover everything a server type
# needs: a plain jar for most types, a zip that has to be unpacked alongside a
# libraries/ tree for Forge.
set -euo pipefail

server_dir="${SERVER_DIR:?SERVER_DIR is required}"
steps_file="${STEPS_FILE:-${server_dir}/.mcjars-installation.json}"

mkdir -p "$server_dir"
cd "$server_dir"

if [ ! -f "$steps_file" ]; then
  echo "::error::No installation steps found at $steps_file"
  exit 1
fi

# Reject paths that would escape the server directory.
check_path() {
  case "$1" in
    /*|..|../*|*/../*|*/..)
      echo "::error::Refusing to use path '$1' outside the server directory"
      exit 1
      ;;
  esac
}

step_count=0
while IFS=$'\t' read -r kind target source; do
  [ -z "$kind" ] && continue
  # Strip any carriage returns so a CRLF-encoded source cannot corrupt a URL.
  kind="${kind%$'\r'}"
  target="${target%$'\r'}"
  source="${source%$'\r'}"

  case "$kind" in
    download)
      check_path "$target"
      echo "Downloading $target"
      curl -fL --retry 3 --retry-delay 5 -o "$target" "$source"
      ;;
    unzip)
      check_path "$target"
      check_path "$source"
      echo "Unpacking $target into $source"
      mkdir -p "$source"
      unzip -o -q "$target" -d "$source"
      ;;
    remove)
      check_path "$target"
      echo "Removing $target"
      rm -rf "$target"
      ;;
    *)
      echo "::error::Unknown installation step '$kind'"
      exit 1
      ;;
  esac

  step_count=$((step_count + 1))
done < <(python3 - "$steps_file" <<'PY'
import json
import sys

with open(sys.argv[1], encoding='utf-8') as handle:
    groups = json.load(handle)

for group in groups:
    for step in group:
        kind = step.get('type')
        if kind == 'download':
            print('\t'.join([kind, step.get('file', ''), step.get('url', '')]))
        elif kind == 'unzip':
            print('\t'.join([kind, step.get('file', ''), step.get('location', '.')]))
        elif kind == 'remove':
            print('\t'.join([kind, step.get('location', ''), '']))
        else:
            print('\t'.join([str(kind), '', '']))
PY
)
if [ "$step_count" -eq 0 ]; then
  echo "::error::The installation steps were empty"
  exit 1
fi

rm -f "$steps_file"

# The install may legitimately produce a jar, a zip that was unpacked, or a
# directory tree; what matters is that something landed in the server folder.
if [ -z "$(ls -A)" ]; then
  echo "::error::The installation produced no files in $server_dir"
  exit 1
fi

if ! find . -name '*.jar' -print -quit | grep -q .; then
  echo "::error::No jar was found in $server_dir after the install"
  exit 1
fi
