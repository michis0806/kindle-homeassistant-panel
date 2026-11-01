#!/bin/sh
# PW1 touchscreen observer. Never grab the device or change browser callbacks.
ROOT=/mnt/us/extensions/HAKiosk
STATE="$ROOT/state"
EVTEST="$ROOT/tools/bin/evtest"
INPUT=/dev/input/event0
IDLE_SECONDS=30
DIM_LEVEL=0
HW=/sys/devices/system/fl_tps6116x/fl_tps6116x0/fl_intensity
read_hardware() {
    REPORT=$(cat "$HW") || return 1
    # PW1 uses a labelled report; newer/plain test files may contain only a number.
    VALUE=$(printf '%s\n' "$REPORT" | sed -n \
        -e 's/^[[:space:]]*FrontLight(Intensity)[[:space:]]*=[[:space:]]*\([0-9][0-9]*\)[[:space:]]*$/\1/' \
        -e 's/^[[:space:]]*\([0-9][0-9]*\)[[:space:]]*$/\1/p')
    case "$VALUE" in
        ''|*[!0-9]*) printf 'Unrecognized driver report: <%s>\n' "$REPORT" >&2; return 1;;
    esac
    printf '%s\n' "$VALUE"
}
now() {
    read UP REST < /proc/uptime || return 1
    NOW=${UP%%.*}
}
collect() {
    LAST_WRITTEN=
    while IFS= read -r LINE; do
        case "$LINE" in
            *'type 3 (EV_ABS)'*|*'type 1 (EV_KEY)'*)
                now || exit 1
                if [ "$NOW" != "$LAST_WRITTEN" ]; then
                    printf '%s\n' "$NOW" > "$WORK/last-touch.tmp" || exit 1
                    mv "$WORK/last-touch.tmp" "$WORK/last-touch" || exit 1
                    LAST_WRITTEN=$NOW
                fi
                ;;
        esac
    done
}
stop_running() {
    [ -f "$STATE/touch-light.pid" ] || return 0
    PID=$(cat "$STATE/touch-light.pid")
    case "$PID" in ''|*[!0-9]*) echo 'Invalid observer PID'; return 1;; esac
    if [ ! -r "/proc/$PID/cmdline" ]; then
        rm -f "$STATE/touch-light.pid"
        return 0
    fi
    CMD=$(tr '\000' ' ' < "/proc/$PID/cmdline")
    case "$CMD" in
        *"$ROOT/touch-light.sh run"*|*"$ROOT/touch-light.sh test"*|*"$ROOT/touch-light-v2.sh run"*|*"$ROOT/touch-light-v2.sh test"*|*"$ROOT/touch-light-v3.sh run"*|*"$ROOT/touch-light-v3.sh test"*|*"$ROOT/touch-light-v4.sh run"*|*"$ROOT/touch-light-v4.sh test"*) ;;
        *) echo 'Observer PID no longer belongs to this app'; rm -f "$STATE/touch-light.pid"; return 0;;
    esac
    kill "$PID" 2>/dev/null || return 1
    COUNT=0
    while [ -f "$STATE/touch-light.pid" ] && [ "$COUNT" -lt 5 ]; do sleep 1; COUNT=$((COUNT + 1)); done
    [ ! -f "$STATE/touch-light.pid" ] || { echo 'Observer did not stop; brightness state retained'; return 1; }
}
if [ "$1" = stop ]; then stop_running; exit $?; fi
if [ "$1" = collect ]; then
    WORK=$2
    collect
    exit $?
fi
[ "$1" = run ] || exit 1
exec >> "$ROOT/touch-light.log" 2>&1
printf '\n--- %s: touchscreen light observer ---\n' "$(date)"
[ -x "$EVTEST" ] && [ -c "$INPUT" ] || { echo 'Touch event reader/device unavailable'; exit 1; }
[ ! -e "$STATE/light-original" ] && [ ! -e "$STATE/light-original-hardware" ] || { echo 'Unrestored brightness state; use Kiosk beenden / Home first'; exit 1; }
ORIGINAL=$(lipc-get-prop com.lab126.powerd flIntensity) || exit 1
case "$ORIGINAL" in [0-9]|1[0-9]|2[0-4]) ;; *) echo 'Invalid brightness reading'; exit 1;; esac
[ -r "$HW" ] && [ -w "$HW" ] || { echo 'PW1 frontlight driver unavailable'; exit 1; }
ORIGINAL_HW=$(read_hardware) || exit 1
ORIGINAL_POWER=
if [ -r "$STATE/prevent-screensaver" ]; then
    SAVED_POWER=$(cat "$STATE/prevent-screensaver")
    case "$SAVED_POWER" in 0|1) ORIGINAL_POWER=$SAVED_POWER;; esac
