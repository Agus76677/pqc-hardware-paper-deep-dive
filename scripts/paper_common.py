#!/usr/bin/env python3
"""Shared paths, records, dependency discovery and build fingerprints."""
from __future__ import annotations
import hashlib, json, os, re, shutil, subprocess, sys, unicodedata
from pathlib import Path

class ToolError(RuntimeError):
    pass

def skill_root():
    return Path(__file__).resolve().parent.parent

def executable(*names):
    return next((found for name in names if (found := shutil.which(name))), None)

def command_output(command, timeout=15):
    try:
        result = subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout)
        return result.returncode, (result.stdout+result.stderr).strip()
    except (OSError,subprocess.TimeoutExpired) as exc:
        return -1,str(exc)

def find_browser():
    explicit=os.environ.get('PAPER_DEEP_DIVE_BROWSER')
    if explicit:
        return shutil.which(explicit) or (explicit if Path(explicit).is_file() else None)
    found=executable('chromium','chromium-browser','google-chrome','google-chrome-stable','chrome','msedge')
    if found:
        return found
    candidates=[]
    if os.name=='nt':
        for key in ('PROGRAMFILES','PROGRAMFILES(X86)','LOCALAPPDATA'):
            base=os.environ.get(key)
            if base:
                candidates.extend(Path(base)/tail for tail in ('Google/Chrome/Application/chrome.exe','Microsoft/Edge/Application/msedge.exe','Chromium/Application/chrome.exe'))
    elif sys.platform=='darwin':
        candidates=[Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),Path('/Applications/Chromium.app/Contents/MacOS/Chromium'),Path('/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge')]
    return next((str(p) for p in candidates if p.is_file()),None)

def find_imagemagick():
    for name in ('magick','convert'):
        candidate=executable(name)
        if candidate:
            code,version=command_output([candidate,'-version'])
            if code==0 and 'ImageMagick' in version:
                return candidate
    return None

def run(command,*,cwd=None,check=True,capture=False,env=None,timeout=120):
    result=subprocess.run(list(command),cwd=cwd,env=env,check=False,text=True,encoding='utf-8',errors='replace',stdout=subprocess.PIPE if capture else None,stderr=subprocess.STDOUT if capture else None,timeout=timeout)
    if check and result.returncode:
        raise ToolError('Command failed (%s): %s\n%s' % (result.returncode,' '.join(map(str,command)),result.stdout or ''))
    return result

def slugify(value,limit=96):
    value=unicodedata.normalize('NFKC',value).strip().lower()
    value=re.sub(r'[<>:"/\\|?*\x00-\x1f]','-',value)
    value=re.sub(r'[^\w.-]+','-',value,flags=re.UNICODE)
    value=re.sub(r'[-_.]{2,}','-',value).strip(' .-_')[:limit].rstrip(' .-_') or 'paper-deep-dive'
    reserved={'CON','PRN','AUX','NUL',*('COM%d'%i for i in range(1,10)),*('LPT%d'%i for i in range(1,10))}
    return 'paper-'+value if value.split('.')[0].upper() in reserved else value

def bibtex_escape(value):
    replacements={'\\':r'\textbackslash{}','{':r'\{','}':r'\}','%':r'\%','&':r'\&','#':r'\#','_':r'\_'}
    return ''.join(replacements.get(c,c) for c in str(value))

def bibtex_url_escape(value):
    return value.replace('{',r'\{').replace('}',r'\}')

def read_json_yaml(path):
    if not path.exists():
        return {'schema_version':2,'paper':{},'sources':[],'figures':[]}
    text=path.read_text(encoding='utf-8-sig')
    try:
        data=json.loads(text)
    except json.JSONDecodeError:
        try:
            import yaml
        except ImportError as exc:
            raise ToolError('Install PyYAML to read ordinary YAML, or save JSON in this .yaml file.') from exc
        data=yaml.safe_load(text)
    if not isinstance(data,dict):
        raise ToolError('%s must contain a mapping/object'%path)
    return data

def write_json_yaml(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    temporary.replace(path)

def contained_path(root,relative):
    from urllib.parse import unquote,urlsplit
    parsed=urlsplit(relative)
    if parsed.scheme or parsed.netloc or not parsed.path:
        raise ToolError('Asset must be a relative local path: %s'%relative)
    path=(root/unquote(parsed.path)).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ToolError('Asset escapes paper directory: %s'%relative) from exc
    return path

def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def input_fingerprint(paper_dir):
    result={}
    for p in sorted(paper_dir.rglob('*')):
        rel=p.relative_to(paper_dir)
        if p.is_file() and rel.parts[0]!='build' and p.name not in ('article.pdf','build-manifest.json'):
            result[rel.as_posix()]=file_hash(p)
    return result

def unique_preserving_order(values):
    return list(dict.fromkeys(value for value in values if value))

def fail(message,code=2):
    print('error: '+str(message),file=sys.stderr)
    raise SystemExit(code)

def is_admin():
    if os.name=='nt':
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    return hasattr(os,'geteuid') and os.geteuid()==0
