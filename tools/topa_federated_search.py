#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, shutil, sqlite3
from pathlib import Path

def read_jsonl(path):
    p=Path(path)
    if not p.exists():return
    with p.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():yield json.loads(line)

def normalize_record(rec,source):
    rid=str(rec.get("arxiv_id") or rec.get("archive_id") or rec.get("path") or rec.get("record_sha256") or "")
    title=str(rec.get("title") or rec.get("path") or rid)
    body=str(rec.get("abstract") or rec.get("text") or rec.get("purpose") or "")
    extra=" ".join(str(x) for x in (rec.get("authors") or rec.get("roles") or rec.get("relation_tags") or []))
    return {"source":source,"id":rid,"title":title,"body":body,"extra":extra,"payload":rec}

def collect(repo=None,arxiv=None,archive=None):
    out=[]
    for src,path in [("repo",repo),("arxiv",arxiv),("archive",archive)]:
        if not path:continue
        for r in read_jsonl(path):out.append(normalize_record(r,src))
    return out

def build_sqlite(rows,db):
    p=Path(db);p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():p.unlink()
    c=sqlite3.connect(p)
    try:
        c.execute("CREATE TABLE docs (k INTEGER PRIMARY KEY, payload TEXT NOT NULL)")
        c.execute("CREATE VIRTUAL TABLE docs_fts USING fts5(source UNINDEXED, id UNINDEXED, title, body, extra)")
        for i,r in enumerate(rows):
            c.execute("INSERT INTO docs(k,payload) VALUES (?,?)",(i,json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))))
            c.execute("INSERT INTO docs_fts(rowid,source,id,title,body,extra) VALUES (?,?,?,?,?,?)",(i,r["source"],r["id"],r["title"],r["body"],r["extra"]))
        c.commit()
    finally:c.close()
    return {"engine":"sqlite_fts5","documents":len(rows),"path":str(p)}

def search_sqlite(db,q,limit):
    c=sqlite3.connect(db);c.row_factory=sqlite3.Row
    try:
        words=[w for w in q.replace('"',' ').split() if len(w)>=2];match=" OR ".join(f'"{w}"' for w in words) or '""'
        rows=c.execute("SELECT d.payload,bm25(docs_fts,0,0,3.0,1.5,1.0) s FROM docs_fts JOIN docs d ON d.k=docs_fts.rowid WHERE docs_fts MATCH ? ORDER BY s LIMIT ?",(match,limit)).fetchall()
        return [dict(json.loads(r["payload"]),search_score=float(r["s"]),rank=i+1) for i,r in enumerate(rows)]
    finally:c.close()

def tantivy_available():
    try:import tantivy;return True
    except Exception:return False

def build_tantivy(rows,index_dir):
    import tantivy
    p=Path(index_dir)
    if p.exists():shutil.rmtree(p)
    p.mkdir(parents=True)
    s=tantivy.SchemaBuilder();s.add_text_field("source",stored=True,tokenizer_name="raw");s.add_text_field("rid",stored=True,tokenizer_name="raw")
    s.add_text_field("title",stored=True,tokenizer_name="en_stem");s.add_text_field("body",stored=True,tokenizer_name="en_stem");s.add_text_field("extra",stored=True);s.add_text_field("payload",stored=True,tokenizer_name="raw")
    schema=s.build();idx=tantivy.Index(schema,path=str(p))
    with idx.writer() as w:
        for r in rows:w.add_document(tantivy.Document(source=[r["source"]],rid=[r["id"]],title=[r["title"]],body=[r["body"]],extra=[r["extra"]],payload=[json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))]))
    return {"engine":"tantivy","documents":len(rows),"path":str(p)}

def search_tantivy(index_dir,q,limit):
    import tantivy
    idx=tantivy.Index.open(str(index_dir));idx.reload();s=idx.searcher();query,errors=idx.parse_query_lenient(q,["title","body","extra"],field_boosts={"title":3.0,"body":1.5,"extra":1.0});res=s.search(query,limit);out=[]
    for i,(score,addr) in enumerate(res.hits,1):
        d=s.doc(addr);r=json.loads(str(d.get_first("payload")));r["search_score"]=float(score);r["rank"]=i;r["query_warnings"]=[str(x) for x in errors];out.append(r)
    return out

def self_test():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p=Path(td);a=p/"a.jsonl";a.write_text('{"archive_id":"1","title":"tachyon Ukraine","text":"reverse information"}\n',encoding="utf-8")
        rows=collect(archive=a);rc=build_sqlite(rows,p/"x.db");res=search_sqlite(p/"x.db","tachyon",5)
        assert rc["documents"]==1 and res and res[0]["source"]=="archive"
        return {"schema":"hawkar.topa.federated_search.self_test.v1","status":"PASS","sqlite":True}

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest="cmd",required=True);sp.add_parser("self-test")
    b=sp.add_parser("build");b.add_argument("--repo");b.add_argument("--arxiv");b.add_argument("--archive");b.add_argument("--engine",choices=["auto","sqlite","tantivy"],default="auto");b.add_argument("--out",required=True)
    q=sp.add_parser("search");q.add_argument("--engine",choices=["sqlite","tantivy"],required=True);q.add_argument("--index",required=True);q.add_argument("--query",required=True);q.add_argument("--limit",type=int,default=20)
    a=ap.parse_args()
    if a.cmd=="self-test":print(json.dumps(self_test(),indent=2));return 0
    if a.cmd=="build":
        rows=collect(a.repo,a.arxiv,a.archive);eng=a.engine
        if eng=="auto":eng="tantivy" if tantivy_available() else "sqlite"
        rc=build_tantivy(rows,a.out) if eng=="tantivy" else build_sqlite(rows,a.out);print(json.dumps(rc,indent=2));return 0
    res=search_tantivy(a.index,a.query,a.limit) if a.engine=="tantivy" else search_sqlite(a.index,a.query,a.limit)
    print(json.dumps({"schema":"hawkar.topa.federated_search.results.v1","query":a.query,"results":res,"claim_ceiling":"RANK_IS_DISCOVERY_PRIORITY_NOT_TRUTH"},ensure_ascii=False,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
