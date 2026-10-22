#!/usr/bin/env bash
# Copy the files listed in the `files` input into the server directory.
# Paths are relative to the repository root.
set -euo pipefail

files="${FILES:-}"
server_dir="${SERVER_DIR:?SERVER_DIR is required}"

if [ -z "${files//[[:space:]]/}" ]; then
  echo 'No files to copy.'
  exit 0
fi

while IFS= read -r path; do
  path="$(printf '%s' "$path" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')"
  [ -z "$path" ] && continue
  case "$path" in \#*) continue ;; esac

  if [ ! -e "$path" ]; then
    echo "::error::'$path' does not exist in the repository"
    exit 1
  fi

  cp -r "$path" "$server_dir/"
  echo "Copied $path -> $server_dir/"
done <<< "$files"
