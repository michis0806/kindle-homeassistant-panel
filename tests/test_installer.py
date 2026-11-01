import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('installer',Path(__file__).resolve().parents[1]/'scripts/install_kindle.py')
installer=importlib.util.module_from_spec(spec);spec.loader.exec_module(installer)

class InstallerTests(unittest.TestCase):
    def test_independent_ids_preserved_on_upgrade_and_runtime_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);runtime=root/'tools';runtime.mkdir();files=[]
            for name in ('bin/sqlite3','bin/evtest','kiosk-http/bin/curl','sqlite3','kiosk-http-get'):
                target=runtime/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b'fixture')
                files.append({'path':name,'sha256':hashlib.sha256(b'fixture').hexdigest()})
            (runtime/'manifest.json').write_text(json.dumps({'files':files}))
            original_root=installer.ROOT
            # Backups belong in the test's temporary directory; retain source tree via a symlink.
            (root/'kindle').symlink_to(original_root/'kindle',target_is_directory=True)
            with patch.object(installer,'ROOT',root):
                a=installer.install('http://example.test:8098',runtime,root/'a')
                b=installer.install('http://example.test:8098',runtime,root/'b')
                self.assertNotEqual(a,b)
                self.assertEqual(a,installer.install('http://example.test:8098',runtime,root/'a'))
                self.assertIn(a,(root/'a/web/settings.js').read_text())
                self.assertIn(b,(root/'b/web/settings.js').read_text())
                (root/'a/state').mkdir();(root/'a/state/light-original').write_text('22')
                with self.assertRaises(ValueError):installer.install('http://example.test:8098',runtime,root/'a')
                (runtime/'bin/evtest').write_bytes(b'corrupted')
                with self.assertRaises(ValueError):installer.install('http://example.test:8098',runtime,root/'c')
    def test_rejects_credentials_and_unexpected_paths(self):
        for url in ('http://user:password@example.test','http://example.test/path','http://example.test/?token=private'):
            with self.assertRaises(ValueError):installer.install(url,Path('/nonexistent'),Path('/nonexistent'))

if __name__=='__main__':unittest.main()
