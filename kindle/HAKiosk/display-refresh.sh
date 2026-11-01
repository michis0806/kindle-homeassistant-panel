# Sourceable, foreground-only PW1 E-Ink refresh helpers.
# Caller sets ROOT, then calls display_refresh_init START and
# display_refresh_tick NOW LAST_TOUCH from its existing foreground loop.
# The interval is read at init; restart the caller to apply configuration edits.

display_refresh_init() {
    DISPLAY_REFRESH_INTERVAL=300
    if [ -r "$ROOT/display-refresh-seconds.txt" ]; then
        DISPLAY_REFRESH_INTERVAL=$(cat "$ROOT/display-refresh-seconds.txt" 2>/dev/null)
    fi
    case "$DISPLAY_REFRESH_INTERVAL" in
        0) DISPLAY_REFRESH_DISABLED=1;;
        ''|*[!0-9]*) DISPLAY_REFRESH_DISABLED=1; echo 'Display refresh disabled: invalid interval' >&2;;
        *)
            if [ "$DISPLAY_REFRESH_INTERVAL" -lt 60 ] || [ "$DISPLAY_REFRESH_INTERVAL" -gt 86400 ]; then
                DISPLAY_REFRESH_DISABLED=1
                echo 'Display refresh disabled: interval must be 0 or 60..86400 seconds' >&2
            else DISPLAY_REFRESH_DISABLED=0
            fi;;
    esac
    DISPLAY_REFRESH_LAST=${1:-0}
    case "$DISPLAY_REFRESH_LAST" in ''|*[!0-9]*) DISPLAY_REFRESH_LAST=0;; esac

    # EIPS_COMMAND is an executable path override for isolated tests only.
    # Production callers leave it unset; never evaluate a command string.
    if [ -n "${EIPS_COMMAND:-}" ]; then
        if [ ! -x "$EIPS_COMMAND" ]; then
            DISPLAY_REFRESH_DISABLED=1
            echo 'Display refresh disabled: configured eips executable unavailable' >&2
        fi
    elif command -v eips >/dev/null 2>&1; then
        EIPS_COMMAND=$(command -v eips)
    elif [ -x /usr/sbin/eips ]; then
        EIPS_COMMAND=/usr/sbin/eips
    else
        EIPS_COMMAND=
        DISPLAY_REFRESH_DISABLED=1
        echo 'Display refresh disabled: eips unavailable' >&2
    fi
}

display_refresh_tick() {
    [ "${DISPLAY_REFRESH_DISABLED:-1}" -eq 0 ] || return 0
    _dr_now=$1
    _dr_touch=$2
    case "$_dr_now" in ''|*[!0-9]*) return 0;; esac
    case "$_dr_touch" in ''|*[!0-9]*) return 0;; esac
    [ "$_dr_now" -ge "$DISPLAY_REFRESH_LAST" ] || return 0
    [ "$((_dr_now - DISPLAY_REFRESH_LAST))" -ge "$DISPLAY_REFRESH_INTERVAL" ] || return 0
    [ "$_dr_now" -ge "$_dr_touch" ] || return 0
    [ "$((_dr_now - _dr_touch))" -ge 5 ] || return 0

    if "$EIPS_COMMAND" -s w=758,h=1024 -f >/dev/null 2>&1; then
        DISPLAY_REFRESH_LAST=$_dr_now
        return 0
    fi
    DISPLAY_REFRESH_DISABLED=1
    echo 'Display refresh disabled for this session: eips command failed' >&2
    return 1
}
