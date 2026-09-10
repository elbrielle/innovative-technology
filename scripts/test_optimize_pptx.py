"""Regression checks: namespace-safe types, duplicate-media types, protection."""
import tempfile,zipfile,io
from pathlib import Path
from xml.etree import ElementTree as ET
from PIL import Image
from optimize_pptx import optimize

def main():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d);buf=io.BytesIO();Image.new('RGB',(900,900),(45,100,200)).save(buf,format='PNG')
        media=buf.getvalue()
        entries={'ppt/':b'','ppt/slides/':b'','[Content_Types].xml':b'<x:Types xmlns:x="http://schemas.openxmlformats.org/package/2006/content-types"><x:Default Extension="xml" ContentType="application/xml"/><x:Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><x:Override PartName="/ppt/media/a.png" ContentType="image/png"/><x:Override PartName="/ppt/media/b.png" ContentType="image/png"/></x:Types>','ppt/slides/slide1.xml':b'<slide/>','ppt/slides/_rels/slide1.xml.rels':b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="r1" Target="../media/a.png" Type="image"/><Relationship Id="r2" Target="../media/b.png" Type="image"/></Relationships>','ppt/media/a.png':media,'ppt/media/b.png':media}
        src=p/'source.pptx'
        with zipfile.ZipFile(src,'w') as z:
            for n,b in entries.items():z.writestr(n,b)
        optimize(src,p/'dedup.pptx')
        with zipfile.ZipFile(p/'dedup.pptx') as z:
            ct=ET.fromstring(z.read('[Content_Types].xml'));assert all(e.get('PartName','').lstrip('/') in z.namelist() for e in ct if e.tag.endswith('Override'))
        r=optimize(src,p/'protected.pptx',['ppt/media/a.png'],[1]);assert not r['images'] and not r['duplicates']
        with zipfile.ZipFile(p/'protected.pptx') as z:
            for n in entries:assert z.read(n)==entries[n]
    # A deterministic smooth texture exercises JPEG conversion without a live
    # curriculum asset or silently skipping when Canvas assigns a new file ID.
    import random
    with tempfile.TemporaryDirectory() as d:
        p=Path(d);rng=random.Random(7)
        texture=Image.frombytes('L',(128,128),bytes(rng.randrange(256) for _ in range(128*128)))
        texture=texture.resize((900,900),Image.Resampling.BICUBIC).convert('RGB')
        buf=io.BytesIO();texture.save(buf,format='PNG');parts=dict(entries)
        parts['ppt/media/a.png']=buf.getvalue();parts['ppt/media/b.png']=buf.getvalue()
        with zipfile.ZipFile(p/'prefixed.pptx','w',zipfile.ZIP_DEFLATED) as z:
            for n,b in parts.items():z.writestr(n,b)
        r=optimize(p/'prefixed.pptx',p/'jpeg.pptx',['ppt/media/a.png'])
        assert any(i['method'].startswith('JPEG') for i in r['images'])
        with zipfile.ZipFile(p/'jpeg.pptx') as z:
            ct=ET.fromstring(z.read('[Content_Types].xml'))
            assert any(e.get('Extension')=='jpg' and e.get('ContentType')=='image/jpeg' for e in ct)
            assert b'<Types ' in z.read('[Content_Types].xml')
    print('PASS: JPEG with prefixed content types, duplicate overrides, protected bytes')
if __name__=='__main__':main()