fi
BRIGHT_LEVEL=$ORIGINAL
if [ "$BRIGHT_LEVEL" -lt 8 ]; then BRIGHT_LEVEL=14; fi
umask 077
WORK=/tmp/kindle-touch-light-$$
mkdir "$WORK" || exit 1
EV_PID=; COLLECT_PID=
APP_PID=
cleanup() {
    trap - 0 1 2 15
    if [ -n "$EV_PID" ]; then kill "$EV_PID" 2>/dev/null; wait "$EV_PID" 2>/dev/null; fi
    if [ -n "$COLLECT_PID" ]; then kill "$COLLECT_PID" 2>/dev/null; wait "$COLLECT_PID" 2>/dev/null; fi
    RESTORE_FAILED=0
    lipc-set-prop com.lab126.powerd flIntensity "$ORIGINAL" || RESTORE_FAILED=1
    if [ -w "$HW" ]; then
        printf '%s\n' "$ORIGINAL_HW" > "$HW" || RESTORE_FAILED=1
    else
        RESTORE_FAILED=1
    fi
    if [ "$RESTORE_FAILED" -eq 0 ]; then
        rm -f "$STATE/light-original" "$STATE/light-original-hardware"
        echo "Original brightness restored: software=$ORIGINAL hardware=$ORIGINAL_HW"
    else
        echo 'Brightness restore failed; both original values retained for Home action'
    fi
    if [ -n "$ORIGINAL_POWER" ]; then
        if lipc-set-prop com.lab126.powerd preventScreenSaver "$ORIGINAL_POWER"; then
            rm -f "$STATE/prevent-screensaver"
            echo "Original screensaver setting restored: $ORIGINAL_POWER"
        fi
    fi
    if [ "$(cat "$STATE/touch-light.pid" 2>/dev/null)" = "$$" ]; then rm -f "$STATE/touch-light.pid"; fi
    rm -f "$WORK/events" "$WORK/last-touch" "$WORK/last-touch.tmp"
    rmdir "$WORK" 2>/dev/null
}
trap cleanup 0
trap 'exit 1' 1 2 15
printf '%s\n' "$ORIGINAL" > "$STATE/light-original" || exit 1
printf '%s\n' "$ORIGINAL_HW" > "$STATE/light-original-hardware" || exit 1
printf '%s\n' "$$" > "$STATE/touch-light.pid" || exit 1
mkfifo "$WORK/events" || exit 1
now || exit 1
START=$NOW
printf '%s\n' "$START" > "$WORK/last-touch"
# No --grab: the existing browser continues to receive all touch input.
"$EVTEST" "$INPUT" > "$WORK/events" 2> "$ROOT/touch-reader-error.log" &
EV_PID=$!
sh "$ROOT/touch-light.sh" collect "$WORK" < "$WORK/events" &
COLLECT_PID=$!
sleep 1
kill -0 "$EV_PID" 2>/dev/null && kill -0 "$COLLECT_PID" 2>/dev/null || { echo 'Event reader failed to start'; exit 1; }
echo "Reader running; idle=${IDLE_SECONDS}s original=$ORIGINAL bright=$BRIGHT_LEVEL dim=$DIM_LEVEL"
# Stop when the native app exits.
find_kiosk_pid() {
    for PROC in /proc/[0-9]*/cmdline; do
        [ -r "$PROC" ] || continue
        CMD=$(tr '\000' ' ' < "$PROC" 2>/dev/null)
        case "$CMD" in
            *mesquite*'-l com.schmid.kindlekiosk'*)
                APP_PID=${PROC#/proc/}; APP_PID=${APP_PID%/cmdline}; break;;
        esac
    done
    [ -n "$APP_PID" ] || { echo 'Cannot find native kiosk process; leaving brightness unchanged'; return 1; }
}
find_kiosk_pid || exit 1
URL=$(head -n 1 "$ROOT/url.txt" | tr -d '\r')
STATUS_URL="${URL%/}/kiosk-status"
CONTROLLER=$(cat "$ROOT/controller-id.txt" 2>/dev/null)
if [ -n "$CONTROLLER" ]; then
    case "$CONTROLLER" in *[!a-f0-9]*) exit 1;; esac
    [ "${#CONTROLLER}" -eq 32 ] || exit 1
    STATUS_URL="$STATUS_URL?controller=$CONTROLLER"
