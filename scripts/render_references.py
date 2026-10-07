#!/usr/bin/env python3
"""Materialize readable citations, bibliography and section navigation in article.html."""
from __future__ import annotations
import argparse, re
from html import escape,unescape
from html.parser import HTMLParser
from pathlib import Path
from paper_common import ToolError

KEY_RE=re.compile(r'^[A-Za-z0-9_.:-]+$')

def balanced(text,start):
    opening=text[start]
    closing='}' if opening=='{' else '"'
    depth=1
    i=start+1
    while i<len(text):
        if text[i]=='\\':
            i+=2
            continue
        if opening=='{' and text[i]=='{':
            depth+=1
        if text[i]==closing:
            depth-=1
            if depth==0:
                return text[start+1:i],i+1
        i+=1
    raise ToolError('Unclosed BibTeX field or entry')

def parse_bib(text):
    # Explicit literal fields only: unsupported macro expansion must fail visibly.
    result={}
    text=re.sub(r'(?m)^\s*%.*$','',text)
    pos=0
    while True:
        m=re.search(r'@(\w+)\s*\{',text[pos:])
        if not m:
            break
        start=pos+m.end()-1
        body,end=balanced(text,start)
        pos=end
        kind=m.group(1).lower()
        if kind=='comment':
            continue
        if kind in ('string','preamble'):
            raise ToolError('BibTeX macros/preambles are not supported; use literal fields.')
        key,sep,rest=body.partition(',')
        key=key.strip()
        if not sep or not KEY_RE.fullmatch(key) or key in result:
            raise ToolError('Invalid or duplicate BibTeX key: '+key)
        fields={}
        p=0
        while p<len(rest):
            field=re.match(r'\s*,?\s*([\w-]+)\s*=\s*',rest[p:])
            if not field:
                if rest[p:].strip(' \n\r\t,'):
                    raise ToolError('Unsupported BibTeX field near '+rest[p:p+60])
                break
            p+=field.end()
            if p>=len(rest):
                raise ToolError('Missing BibTeX field value')
            if rest[p] in ('{','"'):
                value,p=balanced(rest,p)
            else:
                value=rest[p:].split(',',1)[0].strip()
                if not re.fullmatch(r'\d+',value):
                    raise ToolError('Use literal braced/quoted BibTeX fields, not macros.')
                p+=len(rest[p:].split(',',1)[0])
            fields[field.group(1).lower()]=value
        if not fields.get('title'):
            raise ToolError('Bibliography entry lacks title: '+key)
        result[key]=fields
    if not result:
        raise ToolError('No bibliography entries')
    return result

def plain(value):
    value=value.replace(r'\textbackslash{}','\\')
    value=re.sub(r'\\([%&#_{}])',r'\1',value)
    value=re.sub(r'\\(?:textit|textbf|emph)\{([^{}]*)\}',r'\1',value)
    return value.replace('{','').replace('}','')

class Attributes(HTMLParser):
    def __init__(self):
        super().__init__()
        self.attrs={}
    def handle_starttag(self,tag,attrs):
        self.attrs=dict(attrs)

