#!/usr/bin/env python3
"""Show or apply a plan for only missing capabilities; no automatic elevation."""
from __future__ import annotations
import argparse, os, platform, shlex, sys
from dataclasses import dataclass
from check_environment import inspect_environment
from paper_common import executable,is_admin,run,skill_root

@dataclass
class InstallPlan:
    manager: str
    commands: list
    notes: list

def detect_manager(preferred=None):
    if preferred: return preferred if executable(preferred) else None
    candidates={'Windows':['winget','choco'],'Darwin':['brew'],'Linux':['apt-get']}.get(platform.system(),[])
    return next((m for m in candidates if executable(m)),None)

def build_plan(manager,missing):
    names=set(missing)
    commands=[]; notes=[]
    python_missing=names & {'PDF parser (pypdf)','Image decoder (Pillow)','YAML reader (PyYAML)'}
    if python_missing:
        mapping={'PDF parser (pypdf)':'pypdf>=3.17','Image decoder (Pillow)':'Pillow>=9.5','YAML reader (PyYAML)':'PyYAML>=6.0,<7'}
        commands.append([sys.executable,'-m','pip','install',*(mapping[n] for n in sorted(python_missing))])
    package_map={
        'apt-get':{'PDF rasterizer':'poppler-utils','ImageMagick':'imagemagick','HTML PDF browser':'chromium'},
        'brew':{'PDF rasterizer':'poppler','ImageMagick':'imagemagick','HTML PDF browser':'chromium'},
        'winget':{'PDF rasterizer':'oschwartz10612.Poppler','ImageMagick':'ImageMagick.ImageMagick','HTML PDF browser':'Google.Chrome'},
        'choco':{'PDF rasterizer':'poppler','ImageMagick':'imagemagick','HTML PDF browser':'googlechrome'}}
    system_missing=[n for n in sorted(names) if n in ('PDF rasterizer','ImageMagick','HTML PDF browser')]
    if system_missing and not manager:
        notes.append('Install the missing system capabilities manually; no supported package manager was detected.')
    elif system_missing:
        packages=[package_map[manager][n] for n in system_missing]
        if manager=='apt-get':
            prefix=[] if is_admin() else ['sudo']
            commands += [prefix+['apt-get','update'],prefix+['apt-get','install','-y',*packages]]
            notes.append('The plan includes sudo only if needed; use --apply only after authorization for elevation.')
        elif manager=='brew':
            normal=[p for p in packages if p!='chromium']
            if normal: commands.append(['brew','install',*normal])
            if 'chromium' in packages: commands.append(['brew','install','--cask','chromium'])
        elif manager=='winget':
            commands.extend(['winget','install','--id',p,'--exact','--accept-package-agreements','--accept-source-agreements'] for p in packages)
        elif manager=='choco': commands.append(['choco','install','-y',*packages])
    notes.append('CJK fonts are inspected separately; visually verify printed glyphs. Install Noto/Source Han if no suitable system font is available.')
    return InstallPlan(manager or 'manual',commands,notes)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--apply',action='store_true'); p.add_argument('--yes',action='store_true')
    p.add_argument('--manager',choices=['apt-get','brew','winget','choco'])
    p.add_argument('--require-figure-tools',action='store_true')
    args=p.parse_args()
    missing=[c.name for c in inspect_environment(args.require_figure_tools) if c.required and not c.available]
    if not missing: print('Core environment is ready; no packages need installation.'); return 0
    plan=build_plan(detect_manager(args.manager),missing)
    print('Missing: '+', '.join(missing))
    for c in plan.commands: print('  '+' '.join(shlex.quote(str(part)) for part in c))
    for n in plan.notes: print('note: '+n)
    if not args.apply: print('Dry run only; --apply executes the displayed plan.'); return 0
    if not plan.commands: return 2
    if not args.yes and input('Apply this installation plan? [y/N] ').strip().lower() not in ('y','yes'): return 1
    env=os.environ.copy()
    if platform.system()=='Darwin': env.setdefault('HOMEBREW_NO_AUTO_UPDATE','1')
    try:
        for c in plan.commands: run(c,env=env,timeout=900)
    except Exception as exc: print('Installation failed: '+str(exc)); return 1
    remaining=[c.name for c in inspect_environment(args.require_figure_tools) if c.required and not c.available]
    if remaining: print('Still unavailable: '+', '.join(remaining)+'. Reopen the shell and recheck.'); return 1
    print('Environment ready.'); return 0

if __name__=='__main__': raise SystemExit(main())
