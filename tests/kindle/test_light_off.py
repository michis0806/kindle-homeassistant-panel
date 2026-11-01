from pathlib import Path
import tempfile,subprocess,os
source=(Path(__file__).resolve().parents[2] / 'kindle/HAKiosk/light-off-test.sh').read_text()
for style in ('numeric','labelled','unexpected'):
 for failure in (False,True):
  with tempfile.TemporaryDirectory(prefix='kindle-full-off-format-') as tmp:
    root=Path(tmp);(root/'bin').mkdir();(root/'driver').write_text('173\n');(root/'level').write_text('22\n')
    script=root/'light-off-test.sh';script.write_text(source.replace('ROOT=/mnt/us/extensions/HAKiosk','ROOT='+tmp).replace('HW=/sys/devices/system/fl_tps6116x/fl_tps6116x0/fl_intensity','HW='+str(root/'driver')))
    (root/'kiosk.sh').write_text('#!/bin/sh\ntest "$1" = home\n')
    commands={'cat':'''if [ "$1" = "$TEST_ROOT/driver" ]; then
 case "$TEST_STYLE" in
 labelled) printf 'FrontLight(Intensity) = %s\\n' "$(/bin/cat "$1")"; exit 0;;
 unexpected) echo 'unexpected data 173'; exit 0;;
 esac
fi
exec /bin/cat "$@"''',
    'lipc-get-prop':'/bin/cat "$TEST_ROOT/level"',
    'lipc-set-prop':'printf "%s\\n" "$3" >> "$TEST_ROOT/requests"\nif [ "$TEST_FAILURE" = yes ] && [ "$3" = 0 ]; then exit 1; fi\nprintf "%s\\n" "$3" > "$TEST_ROOT/level"',
    'sleep':'if [ "$1" = 2 ]; then exit 0; fi; test "$1" = 5 && test "$(/bin/cat "$TEST_ROOT/driver")" = 0 && test "$(/bin/cat "$TEST_ROOT/level")" = 0'}
    for name,body in commands.items():
      p=root/'bin'/name;p.write_text('#!/bin/sh\n'+body+'\n');p.chmod(0o755)
    env=dict(os.environ,TEST_ROOT=tmp,TEST_STYLE=style,TEST_FAILURE='yes' if failure else 'no',PATH=str(root/'bin')+':'+os.environ['PATH'])
    r=subprocess.run(['sh',str(script),'test'],env=env)
    assert r.returncode==(1 if failure or style=='unexpected' else 0),(style,failure,(root/'light-off-test.log').read_text())
    assert (root/'level').read_text().strip()=='22'
    assert (root/'driver').read_text().strip()=='173'
    assert not (root/'state/full-off-test/level').exists()
    assert not (root/'state/full-off-test/hardware').exists()
    if style=='unexpected':assert not (root/'requests').exists()
    print(style, 'setter failure' if failure else 'normal', ': passed')
