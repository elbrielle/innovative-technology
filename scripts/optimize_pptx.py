#!/usr/bin/env python3
"""Conservative PPTX media optimization. Writes a new file; never edits the source.

Preserves image pixel dimensions, all slide XML, fonts, animations, and notes.
PNG is losslessly optimized by default. --jpeg-part permits an explicitly reviewed opaque PNG conversion
at quality 98, 4:4:4, only if pixel error and file-size checks pass. Render and
review before publishing. --protect-slide also pins its direct image bytes.
"""
import argparse, hashlib, io, json, math, posixpath, re, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from PIL import Image, ImageChops, ImageStat

REL='http://schemas.openxmlformats.org/package/2006/relationships'
def sha(b): return hashlib.sha256(b).hexdigest()
def target(part, value):
    base='' if part=='_rels/.rels' else part.replace('/_rels/','/').removesuffix('.rels')
    return value.lstrip('/') if value.startswith('/') else posixpath.normpath(posixpath.join(posixpath.dirname(base),value))
def reltargets(part,b):
    return [(r.get('Target'),target(part,r.get('Target'))) for r in ET.fromstring(b) if r.get('TargetMode')!='External' and r.get('Target')]
def optimize(source,output,jpeg_parts=(),protect_slides=()):
    source,output=Path(source),Path(output)
    if output.exists() or source.resolve()==output.resolve(): raise ValueError('Choose a new output path')
    with zipfile.ZipFile(source) as z:
        if z.testzip(): raise ValueError('Invalid source ZIP')
        entries={i.filename:z.read(i) for i in z.infolist()}
        if len(entries)!=len(z.infolist()):raise ValueError('Duplicate ZIP entries')
        if any(n.startswith('_xmlsignatures/') or n.endswith('vbaProject.bin') for n in entries):raise ValueError('Signed or macro-enabled package requires manual handling')
    missing=set(jpeg_parts)-set(entries)
    if missing:raise ValueError('Unknown reviewed JPEG parts: '+str(missing))
    protected=set()
    for n in protect_slides:
        slide=f'ppt/slides/slide{n}.xml'; rel=f'ppt/slides/_rels/slide{n}.xml.rels'
        if slide not in entries: raise ValueError(f'Missing protected slide {n}')
        protected.add(slide)
        if rel in entries:
            protected.add(rel);protected.update(t for _,t in reltargets(rel,entries[rel]) if t.startswith('ppt/media/'))
    changed=[];rename={};updated=dict(entries)
    for name,original in entries.items():
        if not name.startswith('ppt/media/') or not name.lower().endswith('.png') or name in protected: continue
        im=Image.open(io.BytesIO(original));im.load()
        if getattr(im,'n_frames',1)!=1:continue
        # Color-managed images retain their profile; unhandled metadata is held.
        if any(k in im.info for k in ['gamma','chromaticity','exif','srgb','cicp']):continue
        buf=io.BytesIO();kwargs={'icc_profile':im.info['icc_profile']} if 'icc_profile' in im.info else {}
        im.save(buf,format='PNG',optimize=True,**kwargs);best=buf.getvalue();method='lossless PNG';psnr=None
        if Image.open(io.BytesIO(best)).convert('RGBA').tobytes()!=im.convert('RGBA').tobytes(): raise AssertionError('PNG pixel change')
        opaque=im.convert('RGBA').getchannel('A').getextrema()==(255,255)
        if name in jpeg_parts and opaque and len(original)>100_000 and 'icc_profile' not in im.info:
            rgb=im.convert('RGB');j=io.BytesIO();rgb.save(j,format='JPEG',quality=98,subsampling=0,optimize=True)
            decoded=Image.open(io.BytesIO(j.getvalue())).convert('RGB');diff=ImageChops.difference(rgb,decoded);stats=ImageStat.Stat(diff)
            mse=sum(v*v for v in stats.rms)/3;score=99 if mse==0 else 10*math.log10(255*255/mse)
            # Retain all pixels and full chroma; do not accept a token saving.
            if score>=45 and max(stats.mean)<=0.8 and len(j.getvalue())<len(best)*0.8:
                best=j.getvalue();method='JPEG 98 4:4:4';psnr=score
        if len(best)>=len(original)*0.95: continue
        if method.startswith('JPEG'):
            new=name.rsplit('.',1)[0]+'-optimized.jpg'
            if new in entries:raise ValueError('Output media name collision')
            rename[name]=new;updated.pop(name);updated[new]=best
        else:updated[name]=best
        changed.append({'part':name,'output_part':rename.get(name,name),'method':method,'before':len(original),'after':len(best),'width':im.width,'height':im.height,'psnr_db':psnr})
    # Repoint exact duplicate media without changing slide/notes XML.
    canonical={};duplicates=[]
    for name in sorted((n for n in updated if n.startswith('ppt/media/')),key=lambda n:(n not in protected,n)):
        key=(Path(name).suffix.lower(),sha(updated[name]))
        if key in canonical and name not in protected:
            rename[name]=canonical[key];duplicates.append({'part':name,'canonical':canonical[key],'bytes':len(updated[name])});updated.pop(name)
        else:canonical[key]=name
    for name,b in entries.items():
        if not name.endswith('.rels'):continue
        out=b
        for original,resolved in reltargets(name,b):
            dest=rename.get(resolved)
            if not dest:continue
            while dest in rename:dest=rename[dest]
            if name in protected:raise AssertionError('Protected relationships would change')
            base=name.replace('/_rels/','/').removesuffix('.rels')
            replacement='/'+dest if original.startswith('/') else posixpath.relpath(dest,posixpath.dirname(base))
            old=('Target="'+original+'"').encode();new=('Target="'+replacement+'"').encode()
            if old not in out:raise ValueError('Unsupported relationship serialization')
            out=out.replace(old,new)
        updated[name]=out
    if rename:
        ct=ET.fromstring(updated['[Content_Types].xml'])
        ns=ct.tag.removesuffix('Types')
        if any(x['method'].startswith('JPEG') for x in changed) and not any(e.get('Extension')=='jpg' for e in ct):
            ET.SubElement(ct,ns+'Default',{'Extension':'jpg','ContentType':'image/jpeg'})
        for e in list(ct):
            if e.tag==ns+'Override' and e.get('PartName','').lstrip('/') not in updated:ct.remove(e)
        ET.register_namespace('',ns[1:-1])
        updated['[Content_Types].xml']=ET.tostring(ct,encoding='utf-8',xml_declaration=True)
    ct=ET.fromstring(updated['[Content_Types].xml'])
    defaults={e.get('Extension'):e.get('ContentType') for e in ct if e.tag.endswith('Default')}
    overrides={e.get('PartName','').lstrip('/'):e.get('ContentType') for e in ct if e.tag.endswith('Override')}
    for name in updated:
        if not name.endswith('/') and name!='[Content_Types].xml' and name not in overrides and name.rsplit('.',1)[-1] not in defaults:
            raise ValueError('Missing content type: '+name)
    for name in protected:assert updated[name]==entries[name]
    for name,b in entries.items():
        if name not in rename and not name.startswith('ppt/media/') and not name.endswith('.rels') and name!='[Content_Types].xml':assert updated[name]==b
    for name,b in updated.items():
        if name.endswith('.rels'):
            for _,t in reltargets(name,b):
                if t not in updated:raise ValueError('Missing relationship target: '+t)
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,b in updated.items():z.writestr(name,b)
    report={'source':str(source.resolve()),'output':str(output.resolve()),'source_sha256':sha(source.read_bytes()),'output_sha256':sha(output.read_bytes()),'before':source.stat().st_size,'after':output.stat().st_size,'protected_parts':sorted(protected),'pixel_dimensions_preserved':True,'slide_xml_notes_fonts_unchanged':True,'images':changed,'duplicates':duplicates}
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source');p.add_argument('output');p.add_argument('--jpeg-part',action='append',default=[]);p.add_argument('--protect-slide',type=int,action='append',default=[]);p.add_argument('--report',required=True);a=p.parse_args()
    r=optimize(a.source,a.output,a.jpeg_part,a.protect_slide);Path(a.report).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ['before','after','pixel_dimensions_preserved','slide_xml_notes_fonts_unchanged']}))
