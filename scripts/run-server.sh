#!/usr/bin/env bash
# Start the Minecraft server, stream its console output, and stop it cleanly
# once the run timeout elapses so the world is flushed to disk.
set -euo pipefail

server_dir="${SERVER_DIR:?SERVER_DIR is required}"
run_timeout="${RUN_TIMEOUT:-10m}"
min_memory="${MIN_MEMORY:-512M}"
max_memory="${MAX_MEMORY:-2G}"

cd "$server_dir"

# Forge ships a launcher jar plus a libraries/ tree; its real entry point is the
# unix_args.txt that comes with the installation. Every other server type is a
# single jar named server.jar.
if [ -d libraries/net/minecraftforge/forge ]; then
  args_file="$(find libraries/net/minecraftforge/forge -name unix_args.txt | head -n 1)"
  if [ -z "$args_file" ]; then
    echo '::error::Could not find unix_args.txt in the Forge installation'
    exit 1
  fi
  set -- "@$args_file" nogui
else
  set -- -jar server.jar nogui
fi

echo "Launching: java -Xms$min_memory -Xmx$max_memory $*"

# A FIFO carries the `stop` command to the server's stdin.
fifo="$(mktemp -u)"
mkfifo "$fifo"
# Opening it read-write keeps it open even when no writer is attached yet, so
# the java process below does not block on opening it.
exec 3<> "$fifo"

cleanup() {
  exec 3>&- || true
  rm -f "$fifo"
}
trap cleanup EXIT

# The wrapper records the java PID before exec'ing it, so the shutdown below can
# signal the server directly instead of guessing through the process tree.
pid_file="$(mktemp)"
(
  java -Xms"$min_memory" -Xmx"$max_memory" "$@" < "$fifo" &
  echo $! > "$pid_file"
  wait
) 2>&1 | tee server.log &
tee_pid=$!

java_pid=''
for _ in $(seq 1 40); do
  if [ -s "$pid_file" ]; then
    java_pid="$(cat "$pid_file")"
    break
  fi
  sleep 0.25
done
rm -f "$pid_file"

if [ -z "$java_pid" ]; then
  echo '::error::Could not determine the server process id'
  exit 1
fi

sleep "$run_timeout" || true

if kill -0 "$java_pid" 2>/dev/null; then
  echo "Run timeout of $run_timeout reached, stopping the server."
  # `stop` makes the server save the world and exit on its own. The server reads
  # commands line by line, so the newline matters.
  echo 'stop' >&3 || true
  for _ in $(seq 1 30); do
    kill -0 "$java_pid" 2>/dev/null || break
    sleep 1
  done
  if kill -0 "$java_pid" 2>/dev/null; then
    echo 'The server did not stop in time, terminating it.'
    kill -TERM "$java_pid" 2>/dev/null || true
    sleep 5
    kill -KILL "$java_pid" 2>/dev/null || true
  fi
else
  echo 'The server is no longer running.'
fi

wait 2>/dev/null || true
