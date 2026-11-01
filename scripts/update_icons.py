#!/usr/bin/env python3
"""Regenerate the bundled MDI SVG paths from the pinned upstream npm package."""
import base64
import hashlib
import html
import io
import json
from pathlib import Path
import tarfile
import urllib.request
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
VERSION='7.4.47'

def generate():
    with urllib.request.urlopen('https://registry.npmjs.org/@mdi/svg/'+VERSION,timeout=30) as response:metadata=json.load(response)
    with urllib.request.urlopen(metadata['dist']['tarball'],timeout=60) as response:data=response.read()
    integrity='sha512-'+base64.b64encode(hashlib.sha512(data).digest()).decode()
    if integrity!=metadata['dist']['integrity']:raise ValueError('Upstream archive integrity mismatch')
    icons={}
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        for member in tar.getmembers():
            if not member.isfile() or not member.name.startswith('package/svg/') or not member.name.endswith('.svg'):continue
            svg=ET.fromstring(tar.extractfile(member).read())
            paths=[path.get('d') for path in svg.iter('{http://www.w3.org/2000/svg}path') if path.get('d')]
            if paths:icons['mdi:'+Path(member.name).stem]=''.join('<path fill="currentColor" d="'+html.escape(path,quote=True)+'"/>' for path in paths)
    assert len(icons)>7000
    (ROOT/'kindle_panel/mdi-icons.json').write_text(json.dumps(icons,sort_keys=True,separators=(',',':'))+'\n')
    (ROOT/'kindle_panel/mdi-icons-source.json').write_text(json.dumps({'package':'@mdi/svg','version':VERSION,'url':metadata['dist']['tarball'],'integrity':integrity,'sha256':hashlib.sha256(data).hexdigest(),'count':len(icons)},indent=2)+'\n')
    print('Generated',len(icons),'upstream MDI icons')

if __name__=='__main__':generate()
