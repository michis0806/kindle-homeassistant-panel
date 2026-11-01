from pathlib import Path
import tempfile,subprocess,os,sys,time
source=(Path(__file__).resolve().parents[2] / 'kindle/HAKiosk/touch-light.sh').read_text()
with tempfile.TemporaryDirectory(prefix='kindle-auto-full-off-') as tmp:
    root=Path(tmp);(root/'state').mkdir();(root/'tools/bin').mkdir(parents=True);(root/'bin').mkdir()
    (root/'driver').write_text('196\n');(root/'level').write_text('22\n');(root/'power').write_text('1\n');(root/'state/prevent-screensaver').write_text('0\n');(root/'state/exit-generation').write_text('0\n');(root/'generation').write_text('0\n');(root/'url.txt').write_text('http://example.test\n')
    s=source.replace('ROOT=/mnt/us/extensions/HAKiosk','ROOT='+tmp).replace('INPUT=/dev/input/event0','INPUT=/dev/null').replace('IDLE_SECONDS=30','IDLE_SECONDS=2').replace('HW=/sys/devices/system/fl_tps6116x/fl_tps6116x0/fl_intensity','HW='+str(root/'driver')).replace('    read UP REST < /proc/uptime || return 1\n    NOW=${UP%%.*}','    NOW=$(date +%s)')
    start=s.index('    for PROC in /proc/');end=s.index('    [ -n "$APP_PID" ]',start);s=s[:start]+'    APP_PID=$TEST_APP_PID\n'+s[end:]
    s=s.replace('if [ ! -r "/proc/$PID/cmdline" ]; then','if ! kill -0 "$PID" 2>/dev/null; then').replace('CMD=$(tr \'\\000\' \' \' < "/proc/$PID/cmdline")','CMD="$ROOT/touch-light.sh run"')
    script=root/'touch-light.sh';script.write_text(s)
    reader=root/'tools/bin/evtest';reader.write_text('#!'+sys.executable+'''\nimport time,os
from pathlib import Path
root=Path(os.environ['TEST_ROOT'])
print('Input device: simulation',flush=True)
time.sleep(3.3)
(root/'observed-off').write_text((root/'driver').read_text())
print('Event: time 0, type 3 (EV_ABS), code 53 (ABS_MT_POSITION_X), value 100',flush=True)
while True:time.sleep(1)
''');reader.chmod(0o755)
    (root/'tools/kiosk-http-get').write_text('#!/bin/sh\ncat \"$TEST_ROOT/generation\"\n');(root/'tools/kiosk-http-get').chmod(0o755)
    commands={'cat':'''if [ "$1" = "$TEST_ROOT/driver" ]; then printf 'FrontLight(Intensity) = %s\\n' "$(/bin/cat "$1")"; else exec /bin/cat "$@"; fi''',
    'lipc-get-prop':'/bin/cat "$TEST_ROOT/level"',
    'lipc-set-prop':'''if [ "$2" = preventScreenSaver ]; then printf '%s\\n' "$3" > "$TEST_ROOT/power"; else
printf '%s\\n' "$3" > "$TEST_ROOT/level"
printf '%s\\n' "$3" >> "$TEST_ROOT/requests"
# Emulate PW1: ordinary level0 still leaves driver1; level22 maps to196.
if [ "$3" = 0 ]; then echo 1 > "$TEST_ROOT/driver"; else echo 196 > "$TEST_ROOT/driver"; fi
fi'''}
    for name,body in commands.items():
        p=root/'bin'/name;p.write_text('#!/bin/sh\n'+body+'\n');p.chmod(0o755)
    env=dict(os.environ,TEST_ROOT=tmp,TEST_APP_PID=str(os.getpid()),PATH=str(root/'bin')+':'+os.environ['PATH'])
    worker=subprocess.Popen(['sh',str(script),'run'],env=env)
    try:
        time.sleep(5)
        assert worker.poll() is None,(root/'touch-light.log').read_text()
        assert (root/'observed-off').read_text().strip()=='0','Driver must be fully off before touch'
        assert (root/'driver').read_text().strip()=='196','Touch must restore brightness'
        (root/'generation').write_text('1\n');worker.wait(timeout=8)
        assert worker.returncode==0
        assert 'Visible exit button requested Home' in (root/'touch-light.log').read_text()
        assert (root/'level').read_text().strip()=='22'
        assert (root/'driver').read_text().strip()=='196'
        assert (root/'power').read_text().strip()=='0'
        assert not (root/'state/light-original-hardware').exists()
        assert not (root/'state/light-original').exists()
        assert not (root/'state/touch-light.pid').exists()
        print('Passed: new exit counter stops observer and restores software22/hardware196/power0 after full-off and touch.')
    finally:
        if worker.poll() is None:worker.terminate();worker.wait(timeout=5)
