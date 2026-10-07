#!/usr/bin/env python3
"""Register explicit formulas and compute traceable single-design-point metrics."""
from __future__ import annotations
import argparse, ast, hashlib, json, math, operator
from pathlib import Path
from paper_common import ToolError,read_json_yaml,write_json_yaml

OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.Pow:operator.pow}

def expression(formula,values=None):
    if not isinstance(formula,str) or len(formula)>1000: raise ToolError('Invalid/overlong formula')
    tree=ast.parse(formula,mode='eval')
    if sum(1 for _ in ast.walk(tree))>100: raise ToolError('Formula is too complex')
    names=set()
    def walk(node):
        if isinstance(node,ast.Expression): return walk(node.body)
        if isinstance(node,ast.Name):
            names.add(node.id)
            return 1.0 if values is None else values[node.id]
        if isinstance(node,ast.Constant) and type(node.value) in (int,float):
            if not math.isfinite(node.value) or abs(node.value)>1e12: raise ToolError('Invalid constant')
            return float(node.value)
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):
            return walk(node.operand) * (-1 if isinstance(node.op,ast.USub) else 1)
        if isinstance(node,ast.BinOp) and type(node.op) in OPS:
            left,right=walk(node.left),walk(node.right)
            if isinstance(node.op,ast.Pow) and (not isinstance(node.right,ast.Constant) or right not in (1,2)):
                raise ToolError('Only literal powers 1 and 2 are supported')
            # Structural validation must not evaluate a dummy division by zero.
            if values is None: return 1.0
            answer=OPS[type(node.op)](left,right)
            if not math.isfinite(answer): raise ToolError('Non-finite metric')
            return answer
        raise ToolError('Only numeric constants, input names, + - * / and powers 1/2 are allowed')
    value=walk(tree)
    return names,value

def validate_definition(metric):
    for key in ('id','version','formula','unit','required_inputs','platform_scope','operation_scope','definition_source','resource_weights','time_definition'):
        if key not in metric or metric[key] in ('',None,[]): raise ToolError('Metric definition missing '+key)
    import re
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_.-]*',metric['id']): raise ToolError('Invalid metric ID')
    if not isinstance(metric['required_inputs'],dict) or not all(isinstance(k,str) and isinstance(v,str) and v for k,v in metric['required_inputs'].items()):
        raise ToolError('required_inputs must map input names to exact units')
    names,_=expression(metric['formula'])
    if names!=set(metric['required_inputs']): raise ToolError('Formula variables must exactly match required_inputs')
    source=metric['definition_source']
    if not isinstance(source,dict) or not source.get('locator') or not (source.get('url') or source.get('user_provided') is True):
        raise ToolError('Definition needs URL/user_provided plus precise locator')
    if not isinstance(metric['platform_scope'],list) or not isinstance(metric['operation_scope'],list): raise ToolError('Scopes must be explicit lists')
    if not isinstance(metric['resource_weights'],dict): raise ToolError('resource_weights must be a mapping (empty for unweighted formulas)')
    if metric.get('verified') is not True: raise ToolError('Confirm the formula against the reference/user definition before registering')
    return metric

def compute_records(data,registry):
    definitions=[validate_definition(m) for m in registry.get('metrics',[])]
    identities=[(m['id'],str(m['version'])) for m in definitions]
    if len(set(identities))!=len(identities): raise ToolError('Duplicate metric ID/version')
    derived=[]
    results=data.get('results',[])
    if len({r.get('id') for r in results})!=len(results) or any(not r.get('id') for r in results): raise ToolError('Missing/duplicate result IDs')
    for record in results:
        for metric in definitions:
            item={'result_id':record['id'],'metric_id':metric['id'],'metric_version':metric['version'],'label':'Analysis','status':'cannot_compute','formula':metric['formula'],'unit':metric['unit'],'definition_source':metric['definition_source'],'definition_sha256':hashlib.sha256(json.dumps(metric,sort_keys=True,ensure_ascii=False).encode('utf-8')).hexdigest(),'result_locator':record.get('locator'),'source_id':record.get('source_id'),'design_point':record.get('design_point'),'inputs':{}}
            reasons=[]
            for key in ('source_id','locator','design_point','parameter_set','measurement_stage'):
                if not record.get(key): reasons.append('missing result context: '+key)
            if record.get('platform_scope') not in metric['platform_scope']: reasons.append('incompatible platform scope')
            if record.get('operation_scope') not in metric['operation_scope']: reasons.append('incompatible operation boundary')
            numbers={}
            for name,unit in metric['required_inputs'].items():
                raw=record.get('inputs',{}).get(name)
                if not isinstance(raw,dict) or raw.get('unit')!=unit: reasons.append('missing/wrong-unit input: '+name); continue
                number=raw.get('value')
                if type(number) not in (int,float) or not math.isfinite(number) or number<0: reasons.append('invalid input: '+name); continue
                if name in ('frequency_Hz','frequency_MHz','II_cycles','throughput_ops_s') and number==0:
                    reasons.append('input must be positive: '+name); continue
                if raw.get('design_point',record['design_point'])!=record['design_point']: reasons.append('mixed design point: '+name); continue
                numbers[name]=number
                item['inputs'][name]=dict(raw)
            if not reasons:
                try:
                    _,value=expression(metric['formula'],numbers)
                    if value<0: raise ToolError('Negative derived cost')
                    item.update(status='computed',value=value)
                except (ToolError,ArithmeticError,KeyError) as exc: reasons.append(str(exc))
            item['reasons']=reasons
            derived.append(item)
    data['derived']=derived
    return data

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    reg=sub.add_parser('register')
    reg.add_argument('--registry',required=True,type=Path)
    reg.add_argument('--definition',required=True,type=Path)
    comp=sub.add_parser('compute')
    comp.add_argument('--paper-dir',required=True,type=Path)
    comp.add_argument('--registry',type=Path)
    args=parser.parse_args()
    try:
        if args.command=='register':
            metric=validate_definition(read_json_yaml(args.definition))
            registry=read_json_yaml(args.registry) if args.registry.exists() else {'schema_version':1,'metrics':[]}
            existing=next((m for m in registry.get('metrics',[]) if (m.get('id'),str(m.get('version')))==(metric['id'],str(metric['version']))),None)
            if existing is not None and existing!=metric: raise ToolError('Existing ID/version has a different definition; register a new version')
            if existing is None: registry.setdefault('metrics',[]).append(metric)
            write_json_yaml(args.registry,registry)
            print('Registered '+metric['id']+' version '+str(metric['version']))
        else:
            paper=args.paper_dir.resolve()
            registry=read_json_yaml(args.registry.resolve() if args.registry else paper/'metrics-registry.json')
            data=read_json_yaml(paper/'metrics.json')
            manifest=read_json_yaml(paper/'sources.yaml')
            known={s['id']:s for s in manifest.get('sources',[])}
            for record in data.get('results',[]):
                source=known.get(record.get('source_id'))
                if not source or not source.get('verified') or source.get('verification_scope')=='metadata': raise ToolError('Raw result source not content-verified: '+str(record.get('source_id')))
            compute_records(data,registry)
            write_json_yaml(paper/'metrics-registry.json',registry)
            write_json_yaml(paper/'metrics.json',data)
            print(json.dumps(data['derived'],ensure_ascii=False,indent=2))
        return 0
    except (ToolError,OSError,ValueError,SyntaxError) as exc:
        print('ERROR: '+str(exc)); return 1

if __name__=='__main__': raise SystemExit(main())
