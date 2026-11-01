#!/bin/sh
# PW1 path and LIPC + sysfs sequence used by KOReader's Kindle backend.
ROOT=/mnt/us/extensions/HAKiosk
STATE="$ROOT/state/full-off-test"
HW=/sys/devices/system/fl_tps6116x/fl_tps6116x0/fl_intensity
mkdir -p "$STATE" || exit 1
exec >> "$ROOT/light-off-test.log" 2>&1
printf '\n--- %s: full light off %s ---\n' "$(date)" "$1"
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
case "$1" in
    restore) restore; exit $?;;
    test) ;;
    *) echo 'Unknown mode'; exit 1;;
esac
[ -r "$HW" ] && [ -w "$HW" ] || { echo 'PW1 frontlight driver path unavailable; no brightness change'; exit 1; }
# End any running observer before saving values or changing the driver.
sh "$ROOT/kiosk.sh" home || { echo 'Kiosk cleanup failed; no test started'; exit 1; }
sleep 2
if [ -f "$STATE/level" ] || [ -f "$STATE/hardware" ]; then
    restore || exit 1
fi
LEVEL=$(lipc-get-prop com.lab126.powerd flIntensity) || exit 1
RAW=$(read_hardware) || exit 1
case "$LEVEL" in [0-9]|1[0-9]|2[0-4]) ;; *) echo 'Invalid software brightness'; exit 1;; esac
case "$RAW" in ''|*[!0-9]*) echo 'Invalid hardware brightness'; exit 1;; esac
printf '%s\n' "$LEVEL" > "$STATE/level" || exit 1
printf '%s\n' "$RAW" > "$STATE/hardware" || exit 1
trap 'restore' 0
trap 'exit 1' 1 2 15
echo "Original software=$LEVEL hardware=$RAW; driver report: $(cat "$HW")"
lipc-set-prop com.lab126.powerd flIntensity 0 || exit 1
printf '%s\n' 0 > "$HW" || exit 1
OFF=$(read_hardware) || exit 1
echo "Full off requested; normalized driver read-back=$OFF"
[ "$OFF" = 0 ] || { echo 'Driver did not confirm off'; exit 1; }
sleep 5
echo "Before restoration: software=$(lipc-get-prop com.lab126.powerd flIntensity) driver=$(read_hardware)"
restore || exit 1
trap - 0 1 2 15
echo "Five-second test complete; software=$(lipc-get-prop com.lab126.powerd flIntensity) driver=$(read_hardware)"
