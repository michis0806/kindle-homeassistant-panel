#!/bin/sh
# Native content-window approach documented by PaulFreund/WebLaunch.
ROOT=/mnt/us/extensions/HAKiosk
STATE="$ROOT/state"
CFG=/var/local/mesquite/browser/config.xml
APPREG=/var/local/appreg.db
APP_ID=com.schmid.kindlekiosk
SQLITE="$ROOT/tools/sqlite3"
OLD_COMMAND="/usr/bin/mesquite -l $APP_ID -c $ROOT/web/"
MIGRATION_COMMAND="/usr/bin/mesquite -l $APP_ID -c file://$ROOT/web-v3/"
PREVIOUS_COMMAND="/usr/bin/mesquite -l $APP_ID -c file://$ROOT/web-v2/"
RUN="-l $APP_ID -c file://$ROOT/web/"
COMMAND="/usr/bin/mesquite $RUN"
db() {
    # The PW1 SQLite CLI supports .timeout, even on its old runtime.
    printf '.timeout 5000\n%s\n' "$1" | "$SQLITE" "$APPREG"
}
mkdir -p "$STATE" || exit 1
exec >> "$ROOT/kiosk.log" 2>&1
printf '\n--- %s: %s ---\n' "$(date)" "$1"
URL=$(head -n 1 "$ROOT/url.txt" | tr -d '\r')
case "$URL" in http://*|https://*) ;; *) echo 'Invalid URL'; exit 1;; esac
restore_light() {
    if [ -f "$STATE/light-original" ]; then
        LEVEL=$(cat "$STATE/light-original")
        case "$LEVEL" in
            [0-9]|1[0-9]|2[0-4]) lipc-set-prop com.lab126.powerd flIntensity "$LEVEL" || return 1;;
            *) echo 'Invalid saved brightness'; return 1;;
        esac
    fi
    if [ -f "$STATE/light-original-hardware" ]; then
        RAW=$(cat "$STATE/light-original-hardware")
        case "$RAW" in ''|*[!0-9]*) echo 'Invalid saved hardware brightness'; return 1;; esac
        HW=/sys/devices/system/fl_tps6116x/fl_tps6116x0/fl_intensity
        [ -w "$HW" ] || return 1
        printf '%s\n' "$RAW" > "$HW" || return 1
    fi
    if [ -f "$STATE/light-original" ] || [ -f "$STATE/light-original-hardware" ]; then
        rm -f "$STATE/light-original" "$STATE/light-original-hardware"
        echo 'Original software and hardware brightness restored.'
    fi
}
restore_config() {
    sh "$ROOT/touch-light.sh" stop || return 1
    restore_light || return 1
    if [ -f "$STATE/browser-config.xml" ]; then
        [ -s "$STATE/browser-config.xml" ] || return 1
        # FAT cannot preserve Unix ownership. Preserve the existing target inode.
        cat "$STATE/browser-config.xml" > "$CFG" || return 1
        rm -f "$STATE/browser-config.xml"
        echo 'Original browser config restored.'
    fi
    if [ -f "$STATE/prevent-screensaver" ]; then
        OLD=$(cat "$STATE/prevent-screensaver")
        case "$OLD" in
            0|1) lipc-set-prop com.lab126.powerd preventScreenSaver "$OLD" || return 1;;
            *) echo 'Invalid saved power state'; return 1;;
        esac
        rm -f "$STATE/prevent-screensaver"
    fi
}
register_native() {
    [ -x "$SQLITE" ] || { echo 'Bundled SQLite wrapper not executable'; return 1; }
    "$SQLITE" -version || { echo 'Bundled SQLite runtime cannot start'; return 1; }
    [ -f "$APPREG" ] || { echo 'Application registry not found'; return 1; }
    [ -x /usr/bin/mesquite ] || { echo 'Native web runtime not found'; return 1; }
    MISSING=0
    for LIB in Kindle.js logging.js eventing.js object.js storage.js applicationManager.js; do
        if [ ! -f "/var/local/mesquite/shared/javascripts/$LIB" ]; then
            echo "Missing native web library: $LIB"; MISSING=1
        fi
    done
    [ "$MISSING" -eq 0 ] || return 1
    EXISTING=$(db "SELECT value FROM properties WHERE handlerId='$APP_ID' AND name='command';") || return 1
    if [ -n "$EXISTING" ] && [ "$EXISTING" != "$COMMAND" ] && [ "$EXISTING" != "$OLD_COMMAND" ] && [ "$EXISTING" != "$PREVIOUS_COMMAND" ] && [ "$EXISTING" != "$MIGRATION_COMMAND" ]; then
        echo 'Application ID conflict; no registry change made'; return 1
    fi
    if [ ! -s "$STATE/appreg-before-kiosk.db" ]; then
        db ".backup '$STATE/appreg-before-kiosk.db'" || return 1
    fi
    db "BEGIN; INSERT OR IGNORE INTO handlerIds(handlerId) VALUES('$APP_ID'); DELETE FROM properties WHERE handlerId='$APP_ID' AND name IN ('command','unloadPolicy','framework','run'); INSERT INTO properties(handlerId,name,value) VALUES('$APP_ID','command','$COMMAND'); INSERT INTO properties(handlerId,name,value) VALUES('$APP_ID','unloadPolicy','unloadOnPause'); INSERT INTO properties(handlerId,name,value) VALUES('$APP_ID','framework',''); INSERT INTO properties(handlerId,name,value) VALUES('$APP_ID','run','$RUN'); COMMIT;" || return 1
    printf '1\n' > "$STATE/native-registered"
    echo 'Separate native web starter registered.'
}
unregister_native() {
    [ -f "$STATE/native-registered" ] || return 0
    db "BEGIN; DELETE FROM properties WHERE handlerId='$APP_ID'; DELETE FROM handlerIds WHERE handlerId='$APP_ID'; COMMIT;" || return 1
    rm -f "$STATE/native-registered"
    echo 'Separate native web starter unregistered.'
}
capture_runtime() {
    echo "Collecting filtered application log"
    {
        date
        echo 'Registered starter:'
        db "SELECT name,value FROM properties WHERE handlerId='$APP_ID';"
        echo 'Runtime processes:'
        ps | grep '[m]esquite'
        echo 'Application system log:'
        if command -v showlog >/dev/null 2>&1; then
            showlog 2>/dev/null | grep -i -e kindlekiosk -e mesquite -e 'appmgr.*fail' -e 'appmgr.*error' | tail -n 120
        elif [ -r /var/log/messages ]; then
            grep -i -e kindlekiosk -e mesquite -e 'appmgr.*fail' -e 'appmgr.*error' /var/log/messages | tail -n 120
        else
            echo 'No readable application system log'
        fi
    } > "$ROOT/runtime-diagnostic.log" 2>&1
}
case "$1" in
    browser)
        restore_config || exit 1
        lipc-set-prop com.lab126.appmgrd stop "$APP_ID" 2>/dev/null || true
        lipc-set-prop com.lab126.appmgrd stop com.lab126.browser 2>/dev/null || true
        sleep 1
        lipc-set-prop com.lab126.appmgrd start "app://com.lab126.browser/?view=$URL"
        ;;
    fullscreen)
        sh "$ROOT/kiosk.sh" _fullscreen || exit 1
        # Keep the proven foreground observer alive; no nohup dependency.
        sh "$ROOT/touch-light.sh" run
        RESULT=$?
        echo "Permanent touch observer ended: $RESULT"
        if [ "$RESULT" -eq 0 ] && [ -d "$ROOT" ]; then
            sh "$ROOT/kiosk.sh" home
        fi
        exit "$RESULT"
        ;;
    _fullscreen)
        restore_config || exit 1
        "$ROOT/tools/kiosk-http-get" --version > "$STATE/http-runtime.log" 2>&1 || { echo 'HTTP runtime cannot start'; exit 1; }
        CONTROLLER=$(cat "$ROOT/controller-id.txt" 2>/dev/null)
        STATUS_URL="${URL%/}/kiosk-status"
        if [ -n "$CONTROLLER" ]; then
            case "$CONTROLLER" in *[!a-f0-9]*) echo 'Invalid device ID'; exit 1;; esac
            [ "${#CONTROLLER}" -eq 32 ] || exit 1
            STATUS_URL="$STATUS_URL?controller=$CONTROLLER"
        fi
        BASE=$("$ROOT/tools/kiosk-http-get" "$STATUS_URL") || { echo 'Cannot initialize exit button'; exit 1; }
        case "$BASE" in ''|*[!0-9]*) echo 'Invalid exit status'; exit 1;; esac
        printf '%s\n' "$BASE" > "$STATE/exit-generation"
        if [ -n "$CONTROLLER" ]; then
            REFRESH_BASE=$("$ROOT/tools/kiosk-http-get" "${URL%/}/kiosk-refresh?controller=$CONTROLLER" 2>/dev/null)
            case "$REFRESH_BASE" in ''|*[!0-9]*) rm -f "$STATE/refresh-generation";; *) printf '%s\n' "$REFRESH_BASE" > "$STATE/refresh-generation";; esac
        fi
        register_native || exit 1
        OLD=$(lipc-get-prop com.lab126.powerd preventScreenSaver 2>/dev/null)
        case "$OLD" in 0|1) printf '%s\n' "$OLD" > "$STATE/prevent-screensaver";; *) echo 'Cannot read power state'; exit 1;; esac
        lipc-set-prop com.lab126.powerd preventScreenSaver 1 || exit 1
        lipc-set-prop com.lab126.appmgrd stop com.lab126.browser 2>/dev/null || true
        lipc-set-prop com.lab126.appmgrd stop "$APP_ID" 2>/dev/null || true
        sleep 1
        lipc-set-prop com.lab126.appmgrd start "app://$APP_ID"
        RESULT=$?
        echo "Native content-window launch result: $RESULT"
        exit "$RESULT"
        ;;
    home)
        # Stop the observer before the app, avoiding a second automatic Home action.
        restore_config || exit 1
        lipc-set-prop com.lab126.appmgrd stop "$APP_ID" 2>/dev/null || true
        sleep 1
        lipc-set-prop com.lab126.appmgrd start 'app://com.lab126.booklet.home/?context=0'
        RESULT=$?
        echo "Return to Home result: $RESULT"
        # Optional registry cleanup must never block returning to Home.
        if [ "$RESULT" -eq 0 ]; then
            unregister_native || echo 'Application registry busy; registration retained for the next launch.'
        fi
        exit "$RESULT"
        ;;
    diagnose)
        capture_runtime
        echo 'Firmware:'; cat /mnt/us/system/version.txt
        echo 'Browser config:'; ls -l "$CFG"
        echo 'Saved browser view mode:'; grep 'viewmodes=' "$CFG"
        echo 'Native runtime:'; ls -l /usr/bin/mesquite
        echo 'Application registry:'; ls -l "$APPREG"
        echo 'SQLite runtime:'; "$SQLITE" -version
        echo 'Power state:'; lipc-get-prop com.lab126.powerd preventScreenSaver
        ;;
    *) echo 'Unknown action'; exit 1;;
esac
