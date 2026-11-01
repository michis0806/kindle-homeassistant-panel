#!/usr/bin/env python3
"""Build a verified PW1 runtime. Never installs USB networking or firmware."""
import argparse, hashlib, io, json, re, struct, tarfile, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def elf_info(data):
    assert data[:6]==b'\x7fELF\x01\x01','Expected 32-bit little-endian ELF'
    assert struct.unpack_from('<H',data,18)[0]==40,'Expected ARM machine'
    offset=struct.unpack_from('<I',data,28)[0];size,count=struct.unpack_from('<HH',data,42)
    programs=[struct.unpack_from('<IIIIIIII',data,offset+i*size) for i in range(count)]
    dynamic=next((p for p in programs if p[0]==2),None);tags=[]
    if dynamic:
        for pos in range(dynamic[1],dynamic[1]+dynamic[4],8):
            tag,value=struct.unpack_from('<iI',data,pos)
            if tag==0:break
            tags.append((tag,value))
    string_addr=next((value for tag,value in tags if tag==5),None)
    def string(index):
        segment=next(p for p in programs if p[0]==1 and p[2]<=string_addr<p[2]+p[4]);pos=segment[1]+string_addr-segment[2]+index
        return data[pos:data.index(b'\0',pos)].decode()
    interpreter=next((data[p[1]:p[1]+p[4]].rstrip(b'\0').decode() for p in programs if p[0]==3),None)
    return {'needed':[string(value) for tag,value in tags if tag==1],'soname':next((string(value) for tag,value in tags if tag==14),None),'interpreter':interpreter,'glibc_versions':sorted(set(x.decode() for x in re.findall(rb'GLIBC_[0-9.]+',data)))}

def ar_data(data):
    if data[:8]!=b'!<arch>\n':raise ValueError('Invalid Debian archive')
    offset=8
    while offset+60<=len(data):
        header=data[offset:offset+60];size=int(header[48:58]);name=header[:16].decode().strip().rstrip('/')
        offset+=60;body=data[offset:offset+size];offset+=size+(size%2)
        if name.startswith('data.tar'):return body
    raise ValueError('No data tarball')

def verify(data, expected):
    if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('Archive checksum mismatch')
    return data

def build(usbnet, output, cache):
    sources=json.loads((ROOT/'runtime-sources.json').read_text())
    output.mkdir(parents=True,exist_ok=True);cache.mkdir(parents=True,exist_ok=True)
    files=[]
    def write(name, data):
        target=output/name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data);target.chmod(0o755)
        files.append({'path':name,'sha256':hashlib.sha256(data).hexdigest()})
    for package in sources['debian_packages']:
        archive=cache/package['url'].rsplit('/',1)[-1]
        if not archive.exists():
            with urllib.request.urlopen(package['url'],timeout=60) as response:data=response.read()
            verify(data,package['sha256']);archive.write_bytes(data)
        data=verify(archive.read_bytes(),package['sha256'])
        with tarfile.open(fileobj=io.BytesIO(ar_data(data))) as tar:
            for item in tar.getmembers():
                if not item.isfile():continue
                name=Path(item.name).name
                binary=item.name.endswith('/usr/bin/sqlite3')
                library=any(name.startswith(prefix) for prefix in ('libsqlite3.so.','libreadline.so.','libncurses.so.','libgcc_s.so.'))
                if binary or library:
                    content=tar.extractfile(item).read();info=elf_info(content)
                    write(('bin/' if binary else 'lib/')+name,content)
                    if info['soname']:write('lib/'+info['soname'],content)
                elif item.name.endswith('/copyright'):
                    write('licenses/'+package['name']+'-copyright.txt',tar.extractfile(item).read())
    data=verify(usbnet.read_bytes(),sources['usbnet']['sha256'])
    with tarfile.open(fileobj=io.BytesIO(data)) as tar:
        prefix='USBNetwork/src/usbnet/'
        def read(name):return tar.extractfile(prefix+name).read()
        write('bin/evtest',read('bin/evtest'))
        write('kiosk-http/bin/curl',read('bin/curl'))
        pending=list(elf_info(read('bin/curl'))['needed']);done=set()
        system={'libc.so.6','libdl.so.2','libm.so.6','librt.so.1','libpthread.so.0','ld-linux.so.3'}
        while pending:
            name=pending.pop()
            if name in system or name in done:continue
            if '/' in name:raise ValueError('Unexpected library path')
            content=read('lib/'+name);write('kiosk-http/lib/'+name,content)
            done.add(name);pending.extend(elf_info(content)['needed'])
        for name in ('USBNetwork/WHERE_ARE_THE_SOURCES.txt',):
            write('licenses/'+Path(name).name,tar.extractfile(name).read())
    for name in ('sqlite3','kiosk-http-get'):
        write(name,(ROOT/'kindle/HAKiosk/tools'/name).read_bytes())
    (output/'manifest.json').write_text(json.dumps({'sources':sources,'files':files},indent=2)+'\n')
    print('Prepared verified runtime:',output)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--usbnet-archive',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'.runtime/HAKiosk/tools')
    parser.add_argument('--cache',type=Path,default=ROOT/'downloads')
    args=parser.parse_args();build(args.usbnet_archive,args.output,args.cache)
