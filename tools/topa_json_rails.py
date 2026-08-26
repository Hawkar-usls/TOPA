#!/usr/bin/env python3
from __future__ import annotations
import argparse,bz2,gzip,hashlib,json,os,re,tempfile
from collections import Counter
from pathlib import Path

LINE_FORMATS={".jsonl",".ndjson"}; COMPRESSED={".gz",".bz2"}

def detect_format(path):
    p=Path(path); s=[x.lower() for x in p.suffixes]; compression=None
    logical=s[-1] if s else ""
    if logical in COMPRESSED:
        compression=logical[1:]; logical=s[-2] if len(s)>=2 else ""
    if logical==".json": kind="json"
    elif logical in LINE_FORMATS: kind="jsonl"
    else: raise ValueError(f"unsupported JSON rail extension for {p}")
    return {"kind":kind,"compression":compression,"logical_suffix":logical}

def open_text(path,mode="rt"):
    p=Path(path); f=detect_format(p)
    if f["compression"]=="gz": return gzip.open(p,mode,encoding="utf-8",newline="")
    if f["compression"]=="bz2": return bz2.open(p,mode,encoding="utf-8",newline="")
    return p.open(mode,encoding="utf-8",newline="")

def raw_sha256(path,chunk_size=1024*1024):
    h=hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda:fh.read(chunk_size),b""): h.update(chunk)
    return h.hexdigest()

def canonical_json_line(obj):
    return (json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n").encode()

def iter_records(path,strict=True,error_sink=None):
    f=detect_format(path)
    if f["kind"]=="json":
        with open_text(path) as fh: obj=json.load(fh)
        if isinstance(obj,list): yield from obj
        else: yield obj
        return
    with open_text(path) as fh:
        for n,line in enumerate(fh,1):
            if not line.strip(): continue
            try: yield json.loads(line)
            except Exception as exc:
                item={"line":n,"error":f"{type(exc).__name__}: {exc}","preview":line[:240].rstrip()}
                if error_sink is not None: error_sink.append(item)
                if strict: raise ValueError(f"invalid JSONL/NDJSON at {path}:{n}: {exc}") from exc

def _writer(path):
    path=Path(path); f=detect_format(path)
    if f["compression"]=="gz": return gzip.open(path,"wt",encoding="utf-8",newline="")
    if f["compression"]=="bz2": return bz2.open(path,"wt",encoding="utf-8",newline="")
    return path.open("wt",encoding="utf-8",newline="")

def write_json_atomic(path,obj,pretty=True):
    path=Path(path)
    if detect_format(path)["kind"]!="json": raise ValueError("target must be .json[.gz|.bz2]")
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix=f".{path.stem}.",suffix="".join(path.suffixes),dir=path.parent); os.close(fd)
    tmp=Path(name)
    try:
        with _writer(tmp) as fh:
            json.dump(obj,fh,ensure_ascii=False,sort_keys=True,indent=2 if pretty else None,separators=None if pretty else (",",":"))
            fh.write("\n")
        os.replace(tmp,path)
    finally:
        if tmp.exists(): tmp.unlink()

class JsonlWriter:
    def __init__(self,path):
        self.path=Path(path)
        if detect_format(self.path)["kind"]!="jsonl": raise ValueError("target must be .jsonl/.ndjson[.gz|.bz2]")
        self.fh=None; self.count=0; self.logical_sha=hashlib.sha256()
    def __enter__(self):
        self.path.parent.mkdir(parents=True,exist_ok=True); self.fh=_writer(self.path); return self
    def write(self,obj):
        b=canonical_json_line(obj); self.logical_sha.update(b); self.fh.write(b.decode()); self.count+=1
    def __exit__(self,*args):
        if self.fh: self.fh.close()
        self.fh=None
    @property
    def semantic_sha256(self): return self.logical_sha.hexdigest()

def _typename(x):
    if x is None:return "null"
    if isinstance(x,bool):return "bool"
    if isinstance(x,dict):return "object"
    if isinstance(x,list):return "array"
    if isinstance(x,str):return "string"
    if isinstance(x,(int,float)):return "number"
    return type(x).__name__

def inspect_stream(path,strict=True,sample=3):
    errors=[]; types=Counter(); h=hashlib.sha256(); samples=[]; count=0
    for obj in iter_records(path,strict,error_sink=errors):
        count+=1; types[_typename(obj)]+=1; h.update(canonical_json_line(obj))
        if len(samples)<sample:samples.append(obj)
    f=detect_format(path)
    return {"schema":"hawkar.topa.json_rails.inspect.v1","path":str(path),"format":f,"raw_sha256":raw_sha256(path),
            "semantic_record_stream_sha256":h.hexdigest(),"records":count,"type_counts":dict(types),
            "malformed_records":len(errors),"errors_sample":errors[:10],"sample":samples,
            "streaming_note":"JSONL/NDJSON processed record-by-record" if f["kind"]=="jsonl" else "monolithic JSON parsed as one document; prefer JSONL/NDJSON for huge dumps"}

def _resolve(obj,dotted):
    cur=obj
    if not dotted:return cur
    for token in dotted.split("."):
        if isinstance(cur,dict): cur=cur.get(token)
        elif isinstance(cur,list) and token.isdigit() and int(token)<len(cur): cur=cur[int(token)]
        else:return None
    return cur

