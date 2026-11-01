from pathlib import Path
import os
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]

class HomeRecoveryTests(unittest.TestCase):
    def test_locked_registry_does_not_block_home(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'state').mkdir();(root/'tools').mkdir();(root/'bin').mkdir()
            (root/'url.txt').write_text('http://example.test:8098\n');(root/'state/native-registered').write_text('1')
            source=(ROOT/'kindle/HAKiosk/kiosk.sh').read_text().replace('ROOT=/mnt/us/extensions/HAKiosk','ROOT='+tmp)
            script=root/'kiosk.sh';script.write_text(source)
            def command(path,body):path.write_text('#!/bin/sh\n'+body+'\n');path.chmod(0o755)
            command(root/'touch-light.sh','exit 0')
            command(root/'bin/sleep','exit 0')
            command(root/'bin/lipc-set-prop','echo "$*" >> "$TEST_ROOT/events"')
            command(root/'tools/sqlite3','cat > "$TEST_ROOT/sql-input"\necho "db cleanup" >> "$TEST_ROOT/events"\necho "Error: database is locked" >&2\nexit 1')
            result=subprocess.run(['sh',str(script),'home'],env=dict(os.environ,TEST_ROOT=tmp,PATH=str(root/'bin')+':'+os.environ['PATH']))
            self.assertEqual(result.returncode,0)
            events=(root/'events').read_text()
            self.assertLess(events.index('start app://com.lab126.booklet.home'),events.index('db cleanup'))
            self.assertTrue((root/'sql-input').read_text().startswith('.timeout 5000\n'))
            self.assertTrue((root/'state/native-registered').exists(),'Retain registration for retry')

if __name__=='__main__':unittest.main()
