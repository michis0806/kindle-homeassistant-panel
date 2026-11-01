#!/bin/sh
# Restore saved PW1 frontlight values, including legacy recovery state.
ROOT=/mnt/us/extensions/HAKiosk
STATE="$ROOT/state/full-off-test"
HW=/sys/devices/system/fl_tps6116x/fl_tps6116x0/fl_intensity
restore() {
    FAILED=0
    if [ -f "$STATE/level" ]; then
        SAVED_LEVEL=$(cat "$STATE/level")
        case "$SAVED_LEVEL" in
            [0-9]|1[0-9]|2[0-4]) lipc-set-prop com.lab126.powerd flIntensity "$SAVED_LEVEL" || FAILED=1;;
            *) echo 'Invalid saved LIPC level'; FAILED=1;;
        esac
    fi
    if [ -f "$STATE/hardware" ]; then
        SAVED_HW=$(cat "$STATE/hardware")
        case "$SAVED_HW" in
            ''|*[!0-9]*) echo 'Invalid saved driver intensity'; FAILED=1;;
            *)
                if [ -w "$HW" ]; then
                    printf '%s\n' "$SAVED_HW" > "$HW" || FAILED=1
                else
                    echo 'Driver unavailable for restoration'; FAILED=1
                fi
                ;;
        esac
    fi
    if [ "$FAILED" -eq 0 ]; then
        rm -f "$STATE/level" "$STATE/hardware"
        echo 'Original software and driver brightness restored.'
    else
        echo 'Restoration incomplete; original values retained. Run Licht wiederherstellen.'
    fi
    return "$FAILED"
}
restore
