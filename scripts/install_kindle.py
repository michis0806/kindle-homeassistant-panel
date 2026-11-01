#!/usr/bin/env python3
"""Prepare one Kindle's KUAL extension with an independent public controller ID."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import uuid
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]


def install(url, runtime, destination, volume=False, new_device_id=False):
    parsed=urlsplit(url)
    if parsed.scheme!='http' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('','/'):
        raise ValueError('Use a plain local HTTP origin, e.g. http://homeassistant.local:8098')
    # Validate port and restrict characters also interpreted by the Kindle's shell/browser.
    if not re.fullmatch(r'http://[a-zA-Z0-9.\-\[\]:]+/?',url) or parsed.port==0:
        raise ValueError('Invalid server address')
    url=url.rstrip('/')
    destination=Path(destination);runtime=Path(runtime)
    if volume:
        version=destination/'system/version.txt'
        if not version.is_file() or '5.6.1.1' not in version.read_text():
            raise ValueError('Only the tested PW1 firmware 5.6.1.1 is supported by this installer')
        if not (destination/'extensions').is_dir():raise ValueError('Install KUAL first')
        destination=destination/'extensions/HAKiosk'
    # A running observer must exit cleanly before USB mounting/upgrading.
    for name in ('touch-light.pid','light-original','light-original-hardware','prevent-screensaver'):
        if (destination/'state'/name).exists():
            raise ValueError('Exit the kiosk via its crossed-out HA icon before upgrading; saved runtime state exists')
    manifest=json.loads((runtime/'manifest.json').read_text())
    for entry in manifest['files']:
        path=Path(entry['path'])
        if path.is_absolute() or '..' in path.parts:raise ValueError('Invalid runtime path')
        if hashlib.sha256((runtime/path).read_bytes()).hexdigest()!=entry['sha256']:
            raise ValueError('Runtime checksum mismatch: '+str(path))
    for required in ('bin/sqlite3','bin/evtest','kiosk-http/bin/curl','sqlite3','kiosk-http-get'):
        if not (runtime/required).is_file():raise ValueError('Incomplete runtime: '+required)
    identity=destination/'controller-id.txt'
    controller=identity.read_text().strip() if identity.exists() and not new_device_id else uuid.uuid4().hex
    if not re.fullmatch('[a-f0-9]{32}',controller):raise ValueError('Invalid saved device ID')
    if destination.exists():
        stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        backup=ROOT/'.local/backups'/stamp
        backup.parent.mkdir(parents=True,exist_ok=True)
        shutil.copytree(destination,backup)
        print('Previous extension backed up locally:',backup)
    shutil.copytree(ROOT/'kindle/HAKiosk',destination,dirs_exist_ok=True)
    shutil.copytree(runtime,destination/'tools',dirs_exist_ok=True)
    (destination/'url.txt').write_text(url+'\n')
    identity.write_text(controller+'\n')
    (destination/'web/settings.js').write_text('var KIOSK_URL = '+json.dumps(url+'/?controller='+controller)+';\n')
    for path in destination.rglob('*'):
        if path.is_file() and (path.suffix=='.sh' or 'tools' in path.parts):path.chmod(0o755)
    print('Prepared one Kindle:',destination)
    return controller

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',required=True)
    parser.add_argument('--runtime',type=Path,default=ROOT/'.runtime/HAKiosk/tools')
    target=parser.add_mutually_exclusive_group(required=True)
    target.add_argument('--volume',type=Path,help='Mounted, jailbroken PW1 with KUAL')
    target.add_argument('--output',type=Path,help='Create a staging extension without touching a Kindle')
    parser.add_argument('--new-device-id',action='store_true',help='Generate a new identity when preparing a cloned extension')
    args=parser.parse_args()
    install(args.url,args.runtime,args.volume or args.output,bool(args.volume),args.new_device_id)
