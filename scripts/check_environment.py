#!/usr/bin/env python3
"""Check core HTML/PDF dependencies; extraction tools are conditional."""
from __future__ import annotations
import argparse, importlib.util, json, os, platform
from dataclasses import dataclass,asdict
from pathlib import Path
from paper_common import executable,command_output,find_browser,find_imagemagick

@dataclass
class Capability:
    name: str
    required: bool
    available: bool
    command: object
    detail: str

def command_capability(name,required,names,args):
    command=executable(*names)
    code,detail=command_output([command,*args]) if command else (-1,'not found')
    return Capability(name,required,bool(command and code==0),command,detail.splitlines()[0] if detail else '')

def font_available():
    fc=executable('fc-match')
    if fc:
        code,text=command_output([fc,'-f','%{family}','Noto Sans CJK SC'])
        if code==0 and any(s in text.lower() for s in ('noto','source han','cjk')):
            return True,text
    if os.name=='nt':
        dirs=[Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts',Path(os.environ.get('LOCALAPPDATA',''))/'Microsoft/Windows/Fonts']
        for directory in dirs:
            if directory.is_dir():
                for p in directory.iterdir():
                    if p.name.lower().startswith(('msyh','simsun','simhei','notosanscjk','notoserifcjk','sourcehansans','sourcehanserif')):
                        return True,str(p)
    return False,'No known CJK font found; inspect printed glyphs.'

def inspect_environment(require_figure_tools=False):
    browser=find_browser()
    browser_ok=bool(browser and Path(browser).is_file())
    if browser_ok and os.name!='nt':
        code,_=command_output([browser,'--version'])
        browser_ok=code==0
    image=find_imagemagick()
    fonts,detail=font_available()
    return [Capability('HTML PDF browser',True,browser_ok,browser,'Resolved executable; rendering checked during build' if browser_ok else 'Set PAPER_DEEP_DIVE_BROWSER or install Chrome/Edge/Chromium'),
        Capability('PDF parser (pypdf)',True,importlib.util.find_spec('pypdf') is not None,None,'pip install -r scripts/requirements.txt'),
        Capability('Image decoder (Pillow)',True,importlib.util.find_spec('PIL') is not None,None,'pip install -r scripts/requirements.txt'),
        Capability('YAML reader (PyYAML)',True,importlib.util.find_spec('yaml') is not None,None,'pip install -r scripts/requirements.txt'),
        command_capability('PDF rasterizer',require_figure_tools,('pdftocairo','pdftoppm'),('-v',)),
        command_capability('PDF metadata',False,('pdfinfo',),('-v',)),
        Capability('ImageMagick',require_figure_tools,bool(image),image,'Verified ImageMagick identity' if image else 'ImageMagick not found'),
        Capability('CJK fonts',False,fonts,None,detail),
        command_capability('Git',False,('git',),('--version',))]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json',action='store_true')
    parser.add_argument('--require-figure-tools',action='store_true')
    parser.add_argument('--allow-missing-figure-tools',action='store_true',help='Compatibility alias; figure tools are optional by default.')
    args=parser.parse_args()
    caps=inspect_environment(args.require_figure_tools)
    payload={'platform':platform.platform(),'python':platform.python_version(),'ready':all(c.available for c in caps if c.required),'capabilities':[asdict(c) for c in caps]}
    if args.json:
        print(json.dumps(payload,ensure_ascii=False,indent=2))
    else:
        for c in caps:
            print('[%s] %s: %s'%('OK' if c.available else ('MISSING' if c.required else 'OPTIONAL'),c.name,c.detail))
        print('READY' if payload['ready'] else 'NOT READY')
    return 0 if payload['ready'] else 1

if __name__=='__main__':
    raise SystemExit(main())