def search_stream(path,contains,field="",require_all=False,ignore_case=True,regex=None,limit=None,output=None,strict=True):
    needles=[n.casefold() for n in contains] if ignore_case else contains
    rx=re.compile(regex,re.I if ignore_case else 0) if regex else None
    errors=[]; scanned=matched=0; hin=hashlib.sha256(); previews=[]
    cm=JsonlWriter(output) if output else None; writer=cm.__enter__() if cm else None
    try:
        for obj in iter_records(path,strict,error_sink=errors):
            scanned+=1; hin.update(canonical_json_line(obj))
            v=_resolve(obj,field); surface=v if isinstance(v,str) else json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"))
            hay=surface.casefold() if ignore_case else surface
            hits=[n in hay for n in needles]; ok=all(hits) if require_all else (any(hits) if hits else True)
            if ok and (rx.search(surface) if rx else True):
                matched+=1
                if writer: writer.write(obj)
                elif len(previews)<20:previews.append(obj)
                if limit is not None and matched>=limit:break
    finally:
        if cm: cm.__exit__(None,None,None)
    r={"schema":"hawkar.topa.json_rails.search.v1","input":str(path),"format":detect_format(path),
       "input_raw_sha256":raw_sha256(path),"input_semantic_prefix_sha256":hin.hexdigest(),
       "records_scanned":scanned,"records_matched":matched,
       "query":{"contains":contains,"field":field or None,"require_all":require_all,"ignore_case":ignore_case,"regex":regex,"limit":limit},
       "malformed_records":len(errors),"errors_sample":errors[:10],"output":str(output) if output else None,"preview":previews}
    if output:
        r["output_raw_sha256"]=raw_sha256(output); r["output_semantic_sha256"]=writer.semantic_sha256
    return r

def convert_stream(inp,out,strict=True):
    of=detect_format(out); errors=[]; count=0
    if of["kind"]=="jsonl":
        with JsonlWriter(out) as w:
            for obj in iter_records(inp,strict,error_sink=errors): w.write(obj); count+=1
        sem=w.semantic_sha256
    else:
        items=list(iter_records(inp,strict,error_sink=errors)); count=len(items); write_json_atomic(out,items,pretty=False)
        h=hashlib.sha256()
        for x in items:h.update(canonical_json_line(x))
        sem=h.hexdigest()
    return {"schema":"hawkar.topa.json_rails.convert.v1","input":str(inp),"output":str(out),
            "input_format":detect_format(inp),"output_format":of,"records_written":count,"malformed_records":len(errors),
            "input_raw_sha256":raw_sha256(inp),"output_raw_sha256":raw_sha256(out),
            "output_semantic_record_stream_sha256":sem,
            "memory_boundary":"streaming" if of["kind"]=="jsonl" else "output JSON array materialized in memory; use JSONL/NDJSON for huge outputs"}

def self_test():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); rec=[{"id":1,"tag":"Palomar"},{"id":2,"tag":"nuclear"},{"id":3,"tag":"PALOMAR nuclear"}]
        ps=[root/"x.jsonl",root/"x.ndjson",root/"x.jsonl.gz",root/"x.ndjson.gz",root/"x.jsonl.bz2",root/"x.ndjson.bz2"]
        for p in ps:
            with JsonlWriter(p) as w:
                for r in rec:w.write(r)
            assert list(iter_records(p))==rec
            out=root/(p.name+".matches.jsonl.gz")
            s=search_stream(p,["palomar","nuclear"],field="tag",require_all=True,output=out)
            assert s["records_matched"]==1
        for p in [root/"x.json",root/"x.json.gz",root/"x.json.bz2"]:
            write_json_atomic(p,rec); assert list(iter_records(p))==rec
        cv=root/"converted.jsonl.bz2"; assert convert_stream(root/"x.json",cv)["records_written"]==3
        return {"schema":"hawkar.topa.json_rails.self_test.v1","status":"PASS","formats_tested":[p.name for p in ps]+["x.json","x.json.gz","x.json.bz2"]}

def main():
    p=argparse.ArgumentParser(); sp=p.add_subparsers(dest="cmd",required=True)
    q=sp.add_parser("inspect"); q.add_argument("path"); q.add_argument("--sample",type=int,default=3); q.add_argument("--skip-bad",action="store_true")
    q=sp.add_parser("search"); q.add_argument("path"); q.add_argument("--contains",action="append",default=[]); q.add_argument("--field",default=""); q.add_argument("--all",action="store_true"); q.add_argument("--regex"); q.add_argument("--limit",type=int); q.add_argument("--out"); q.add_argument("--receipt"); q.add_argument("--skip-bad",action="store_true")
    q=sp.add_parser("convert"); q.add_argument("input"); q.add_argument("output"); q.add_argument("--skip-bad",action="store_true"); q.add_argument("--receipt")
    sp.add_parser("self-test")
    a=p.parse_args()
    if a.cmd=="self-test": r=self_test()
    elif a.cmd=="inspect": r=inspect_stream(a.path,not a.skip_bad,a.sample)
    elif a.cmd=="search": r=search_stream(a.path,a.contains,a.field,a.all,True,a.regex,a.limit,a.out,not a.skip_bad)
    else:r=convert_stream(a.input,a.output,not a.skip_bad)
    if getattr(a,"receipt",None):write_json_atomic(a.receipt,r)
    print(json.dumps(r,ensure_ascii=False,indent=2,sort_keys=True))
if __name__=="__main__":main()
