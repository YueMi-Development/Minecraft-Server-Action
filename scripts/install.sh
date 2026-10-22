#!/usr/bin/env bash
# Download the Minecraft server by running the install script mcjars generates
# for the resolved build. Using their script means multi-step installs (Forge
# downloads a zip and unpacks it) work the same way as single-jar ones.
set -euo pipefail

build_id="${BUILD_ID:?BUILD_ID is required}"
server_dir="${SERVER_DIR:?SERVER_DIR is required}"

mkdir -p "$server_dir"
cd "$server_dir"

curl -fsSL --retry 3 --retry-delay 5 \
  "https://mcjars.app/api/v1/script/$build_id/bash" -o install.sh
bash install.sh

# The install script downloads whatever the server type needs: a jar for most
# types, a zip that it unpacks for Forge. Either way something has to be there.
if [ -z "$(ls -A)" ]; then
  echo "::error::The install script produced no files in $server_dir"
  exit 1
fi

if ! find . -name '*.jar' -print -quit | grep -q .; then
  echo "::error::No jar was found in $server_dir after the install"
  exit 1
fi
