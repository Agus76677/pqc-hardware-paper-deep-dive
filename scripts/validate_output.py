#!/usr/bin/env python3
"""Validate authored HTML, evidence registration, decoded assets and current PDF."""
from __future__ import annotations
import argparse, json, re, xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from paper_common import ToolError,contained_path,read_json_yaml,input_fingerprint,file_hash
from render_references import parse_bib

MAIN_SECTIONS=['论文概述','背景与相关工作','问题定义','方法','实验','方法分析','局限性','启发与研究思考','资料来源']
VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}

class HTMLInventory(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.assets=set(); self.images=set(); self.citations=[]; self.meta={}; self.headings=[]
        self.ids=set(); self.hrefs=[]; self.errors=[]; self.stack=[]; self.lang=''; self.title_text=''
        self.blocks=[]; self.current_block=None; self.main_depth=0; self.title_depth=0; self.h2=None
        self.roots={'html':0,'body':0,'main':0}
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag in self.roots: self.roots[tag]+=1
        if tag=='html': self.lang=a.get('lang','')
        if tag=='main': self.main_depth+=1
        if tag=='title': self.title_depth+=1
        if tag=='meta' and a.get('name'): self.meta[a['name']]=a.get('content','')
        if tag=='h2': self.h2=''
        if a.get('id'):
            if a['id'] in self.ids: self.errors.append('duplicate id: '+a['id'])
            self.ids.add(a['id'])
        if a.get('href'): self.hrefs.append(a['href'])
        if tag=='base': self.errors.append('base URLs are not allowed in self-contained HTML')
        if tag=='script': self.errors.append('Executable scripts are not needed; use static HTML/MathML.')
        if tag=='img' and a.get('src'): self.images.add(a['src']); self.assets.add(a['src'])
        if tag=='link' and a.get('rel')=='stylesheet': self.assets.add(a.get('href',''))
        if tag in ('source','img') and a.get('srcset'):
            self.assets.update(item.strip().split()[0] for item in a['srcset'].split(',') if item.strip())
        if tag in ('object','embed'):
            self.assets.add(a.get('data',a.get('src','')))
        if tag=='a' and 'data-cite' in a:
            self.citations.append(a)
            if self.current_block is not None: self.current_block['citations'].append(a)
        elif 'data-cite' in a:
            self.errors.append('Use a single-key <a data-cite="..."> for visible citations.')
        if tag=='p' and self.main_depth and not self.current_block:
            self.current_block={'text':'','citations':[]}
        if a.get('style'): self.assets.update(re.findall(r'url\([\"\']?([^\)\"\']+)',a['style']))
        if tag not in VOID: self.stack.append(tag)
    def handle_endtag(self,tag):
        if tag in VOID: return
        if not self.stack or self.stack[-1]!=tag:
            self.errors.append('mismatched/unclosed HTML tag: '+tag)
            if tag in self.stack:
                while self.stack and self.stack[-1]!=tag: self.stack.pop()
                self.stack.pop()
        else: self.stack.pop()
        if tag=='title': self.title_depth=0
        if tag=='h2' and self.h2 is not None: self.headings.append(self.h2.strip()); self.h2=None
        if tag=='main': self.main_depth=max(0,self.main_depth-1)
        if tag=='p' and self.current_block is not None:
            self.blocks.append(self.current_block); self.current_block=None
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        if tag not in VOID: self.handle_endtag(tag)
    def handle_data(self,data):
        if self.title_depth: self.title_text+=data
        if self.h2 is not None: self.h2+=data
        if self.current_block is not None: self.current_block['text']+=data
        if self.stack and self.stack[-1]=='style': self.assets.update(re.findall(r'url\([\"\']?([^\)\"\']+)',data))

def valid_pdf(path):
    try:
        from pypdf import PdfReader
        if not path.is_file() or path.stat().st_size==0: return False
        with path.open('rb') as handle:
            reader=PdfReader(handle,strict=True)
            return not reader.is_encrypted and len(reader.pages)>0 and all(float(p.mediabox.width)>0 and float(p.mediabox.height)>0 for p in reader.pages)
    except Exception:
        return False

def validate_asset(root,src,seen):
    if src.startswith('#'): return  # SVG paint servers/filters are in-document fragment references.
    p=contained_path(root,src)
    if p in seen: return
    seen.add(p)
    if not p.is_file(): raise ToolError('Missing local asset: '+src)
    suffix=p.suffix.lower()
    if suffix=='.css':
        text=p.read_text(encoding='utf-8')
        urls=re.findall(r'url\([\"\']?([^\)\"\']+)',text)
        urls+=re.findall(r'@import\s+[\"\']([^\"\']+)',text)
        for url in urls:
            if url.startswith(('http:','https:','data:','//','file:')):
                raise ToolError('Stylesheet assets must be local: '+url)
            dep=contained_path(root,((p.parent.relative_to(root)/url).as_posix()))
            validate_asset(root,dep.relative_to(root).as_posix(),seen)
    elif suffix=='.svg':
        tree=ET.parse(p)
        if tree.getroot().tag.split('}')[-1]!='svg': raise ToolError('Not an SVG: '+src)
        for node in tree.iter():
            if node.tag.split('}')[-1]=='script': raise ToolError('SVG scripts are not supported')
            for key,value in node.attrib.items():
                if key.split('}')[-1]=='href' and value and not value.startswith('#'):
                    if value.startswith(('http:','https:','data:','//','file:')):
                        raise ToolError('SVG assets must be local: '+value)
                    dep=contained_path(root,(p.parent.relative_to(root)/value).as_posix())
                    validate_asset(root,dep.relative_to(root).as_posix(),seen)
            style=node.attrib.get('style','')
            if node.tag.split('}')[-1]=='style': style+=''.join(node.itertext())
            for value in re.findall(r'url\([\"\']?([^\)\"\']+)',style):
                if value.startswith('#'): continue
                if value.startswith(('http:','https:','data:','//','file:')): raise ToolError('SVG style assets must be local: '+value)
                dep=contained_path(root,(p.parent.relative_to(root)/value).as_posix())
                validate_asset(root,dep.relative_to(root).as_posix(),seen)
    elif suffix not in ('.woff','.woff2','.ttf','.otf'):
        from PIL import Image
        with Image.open(p) as im: im.verify()

def validate(paper_dir,allow_missing_pdf=False,allow_no_figures=False):
    errors=[]; warnings=[]
    for name in ('article.html','references.bib','sources.yaml','theme.css','metrics.json','metrics-registry.json'):
        if not (paper_dir/name).is_file(): errors.append('missing required file: '+name)
    if errors: return {'ok':False,'errors':errors,'warnings':warnings}
    text=(paper_dir/'article.html').read_text(encoding='utf-8')
    if '{{' in text or '在此准确' in text or '[TODO:' in text or 'Example title' in text:
        errors.append('unfinished template placeholders remain')
    inv=HTMLInventory()
    inv.feed(text); inv.close()
    errors.extend(inv.errors)
    if inv.stack: errors.append('unclosed HTML elements: '+', '.join(inv.stack))
    if any(count!=1 for count in inv.roots.values()): errors.append('require exactly one html, body and main element')
    if inv.lang!='zh-CN' or not inv.title_text.strip(): errors.append('require lang=zh-CN and nonempty title')
    for key in ('paper-title','paper-authors','paper-year','paper-url','code-url','project-url','dataset-url','domains'):
        if key not in inv.meta: errors.append('missing metadata: '+key)
    for key in ('paper-title','paper-authors','paper-year','paper-url','domains'):
        if not inv.meta.get(key): errors.append('empty metadata: '+key)
    normalized=[re.sub(r'^\d+[.、\s]*','',s) for s in inv.headings]
    if normalized!=MAIN_SECTIONS: errors.append('main sections must match references/article-structure.md')
    if 'bibliography' not in inv.ids or 'toc' not in inv.ids: errors.append('render visible bibliography and navigation before validation')
    if not inv.citations: errors.append('article has no evidence citations')
    for href in inv.hrefs:
        if href.startswith('#') and href[1:] not in inv.ids: errors.append('broken fragment link: '+href)
    seen=set()
    for src in inv.assets:
        try: validate_asset(paper_dir,src,seen)
        except Exception as exc: errors.append('invalid asset %s: %s'%(src,exc))
    try:
        bib=parse_bib((paper_dir/'references.bib').read_text(encoding='utf-8'))
        manifest=read_json_yaml(paper_dir/'sources.yaml')
        sources=manifest.get('sources',[])
        if not isinstance(sources,list): raise ToolError('sources must be a list')
        source_map={s['id']:s for s in sources}
        if len(source_map)!=len(sources): errors.append('duplicate source IDs')
        if not manifest.get('paper',{}).get('title'): errors.append('missing paper identity')
        paper=manifest.get('paper',{})
        for key,mkey in (('title','paper-title'),('year','paper-year'),('url','paper-url')):
            expected=str(paper.get(key) or ('未报告' if key=='year' else ''))
            if expected!=inv.meta.get(mkey): errors.append('HTML/manifest metadata mismatch: '+key)
        authors=', '.join(paper.get('authors',[])) or '未报告'
        if authors!=inv.meta.get('paper-authors'): errors.append('HTML/manifest authors mismatch')
        gaps=manifest.get('evidence_gaps',[])
        for cite in inv.citations:
            key=cite.get('data-cite','')
            if key not in bib: errors.append('citation missing from bibliography: '+key)
            src=source_map.get(key)
            if not src: errors.append('citation missing source registration: '+key); continue
            if not (src.get('url') or src.get('local_path')): errors.append('source has no URL/local path: '+key)
            if not src.get('accessed') or not src.get('supports'): errors.append('source lacks accessed/supports: '+key)
            if not src.get('verified') or src.get('verification_scope')=='metadata':
                declared=cite.get('data-uncertain')=='true' and any(g.get('source_id')==key and g.get('reason') for g in gaps)
                if declared: warnings.append('explicit unverified citation: '+key)
                else: errors.append('cited evidence not verified: '+key)
        for block in inv.blocks:
            markers=re.findall(r'【(Paper|Code|Source|Analysis)】',block['text'])
            if not block['text'].strip(): continue
            if not markers: errors.append('main paragraph lacks evidence marker: '+block['text'][:50])
            if any(m in markers for m in ('Paper','Code','Source')) and not block['citations']:
                errors.append('factual paragraph lacks a visible citation: '+block['text'][:50])
            if any(m in markers for m in ('Paper','Code')) and any(not c.get('data-locator') for c in block['citations']):
                errors.append('Paper/Code citation needs section/page/table/file locator')
            if any(c.get('data-uncertain')=='true' for c in block['citations']) and '未核验' not in block['text']:
                errors.append('Uncertain citation must be visibly described as 未核验')
            if 'Code' in markers and not any(source_map.get(c.get('data-cite'),{}).get('type')=='code' for c in block['citations']):
                errors.append('Code paragraph needs actual code evidence, not only a paper citation')
            if 'Code' in markers and any(source_map.get(c.get('data-cite'),{}).get('type')=='code' and not source_map[c['data-cite']].get('version') for c in block['citations']):
                errors.append('Code evidence must record an exact release/version/commit')
        figures=manifest.get('figures',[])
        registered={contained_path(paper_dir,f['path']).relative_to(paper_dir).as_posix():f for f in figures}
        if len(registered)!=len(figures): errors.append('duplicate figure paths')
        if not inv.images and not (allow_no_figures and manifest.get('figure_omission_reason')):
            errors.append('no figures; use --allow-no-figures and document figure_omission_reason only when justified')
        for image in inv.images:
            rel=contained_path(paper_dir,image).relative_to(paper_dir).as_posix()
            f=registered.get(rel)
            if not f: errors.append('figure lacks exact-path provenance: '+rel); continue
            if not f.get('original_figure') or not f.get('caption') or f.get('source_id') not in source_map:
                errors.append('figure lacks original number/caption/valid source: '+rel)
            if not f.get('crop'): errors.append('figure crop must state parameters or none: '+rel)
        for asset in seen:
            if asset.suffix=='.svg':
                warnings.append('Visually verify SVG typography/crop: '+asset.name)
        from hardware_metrics import compute_records
        metrics=read_json_yaml(paper_dir/'metrics.json')
        registry=read_json_yaml(paper_dir/'metrics-registry.json')
        expected=compute_records(json.loads(json.dumps(metrics)),registry)
        if expected.get('derived')!=metrics.get('derived'): errors.append('Derived metrics are stale or inconsistent; run hardware_metrics.py compute')
        for row in metrics.get('results',[]):
            if row.get('source_id') not in source_map or not row.get('locator') or not row.get('design_point'):
                errors.append('Raw metric result lacks source/locator/design point')
            elif not source_map[row['source_id']].get('verified') or source_map[row['source_id']].get('verification_scope')=='metadata':
                errors.append('Raw metric result source is not content-verified')
    except Exception as exc: errors.append('bibliography/provenance error: '+str(exc))
    if not allow_missing_pdf:
        pdf=paper_dir/'article.pdf'
        if not valid_pdf(pdf): errors.append('missing or unparseable PDF')
        try:
            record=json.loads((paper_dir/'build-manifest.json').read_text(encoding='utf-8'))
            if record.get('inputs')!=input_fingerprint(paper_dir): errors.append('PDF is stale: HTML/assets/records changed since build')
            if not pdf.is_file() or record.get('pdf_sha256')!=file_hash(pdf): errors.append('PDF does not match the current build record')
        except Exception as exc: errors.append('missing/invalid build record: '+str(exc))
    return {'ok':not errors,'errors':errors,'warnings':list(dict.fromkeys(warnings))}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--paper-dir',required=True,type=Path)
    parser.add_argument('--allow-missing-pdf',action='store_true')
    parser.add_argument('--allow-no-figures',action='store_true')
    parser.add_argument('--json',action='store_true')
    args=parser.parse_args()
    try: result=validate(args.paper_dir.resolve(),args.allow_missing_pdf,args.allow_no_figures)
    except Exception as exc: result={'ok':False,'errors':[str(exc)],'warnings':[]}
    if args.json: print(json.dumps(result,ensure_ascii=False,indent=2))
    else:
        for kind in ('errors','warnings'):
            for line in result[kind]: print(kind.upper()+': '+line)
        print('VALID' if result['ok'] else 'INVALID')
    return 0 if result['ok'] else 1

if __name__=='__main__': raise SystemExit(main())
