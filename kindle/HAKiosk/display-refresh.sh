#!/bin/sh
# PW1: request a flashing update of existing pixels; never clear the framebuffer.
LOG=/mnt/us/extensions/HAKiosk/display-refresh.log
exec >> "$LOG" 2>&1
printf '\n--- %s: manual full display refresh ---\n' "$(date)"
EIPS=$(command -v eips)
[ -n "$EIPS" ] || EIPS=/usr/sbin/eips
[ -x "$EIPS" ] || { echo 'eips unavailable'; exit 1; }
"$EIPS" -s w=758,h=1024 -f
RESULT=$?
echo "Full refresh result: $RESULT"
exit "$RESULT"