def render(paper_dir):
    path=paper_dir/'article.html'
    text=path.read_text(encoding='utf-8')
    entries=parse_bib((paper_dir/'references.bib').read_text(encoding='utf-8'))
    used=[]
    pattern=re.compile(r'<a\b(?P<attrs>[^>]*\bdata-cite\s*=\s*([\"\']).*?\2[^>]*)>.*?</a\s*>',re.S|re.I)
    def citation(m):
        parser=Attributes()
        parser.feed('<a'+m.group('attrs')+'>')
        attrs=parser.attrs
        key=attrs.get('data-cite','')
        if key not in entries:
            raise ToolError('Citation key missing or not a single key: '+key)
        if key not in used:
            used.append(key)
        number=used.index(key)+1
        extras=''.join(' %s="%s"'%(name,escape(attrs[name],quote=True)) for name in ('data-locator','data-uncertain') if attrs.get(name))
        locator=' '+escape(attrs['data-locator']) if attrs.get('data-locator') else ''
        return '<a class="citation" data-cite="%s"%s href="#ref-%s">[%d]%s</a>'%(escape(key),extras,escape(key),number,locator)
    text=pattern.sub(citation,text)
    if not used:
        raise ToolError('No visible citations: author <a data-cite="paper" data-locator="Table III">...</a>.')
    items=[]
    for key in used:
        fields=entries[key]
        if 'paper' == key and fields.get('eprint') and not fields.get('version'):
            fields['version']=fields['eprint']
        parts=[plain(fields.get('author','')),plain(fields['title']),plain(fields.get('year','')),plain(fields.get('journaltitle',fields.get('booktitle','')))]
        label='. '.join(escape(p) for p in parts if p)
        url=fields.get('url') or ('https://doi.org/'+fields['doi'] if fields.get('doi') else '')
        if url:
            if url.startswith('file:'):
                import os
                from urllib.parse import urlsplit,unquote,quote
                parsed=urlsplit(url)
                local=unquote(parsed.path)
                if parsed.netloc: raise ToolError('UNC bibliography files are unsupported; copy the source into the paper directory.')
                if os.name=='nt' and re.match(r'^/[A-Za-z]:/',local): local=local[1:]
                try: relative=Path(local).resolve().relative_to(paper_dir.resolve())
                except ValueError as exc: raise ToolError('Copy local bibliography source into the paper directory: '+key) from exc
                if not (paper_dir/relative).is_file(): raise ToolError('Missing local bibliography source: '+key)
                url=quote(relative.as_posix())
            elif not url.startswith(('https://','http://')):
                raise ToolError('Bibliography URL must be http(s) or a local file copied into paper-dir: '+key)
            label+=' <a href="%s">来源</a>'%escape(url,quote=True)
        if fields.get('version'):
            label+='；版本 '+escape(plain(fields['version']))
        items.append('<li id="ref-%s">%s</li>'%(escape(key),label))
    block='<div id="bibliography" data-generated="references"><ol>\n'+'\n'.join(items)+'\n</ol></div>'
    if not re.search(r'<div\b[^>]*id=[\"\']bibliography[\"\'][^>]*>.*?</div\s*>',text,re.S|re.I):
        raise ToolError('Add <div id="bibliography"></div> to the sources section.')
    text=re.sub(r'<div\b[^>]*id=[\"\']bibliography[\"\'][^>]*>.*?</div\s*>',lambda _:block,text,flags=re.S|re.I)
    toc=[]
    def heading(m):
        number=len(toc)+1
        parser=Attributes()
        parser.feed('<h2'+m.group('attrs')+'>')
        existing=parser.attrs.get('id')
        ident=existing or 'section-%d'%number
        attrs=m.group('attrs') if existing else m.group('attrs')+' id="'+ident+'"'
        label=unescape(re.sub('<[^>]+>','',m.group('body')))
        label=re.sub(r'^\d+[.、\s]*','',label)
        toc.append('<li><a href="#%s">%s</a></li>'%(escape(ident),escape(label)))
        return '<h2%s>%s</h2>'%(attrs,m.group('body'))
    text=re.sub(r'<h2\b(?P<attrs>[^>]*)>(?P<body>.*?)</h2\s*>',heading,text,flags=re.S|re.I)
    nav='<nav id="toc" aria-label="目录"><ol>'+'\n'.join(toc)+'</ol></nav>'
    if re.search(r'<nav\b[^>]*id=[\"\']toc[\"\'][^>]*>.*?</nav\s*>',text,re.S|re.I):
        text=re.sub(r'<nav\b[^>]*id=[\"\']toc[\"\'][^>]*>.*?</nav\s*>',lambda _:nav,text,flags=re.S|re.I)
    else:
        text=text.replace('<main>',nav+'\n<main>',1)
    path.write_text(text,encoding='utf-8')
    return used

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--paper-dir',required=True,type=Path)
    args=parser.parse_args()
    try:
        used=render(args.paper_dir.resolve())
        print('Rendered references: '+', '.join(used))
        return 0
    except (ToolError,OSError) as exc:
        print('ERROR: '+str(exc))
        return 1

if __name__=='__main__':
    raise SystemExit(main())
