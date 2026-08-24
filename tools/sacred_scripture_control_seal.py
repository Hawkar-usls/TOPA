#!/usr/bin/env python3
"""Fail-closed source/slice sealer for preregistered TOPA matched controls."""
from __future__ import annotations
import argparse, hashlib, html.parser, json, re, unicodedata, urllib.request
from datetime import datetime, timezone
from pathlib import Path

UA = "TOPA-control-seal/0.2 (+https://github.com/Hawkar-usls/TOPA)"
EXPECTED_SLOTS = [f"C{i:02d}" for i in range(1, 9)]

def h(b: bytes) -> str: return hashlib.sha256(b).hexdigest()

def fetch(url: str, timeout=120):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,*/*;q=0.8"})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        raw=r.read(); ct=r.headers.get("Content-Type")
    if not raw: raise RuntimeError(f"empty response: {url}")
    return raw,ct

class Visible(html.parser.HTMLParser):
    BLOCK={"address","article","aside","blockquote","br","dd","div","dl","dt","figcaption","figure","footer","h1","h2","h3","h4","h5","h6","header","hr","li","main","nav","ol","p","pre","section","table","tbody","td","tfoot","th","thead","tr","ul"}
    def __init__(self): super().__init__(convert_charrefs=True); self.parts=[]; self.skip=0
    def handle_starttag(self,tag,attrs):
        tag=tag.lower()
        if tag in {"script","style","noscript"}: self.skip+=1
        elif not self.skip and tag in self.BLOCK: self.parts.append("\n")
    def handle_endtag(self,tag):
        tag=tag.lower()
        if tag in {"script","style","noscript"}:
            if self.skip: self.skip-=1
        elif not self.skip and tag in self.BLOCK: self.parts.append("\n")
    def handle_data(self,data):
        if not self.skip: self.parts.append(data)

def flow(s:str)->str:
    s=unicodedata.normalize("NFC",s.replace("\r\n","\n").replace("\r","\n"))
    return re.sub(r"\s+"," ",s).strip()

def visible(raw:bytes)->str:
    decoded=None
    for enc in ("utf-8-sig","utf-8","windows-1252","iso-8859-1"):
        try: decoded=raw.decode(enc,errors="strict"); break
        except UnicodeDecodeError: pass
    if decoded is None: raise RuntimeError("source HTML could not be decoded losslessly")
    p=Visible(); p.feed(decoded); p.close(); return flow("".join(p.parts))

def extract(text:str,start_marker:str,end_marker:str):
    start,end=flow(start_marker),flow(end_marker)
    starts=[m.start() for m in re.finditer(re.escape(start),text)]
    if not starts: raise RuntimeError(f"start marker not found: {start[:120]}")
    candidates=[]
    for pos in starts:
        ep=text.find(end,pos+len(start))
        if ep>=0: candidates.append((ep-pos,pos,ep))
    if not candidates: raise RuntimeError(f"end marker not found after any start: {end[:120]}")
    # Repeated headings occur in Gutenberg TOCs. The frozen locus is heading-to-heading;
    # choose the largest valid occurrence span, which deterministically selects body text
    # over its short TOC echo without changing source identity or locus boundaries.
    span,chosen,endpos=max(candidates,key=lambda x:(x[0],x[1]))
    locus=text[chosen:endpos].strip()
    if len(locus)<300: raise RuntimeError(f"implausibly short body locus after TOC disambiguation: {len(locus)} chars")
    b=(unicodedata.normalize("NFC",locus)+"\n").encode("utf-8")
    return b,{"start_occurrences_in_source":len(starts),"valid_start_end_candidates":len(candidates),"selection_rule":"MAXIMUM_VALID_PREREGISTERED_HEADING_SPAN_TO_AVOID_TOC_ECHO","selected_span_flow_chars":span,"selected_start_offset_flow_chars":chosen,"selected_end_offset_flow_chars":endpos,"canonical_start_marker":start,"canonical_end_marker":end}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--freeze",default="research/sacred-scriptures/CONTROL_CANDIDATE_FREEZE.v0.1.json"); ap.add_argument("--out",required=True); a=ap.parse_args()
    fp=Path(a.freeze); fr=fp.read_bytes(); freeze=json.loads(fr.decode("utf-8")); controls=freeze.get("controls",[])
    if [c.get("slot") for c in controls]!=EXPECTED_SLOTS: raise SystemExit("control freeze slot/order mismatch")
    sealed=[]; errors=[]
    for c in controls:
        try:
            raw,ct=fetch(c["source_url"]); head=raw[:4096].lower()
            if b"<html" not in head and b"<!doctype html" not in head: raise RuntimeError("download did not look like HTML")
            sb,ex=extract(visible(raw),c["start_marker"],c["end_marker"])
            r={k:v for k,v in c.items() if k not in {"start_marker","end_marker"}}
            r.update({"source_download_bytes":len(raw),"source_sha256":h(raw),"source_content_type":ct,"slice_bytes":len(sb),"slice_sha256":h(sb),"slice_seal_type":"NFC_UTF8_FLOW_NORMALIZED_VISIBLE_TEXT_SHA256","normalization":"HTML visible text only; script/style/noscript removed; NFC; all Unicode whitespace collapsed to one ASCII space; final LF","extraction_receipt":ex,"status":"SEALED"})
            sealed.append(r); print(f"CONTROL_SEAL_{c['slot']}=PASS")
        except Exception as e:
            errors.append({"slot":c["slot"],"error":f"{type(e).__name__}: {e}"}); print(f"CONTROL_SEAL_{c['slot']}=FAIL: {e}")
    by={x["slot"]:x for x in sealed}; ok=all(s in by for s in EXPECTED_SLOTS) and not errors
    out={"schema":"topa.sacred_scriptures.control_seal_run.v0.1","executed_at_utc":datetime.now(timezone.utc).isoformat(),"status":"EIGHT_OF_EIGHT_REAL_CONTROLS_SEALED" if ok else "CONTROL_SEAL_FAILURE","control_freeze_path":str(fp),"control_freeze_sha256":h(fr),"parser_version":"0.2_MAX_VALID_SPAN_TOC_DISAMBIGUATION","required_slots":EXPECTED_SLOTS,"controls":[by[s] for s in EXPECTED_SLOTS if s in by],"sealed_count":len(by),"required_count":8,"errors":errors,"rights_policy":"Receipts store source identity, rights state and hashes only; downloaded source texts are not mirrored by this artifact.","double_coding_permission_from_real_controls":ok,"score_permission":False,"epistemic_effect":"CONTROL_PROVENANCE_AND_IMMUTABILITY_ONLY_NO_RESEARCH_RESULT_CREDIT"}
    p=Path(a.out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"TOPA_REAL_CONTROLS={'PASS' if ok else 'FAIL'}"); print(f"CONTROL_SEAL_COUNT={len(by)}/8"); print(f"RECEIPT={p}"); return 0 if ok else 2
if __name__=="__main__": raise SystemExit(main())