fi
BASE=$(cat "$STATE/exit-generation") || exit 1
case "$BASE" in ''|*[!0-9]*) echo 'Invalid baseline exit status'; exit 1;; esac
REFRESH_URL=
REFRESH_BASE=$(cat "$STATE/refresh-generation" 2>/dev/null)
case "$REFRESH_BASE" in ''|*[!0-9]*) REFRESH_BASE=;; esac
REFRESH_AT=0
if [ -n "$CONTROLLER" ]; then REFRESH_URL="${URL%/}/kiosk-refresh?controller=$CONTROLLER"; fi
NEXT_REFRESH_POLL=0
NEXT_POLL=0
LEVEL=
while :; do
    kill -0 "$EV_PID" 2>/dev/null && kill -0 "$COLLECT_PID" 2>/dev/null || { echo 'Event reader stopped; aborting'; exit 1; }
    now || exit 1
    [ -d "$ROOT" ] && kill -0 "$APP_PID" 2>/dev/null || { echo 'Native kiosk stopped'; break; }
    if [ "$NOW" -ge "$NEXT_POLL" ]; then
        NEXT_POLL=$((NOW + 2))
        GENERATION=$("$ROOT/tools/kiosk-http-get" "$STATUS_URL" 2>/dev/null)
        case "$GENERATION" in
            ''|*[!0-9]*) ;; # Keep light operation working during network failures.
            *) if [ "$GENERATION" != "$BASE" ]; then echo 'Visible exit button requested Home'; break; fi;;
        esac
    fi
    if [ "$NOW" -ge "$NEXT_REFRESH_POLL" ] 2>/dev/null && [ -n "$REFRESH_URL" ]; then
        NEXT_REFRESH_POLL=$((NOW + 2))
        READY=$("$ROOT/tools/kiosk-http-get" "$REFRESH_URL" 2>/dev/null)
        case "$READY" in
            ''|*[!0-9]*) ;;
            *)
                if [ -z "$REFRESH_BASE" ]; then REFRESH_BASE=$READY
                elif [ "$READY" != "$REFRESH_BASE" ]; then
                    REFRESH_BASE=$READY
                    REFRESH_AT=$((NOW + 1))
                fi;;
        esac
    fi
    LAST=$(cat "$WORK/last-touch")
    case "$LAST" in ''|*[!0-9]*) echo 'Invalid activity time'; exit 1;; esac
    if [ "$REFRESH_AT" -gt 0 ] && [ "$NOW" -ge "$REFRESH_AT" ] && [ $((NOW - LAST)) -ge 2 ]; then
        # One request, one attempt. Network errors never trigger a display flash.
        REFRESH_AT=0
        if sh "$ROOT/display-refresh.sh"; then echo 'Manual full refresh completed'; else echo 'Manual full refresh failed; see display-refresh.log'; fi
    fi
    TARGET=$BRIGHT_LEVEL
    if [ $((NOW - LAST)) -ge "$IDLE_SECONDS" ]; then TARGET=$DIM_LEVEL; fi
    if [ "$LEVEL" != "$TARGET" ]; then
        lipc-set-prop com.lab126.powerd flIntensity "$TARGET" || exit 1
        if [ "$TARGET" -eq 0 ]; then
            printf '%s\n' 0 > "$HW" || exit 1
            OFF=$(read_hardware) || exit 1
            [ "$OFF" = 0 ] || { echo 'Driver did not confirm complete off'; exit 1; }
        fi
        LEVEL=$TARGET
        echo "Elapsed=$((NOW - START))s idle=$((NOW - LAST))s requested=$LEVEL actual=$(lipc-get-prop com.lab126.powerd flIntensity) hardware=$(read_hardware)"
    fi
    sleep 1
done
echo 'Touch light observer finished'
