#!/bin/bash
# Behaviour tests of the http_endpoint image. Run on the workstation (Linux or WSL) with
# the docker CLI against a built image:
#
#   tests/run.sh http_endpoint:local
#
# Every container runs with --network none; requests are sent from inside the container
# (python/urllib) to the app on 127.0.0.1:8050. The data volume is a docker volume created
# for the test. Containers and volumes have names starting with a unique prefix and are
# removed at the end; nothing else is touched.
# Each check prints "PASS: <name>" or "FAIL: <name>: <reason>". The last line is
# "ALL <n> TESTS PASSED" (exit 0) or "<m> OF <n> TESTS FAILED" (exit 1).
set -euo pipefail

IMAGE="${1:-}"
[ -n "$IMAGE" ] && [ $# -eq 1 ] || { echo "Usage: $0 <image>" >&2; exit 2; }
command -v docker >/dev/null || { echo "docker not found" >&2; exit 2; }
docker image inspect "$IMAGE" >/dev/null 2>&1 || { echo "image not found: $IMAGE" >&2; exit 2; }

PFX="httpep-test-$$"
VOL="$PFX-data"
DATA=/var/www/app/data

cleanup() {
  local rc=$?
  trap - EXIT
  local ids
  ids="$(docker ps -aq --filter "name=${PFX}-" 2>/dev/null || true)"
  [ -z "$ids" ] || docker rm -f $ids >/dev/null 2>&1 || true
  docker volume rm -f "$VOL" >/dev/null 2>&1 || true
  exit $rc
}
trap cleanup EXIT
trap 'exit 130' INT TERM

# ---- helpers -------------------------------------------------------------------------

fail_t() { echo "$*"; exit 1; }                       # fail the current test (runs in a subshell)
expect() { [ "$2" = "$3" ] || fail_t "$1: expected [$3], got [$2]"; }
contains() { case "$2" in *"$3"*) ;; *) fail_t "$1: output does not contain [$3]: $2" ;; esac; }
lacks() { case "$2" in *"$3"*) fail_t "$1: output contains [$3]: $2" ;; esac; }

plain() { docker run --rm --network none --entrypoint sh "$IMAGE" -c "$1"; }

wait_until() {   # wait_until <tries> <cmd...>: run cmd every 0.5 s until it succeeds
  local n=$1; shift
  while [ "$n" -gt 0 ]; do "$@" >/dev/null 2>&1 && return 0; sleep 0.5; n=$((n - 1)); done
  return 1
}
health_is() { [ "$(docker inspect -f '{{.State.Health.Status}}' "$1" 2>/dev/null)" = "$2" ]; }

# Request from inside the container: req <container> <METHOD> <path> [content-type]
# The body is read from stdin. Prints "<status> <body>".
REQ_PY='
import sys, urllib.request, urllib.error
method, path = sys.argv[1], sys.argv[2]
ctype = sys.argv[3] if len(sys.argv) > 3 else None
body = sys.stdin.buffer.read() or None
r = urllib.request.Request("http://127.0.0.1:8050" + path, data=body, method=method)
if ctype:
    r.add_header("Content-Type", ctype)
try:
    resp = urllib.request.urlopen(r, timeout=10)
    print(resp.status, resp.read().decode())
except urllib.error.HTTPError as e:
    print(e.code, e.read().decode())
'
req() { local c="$1"; shift; docker exec -i "$c" python -c "$REQ_PY" "$@"; }

# A real ChirpStack uplink event, protobuf-encoded with chirpstack-api, on stdout
UPLINK_PY='
import sys
from chirpstack_api import integration
from google.protobuf.json_format import Parse
ev = Parse("{\"deviceInfo\": {\"devEui\": \"0102030405060708\", \"deviceName\": \"test-sensor\"}, \"fPort\": 8, \"fCnt\": 5, \"data\": \"AQID\"}", integration.UplinkEvent())
sys.stdout.buffer.write(ev.SerializeToString())
'

