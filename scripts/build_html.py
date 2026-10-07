#!/usr/bin/env python3
"""Render references, preflight HTML, and atomically print a current Chromium PDF."""
from __future__ import annotations
import argparse, json, subprocess, tempfile, shutil, time
from datetime import datetime, timezone
from pathlib import Path
from paper_common import ToolError,find_browser,file_hash,input_fingerprint,write_json_yaml
from render_references import render
from validate_output import validate,valid_pdf

class PrintWorkspace:
    """Browser children may close profiles after the parent returns on Windows."""
    def __init__(self, scratch):
        self.scratch=scratch.resolve()
        self.path=None
    def __enter__(self):
        self.path=Path(tempfile.mkdtemp(prefix='print-',dir=str(self.scratch)))
        return str(self.path)
    def __exit__(self, exc_type, exc, traceback):
        self.path.resolve().relative_to(self.scratch)
        for attempt in range(4):
            try:
                shutil.rmtree(self.path)
                return False
            except OSError:
                time.sleep(.2)
        # A verified PDF must not be reported as failed merely because an isolated
        # profile is briefly locked. Leave only scratch data and disclose its path.
        with (self.scratch/'cleanup-warnings.log').open('a',encoding='utf-8') as log:
            log.write('Isolated browser profile still locked; remove after browser exit: '+str(self.path)+'\n')
        print('NOTE: isolated browser scratch retained temporarily; see build/cleanup-warnings.log')
        return False

def build(paper_dir,timeout=120,allow_no_figures=False):
    render(paper_dir)
    result=validate(paper_dir,allow_missing_pdf=True,allow_no_figures=allow_no_figures)
    if not result['ok']: raise ToolError('HTML preflight failed:\n'+'\n'.join(result['errors']))
    browser=find_browser()
    if not browser: raise ToolError('No browser found; set PAPER_DEEP_DIVE_BROWSER to Chrome/Edge/Chromium.')
    scratch=paper_dir/'build'
    scratch.mkdir(exist_ok=True)
    inputs=input_fingerprint(paper_dir)
    with PrintWorkspace(scratch) as temporary:
        tmp=Path(temporary)
        pdf=tmp/'article.pdf'
        command=[browser,'--headless','--disable-gpu','--no-pdf-header-footer','--allow-file-access-from-files','--print-to-pdf='+str(pdf),'--user-data-dir='+str(tmp/'profile'),(paper_dir/'article.html').as_uri()]
        try:
            import os
            completed=subprocess.run(command,cwd=str(paper_dir),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=timeout,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        except subprocess.TimeoutExpired as exc:
            raise ToolError('Browser print timed out; previous PDF was not accepted as a new build.') from exc
        (scratch/'browser.log').write_text(completed.stdout+'\n'+completed.stderr,encoding='utf-8')
        if completed.returncode or not valid_pdf(pdf):
            raise ToolError('Browser did not produce a parseable new PDF; inspect build/browser.log.')
        if inputs!=input_fingerprint(paper_dir): raise ToolError('Inputs changed while printing; rebuild.')
        digest=file_hash(pdf)
        pdf.replace(paper_dir/'article.pdf')
        write_json_yaml(paper_dir/'build-manifest.json',{'schema_version':1,'built_at':datetime.now(timezone.utc).isoformat(),'browser':browser,'inputs':inputs,'pdf_sha256':digest})
    return paper_dir/'article.pdf'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--paper-dir',required=True,type=Path)
    parser.add_argument('--timeout',type=int,default=120)
    parser.add_argument('--allow-no-figures',action='store_true')
    args=parser.parse_args()
    try:
        print(build(args.paper_dir.expanduser().resolve(),args.timeout,args.allow_no_figures))
        return 0
    except (ToolError,OSError) as exc:
        print('ERROR: '+str(exc))
        return 1

if __name__=='__main__': raise SystemExit(main())