# Start a container on the test volume and wait until it is healthy: start_app <name>
start_app() {
  docker run -d --network none --name "$1" -v "$VOL:$DATA" "$IMAGE" >/dev/null || fail_t "could not start"
  wait_until 80 health_is "$1" healthy || fail_t "never healthy (status: $(docker inspect -f '{{.State.Health.Status}}' "$1")): $(docker logs "$1" 2>&1 | tail -n 8)"
}

PASSED=0 FAILED=0
run_test() {   # run_test <name> <function> [args...]
  local name="$1" fn="$2"; shift 2
  local out rc=0
  out="$($fn "$@" 2>&1)" || rc=$?
  if [ "$rc" -eq 0 ]; then
    PASSED=$((PASSED + 1)); echo "PASS: $name"
  else
    FAILED=$((FAILED + 1)); echo "FAIL: $name: $(printf '%s' "$out" | head -n 12 | sed '2,$s/^/    /')"
  fi
}

C1="$PFX-app1"
C2="$PFX-app2"

# ---- image contents ------------------------------------------------------------------

t_lacks() { ! plain "command -v $1" >/dev/null 2>&1 || fail_t "$1 is present"; }

t_python_imports() {
  docker run --rm --network none --entrypoint python "$IMAGE" -c \
    'import flask, gunicorn, gevent, pydantic, pydantic_settings, google.protobuf; from chirpstack_api import integration' 2>&1 || fail_t "import failed"
}

t_user() {
  expect "uid" "$(docker run --rm --network none --entrypoint id "$IMAGE" -u)" "30000"
  expect "configured user" "$(docker inspect -f '{{.Config.User}}' "$IMAGE")" "web"
}

t_healthcheck_defined() {
  contains "image healthcheck" "$(docker inspect -f '{{json .Config.Healthcheck}}' "$IMAGE")" "/health"
}

t_settings() {
  local out
  out="$(docker run --rm --network none --entrypoint python "$IMAGE" -c \
    'from config import settings; print(settings.DB_FILE); print(settings.JSON_OUTPUT_DIR)')"
  contains "DB_FILE" "$out" "$DATA/events.sqlite"
  contains "JSON_OUTPUT_DIR" "$out" "$DATA/json"
}

t_event_types() {
  local out
  out="$(docker run --rm --network none --entrypoint python "$IMAGE" -c     'from handlers import event_dict; print(sorted(event_dict))')" || fail_t "handlers do not import"
  expect "event types" "$out" "['ack', 'integration', 'join', 'location', 'log', 'status', 'txack', 'up']"
}

t_log_level() {
  local cmd
  cmd="$(docker inspect -f '{{json .Config.Cmd}}' "$IMAGE")"
  contains "gunicorn command" "$cmd" '"info"'
  lacks "gunicorn command" "$cmd" 'debug'
}

# ---- app -----------------------------------------------------------------------------
# The tests below share the container C1 (and the volume), in this order. Each one is
# its own subshell, so the app is started by the first one and the others check that it ran.

t_starts_healthy() {
  docker volume create "$VOL" >/dev/null || fail_t "could not create the test volume"
  start_app "$C1"
}

need_app() { health_is "$C1" healthy || fail_t "the app did not start"; }

t_health() {
  need_app
  expect "GET /health" "$(req "$C1" GET /health </dev/null)" "200 OK"
}

t_index() {
  need_app
  local out; out="$(req "$C1" GET / </dev/null)"
  expect "GET / status" "${out%% *}" "200"
}

t_uplink_protobuf() {
  need_app
  local out files rows
  out="$(docker exec "$C1" python -c "$UPLINK_PY" | req "$C1" POST '/event?event=up' application/octet-stream)"
  expect "POST /event?event=up" "$out" "200 up event processed"
  files="$(docker exec "$C1" sh -c "ls $DATA/json")"
  case "$files" in up_*.json) ;; *) fail_t "no up_*.json file in $DATA/json: $files" ;; esac
  contains "json file" "$(docker exec "$C1" sh -c "cat $DATA/json/up_*.json")" "0102030405060708"
  rows="$(docker exec "$C1" python -c "
import sqlite3
c = sqlite3.connect('$DATA/events.sqlite')
print(c.execute('select count(*), min(event_type) from messages').fetchone())
print(c.execute('select payload from messages').fetchone()[0])")"
  contains "sqlite rows" "$rows" "(1, 'up')"
  contains "sqlite payload" "$rows" "0102030405060708"
  contains "GET /last-messages" "$(req "$C1" GET '/last-messages?n=5&event=up' </dev/null)" "test-sensor"
}

t_uplink_json() {
  need_app
  sleep 1   # file names have a one-second timestamp
  local out
  out="$(printf '%s' '{"deviceInfo":{"devEui":"1111111111111111"},"fPort":1}' | req "$C1" POST '/event?event=up' application/json)"
  expect "POST json" "$out" "200 up event processed"
}

t_bad_requests() {
  need_app
  expect "unknown event" "$(printf 'x' | req "$C1" POST '/event?event=nope' application/octet-stream | cut -c1-3)" "400"
  expect "empty body" "$(req "$C1" POST '/event?event=up' application/octet-stream </dev/null | cut -c1-3)" "400"
  expect "wrong content type" "$(printf 'x' | req "$C1" POST '/event?event=up' text/plain | cut -c1-3)" "400"
}

t_clear_messages_gone() {
  need_app
  local m
  for m in GET POST; do
    case "$(req "$C1" "$m" '/clear_messages?confirm=yes' </dev/null | cut -c1-3)" in
      404|405) ;;
      *) fail_t "$m /clear_messages is still served" ;;
    esac
  done
  contains "messages kept" "$(req "$C1" GET '/last-messages?n=10' </dev/null)" "0102030405060708"
}

t_data_only_in_volume() {
  need_app
  local found
  found="$(docker exec "$C1" sh -c "find / -xdev \( -name '*.sqlite' -o -name '*.db' -o -name 'up_*.json' \) -not -path '/proc/*' -not -path '$DATA/*' 2>/dev/null" || true)"
  expect "data files outside the volume" "$found" ""
  expect "owner of the database file" "$(docker exec "$C1" stat -c '%u' "$DATA/events.sqlite")" "30000"
}

t_logs() {
  need_app
  local logs; logs="$(docker logs "$C1" 2>&1)"
  contains "container log" "$logs" "Booting worker"
  contains "container log" "$logs" "Stored message of type 'up'"
  lacks "container log" "$logs" "[DEBUG]"
}

t_persistence() {
  need_app
  docker rm -f "$C1" >/dev/null
  start_app "$C2"
  contains "messages after restart" "$(req "$C2" GET '/last-messages?n=10' </dev/null)" "0102030405060708"
  expect "json files after restart" "$(docker exec "$C2" sh -c "ls $DATA/json | wc -l")" "2"
}

# ---- run -----------------------------------------------------------------------------

for c in sudo nano vi vim curl wget git unzip; do run_test "image lacks $c" t_lacks "$c"; done
run_test "image python packages import" t_python_imports
run_test "image runs as the web user (uid 30000)" t_user
run_test "image defines a healthcheck on /health" t_healthcheck_defined
run_test "database and JSON paths default into the data volume" t_settings
run_test "all eight ChirpStack event types are known to the installed chirpstack-api" t_event_types
run_test "gunicorn log level is info" t_log_level

run_test "app starts and becomes healthy" t_starts_healthy
run_test "GET /health is OK" t_health
run_test "GET / serves the index page" t_index
run_test "protobuf uplink is stored as JSON file and in SQLite in the data volume" t_uplink_protobuf
run_test "JSON uplink is accepted" t_uplink_json
run_test "bad requests are rejected" t_bad_requests
run_test "/clear_messages is gone and deletes nothing" t_clear_messages_gone
run_test "no data files outside the volume, database owned by uid 30000" t_data_only_in_volume
run_test "container log shows info lines, no debug" t_logs
run_test "data survives a new container on the same volume" t_persistence

TOTAL=$((PASSED + FAILED))
if [ "$FAILED" -eq 0 ]; then
  echo "ALL $TOTAL TESTS PASSED"
  exit 0
fi
echo "$FAILED OF $TOTAL TESTS FAILED"
exit 1
