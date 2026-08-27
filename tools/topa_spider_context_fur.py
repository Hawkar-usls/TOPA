#!/usr/bin/env python3
"""TOPA ULTRA-SPIDER Context Fur.

Builds provenance-bearing contextual facets around each archival/document node.
The fur is deliberately greedy about *questions* and conservative about *answers*:
unknown values stay UNKNOWN and replaying identical bytes never creates evidence.

Each pass may add observations, conflicts, missing-field acquisition tasks, and
append-only history. This is enrichment/routing, not causal inference.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from collections import defaultdict
from pathlib import Path

SCHEMA="hawkar.topa.spider.context_fur.v1"
DATE_ISO=re.compile(r"\b((?:18|19|20)\d{2}-\d{2}-\d{2})\b")
YEAR=re.compile(r"\b((?:18|19|20)\d{2})\b")
TIME24=re.compile(r"\b([01]?\d|2[0-3]):([0-5]\d)(?::([0-5]\d))?\b")
COORD_PAIR=re.compile(r"(?<!\d)(-?\d{1,2}(?:\.\d+)?)\s*[,;/]\s*(-?\d{1,3}(?:\.\d+)?)(?!\d)")

FACET_FIELDS={
  "physical_event":["event_type","reported_motion","shape","color","duration","altitude","speed","sound","physical_effects"],
  "witness_report":["witness_count","witness_identity_or_role","independence","viewing_geometry","statement_time","statement_chain"],
  "temporal":["event_date","event_time_local","event_time_utc","timezone","time_uncertainty","report_delay"],
  "geospatial":["place_name","latitude","longitude","coordinate_uncertainty","elevation","terrain_context"],
  "weather":["temperature","cloud_cover","visibility","precipitation","wind_speed","wind_direction","pressure","weather_station_or_reanalysis"],
  "illumination_astronomy":["sun_altitude","sun_azimuth","twilight_state","moon_phase","moon_altitude","moon_azimuth","bright_planets","meteor_activity"],
  "geospace":["kp","ap","dst","solar_wind","solar_flares","geomagnetic_storm_state","auroral_context"],
  "atmospheric_environment":["lightning","inversion_layer","contrails","cloud_type","balloon_activity","atmospheric_optics"],
  "aviation":["known_aircraft","air_routes","airport_context","atc_or_radar_report","notam","military_exercise","flight_track"],
  "space_activity":["satellite_pass","reentry","launch_activity","rocket_stage","space_debris_candidate"],
  "sensors":["sensor_modalities","radar_parameters","camera_parameters","sensor_calibration","raw_data_available","chain_of_custody"],
  "institutional_routing":["originating_body","recipients","routing_chain","classification_status","foia_status","investigation_unit","disposition"],
  "media_amplification":["first_publication","publication_delay","syndication_chain","headline_drift","report_volume","publicity_trigger"],
  "archive_provenance":["provider","archive_id","record_group","series","source_url","document_date","declassification_or_release_date","copy_lineage"],
  "conventional_hypotheses":["aircraft","balloon","astronomical","reentry","weather_optical","sensor_artifact","hoax_misreport","experimental_platform"],
  "contradiction_disconfirmation":["contradicting_source","negative_control","later_identification","missing_expected_signature","failed_replication"],
  "information_flow":["source_to_source_path","same_source_reprints","independent_witness_count","institution_media_feedback","temporal_order_of_claims"],
  "uncertainty_missingness":["known_unknowns","conflicts","precision_limits","unavailable_primary_source","blocked_provider","unresolved_questions"]
}

PROVIDER_HINTS={
  "weather":["NOAA/NCEI station data","ERA5/reanalysis","official meteorological archive"],
  "illumination_astronomy":["deterministic ephemeris","USNO/JPL public ephemeris"],
  "geospace":["NOAA SWPC","GFZ geomagnetic indices","NASA public space-weather archive"],
  "atmospheric_environment":["meteorological archive","lightning archive where public","balloon/upper-air logs"],
  "aviation":["FAA/NTSB/ATC records","public historical flight/airport records","military exercise records"],
  "space_activity":["CelesTrak/public TLE history where available","official launch/reentry logs","NASA/USSPACECOM public notices"],
  "media_amplification":["newspaper/library archives","wire-service archives","official press records"],
  "institutional_routing":["agency FOIA reading rooms","NARA record series","presidential libraries"],
  "archive_provenance":["source archive metadata","finding aids","release/declassification ledgers"]
}

LAWS=[
  "CONTEXT_FACET_IS_NOT_CAUSATION",
  "UNKNOWN_STAYS_UNKNOWN",
  "REPLAY_IS_NOT_NEW_EVIDENCE",
  "SAME_SOURCE_REPRINT_IS_NOT_INDEPENDENT_WITNESS",
  "WEATHER_MATCH_IS_NOT_EVENT_IDENTIFICATION",
  "ASTRONOMICAL_MATCH_IS_A_HYPOTHESIS_UNTIL_GEOMETRY_AND_TIME_AGREE",
  "MISSING_DATA_IS_A_FIRST_CLASS_RESULT",
  "CONFLICTS_ARE_PRESERVED_NOT_AVERAGED_AWAY"
]

def canon(o): return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def sh(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()
def read_jsonl(path):
    p=Path(path)
    if not p.exists(): return []
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
def write_jsonl(path,rows):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text("".join(canon(r)+"\n" for r in rows),encoding="utf-8")
def doc_id(r): return f"doc:{r.get('provider','?')}:{r.get('archive_id') or sh(str(r.get('source_url','')))[:16]}"
def text_of(r):
    bits=[r.get("title"),r.get("text"),r.get("agency")]
    bits += list(r.get("relation_tags") or [])
    raw=r.get("raw_metadata")
    if isinstance(raw,dict):
        for k in ("title","scopeAndContentNote","dateNote","arrangement","description","subject","place","location"):
            if raw.get(k): bits.append(str(raw[k]))
    return " ".join(str(x) for x in bits if x)
def obs(field,value,source_ref,method="SOURCE_TEXT_EXTRACTION",confidence=0.45):
    o={"field":field,"value":value,"source_ref":source_ref,"method":method,"confidence":round(float(confidence),3)}
    o["evidence_signature"]=sh(canon({k:o[k] for k in ("field","value","source_ref","method")}))
    return o

def extracted_observations(r):
    sid=doc_id(r); src=r.get("source_url") or sid; t=text_of(r); out=defaultdict(list)
    # Archive provenance is directly source-bound metadata.
    for f,v in (("provider",r.get("provider")),("archive_id",r.get("archive_id")),("source_url",r.get("source_url")),("document_date",r.get("document_date"))):
        if v not in (None,""): out["archive_provenance"].append(obs(f,v,src,"STRUCTURED_METADATA",0.9))
    if r.get("agency"): out["institutional_routing"].append(obs("originating_body",r["agency"],src,"STRUCTURED_METADATA",0.75))
    # Dates/times only become candidate temporal facts; text can contain multiple dates.
    dates=list(dict.fromkeys(DATE_ISO.findall(t)))
    if dates:
        for d in dates: out["temporal"].append(obs("event_date",d,src,"TEXT_DATE_CANDIDATE",0.45))
    else:
        years=list(dict.fromkeys(YEAR.findall(t)))
        if len(years)==1: out["temporal"].append(obs("event_date",years[0],src,"YEAR_ONLY_CANDIDATE",0.25))
    times=[]
    for m in TIME24.finditer(t):
        hh,mm,ss=m.groups(); times.append(f"{int(hh):02d}:{mm}"+(f":{ss}" if ss else ""))
    for tm in list(dict.fromkeys(times)): out["temporal"].append(obs("event_time_local",tm,src,"TEXT_TIME_CANDIDATE",0.35))
    # Decimal coordinate pairs are candidates until independently validated.
    for a,b in COORD_PAIR.findall(t):
        lat,lon=float(a),float(b)
        if -90<=lat<=90 and -180<=lon<=180:
            out["geospatial"].append(obs("latitude",lat,src,"TEXT_COORDINATE_CANDIDATE",0.4))
            out["geospatial"].append(obs("longitude",lon,src,"TEXT_COORDINATE_CANDIDATE",0.4))
            break
    # Tags provide weak context, never physical truth.
    tags=[str(x) for x in (r.get("relation_tags") or [])]
    for tag in tags:
        low=tag.lower()
        if any(x in low for x in ("ukraine","odesa","odessa","kyiv","kiev","roswell","area 51")):
            out["geospatial"].append(obs("place_name",tag,src,"TAG_CONTEXT",0.3))
        if any(x in low for x in ("cia","fbi","nsa","nara","air force","odni","osd")):
            out["institutional_routing"].append(obs("routing_chain",tag,src,"TAG_CONTEXT",0.3))
    return out

def facet_status(observations,total_fields):
    fields={o.get("field") for o in observations}
    if not observations: return "UNKNOWN"
    return "RESOLVED" if len(fields)>=len(total_fields) else "PARTIAL"

def build_one(r,pass_id="FUR-P1"):
    ex=extracted_observations(r); facets={}; queue=[]; resolved=0; total=sum(len(v) for v in FACET_FIELDS.values())
    for name,fields in FACET_FIELDS.items():
        oo=ex.get(name,[]); have={o["field"] for o in oo}; missing=[f for f in fields if f not in have]; resolved+=len(have)
        facets[name]={"status":facet_status(oo,fields),"observations":oo,"missing":missing,"conflicts":[],"provider_hints":PROVIDER_HINTS.get(name,[])}
        if missing:
            queue.append({"facet":name,"missing_fields":missing,"priority":"HIGH" if name in {"temporal","geospatial","weather","illumination_astronomy","witness_report","sensors"} else "NORMAL","provider_hints":PROVIDER_HINTS.get(name,[]),"authority":"ACQUISITION_TASK_ONLY"})
    coverage=resolved/total if total else 0.0
    return {"schema":SCHEMA,"subject_id":doc_id(r),"pass_id":pass_id,"source_record_sha256":r.get("record_sha256"),"context_fur":facets,"coverage":{"resolved_fields":resolved,"total_fields":total,"score":round(coverage,6)},"acquisition_queue":queue,"history":[{"pass_id":pass_id,"coverage":round(coverage,6),"fresh_observations":sum(len(v) for v in ex.values()),"conflicts":0}],"laws":LAWS,"claim_authority":"CONTEXT_ENRICHMENT_AND_DISCOVERY_ROUTING_ONLY"}

def merge_one(prev,new,pass_id):
    out=json.loads(json.dumps(prev)); out["pass_id"]=pass_id; fresh=0; conflicts=0
    for name,fields in FACET_FIELDS.items():
        pf=out["context_fur"].setdefault(name,{"status":"UNKNOWN","observations":[],"missing":fields[:],"conflicts":[],"provider_hints":PROVIDER_HINTS.get(name,[])})
        nf=new["context_fur"].get(name,{"observations":[]})
        sigs={o.get("evidence_signature") for o in pf.get("observations",[])}
        by_field=defaultdict(list)
        for o in pf.get("observations",[]): by_field[o.get("field")].append(o)
        for o in nf.get("observations",[]):
            if o.get("evidence_signature") in sigs: continue
            # Preserve differing source-bound values as a conflict; never average them.
            differing=[x for x in by_field[o.get("field")] if canon(x.get("value"))!=canon(o.get("value"))]
            if differing:
                c={"field":o.get("field"),"existing":[x.get("value") for x in differing],"new":o.get("value"),"source_ref":o.get("source_ref"),"pass_id":pass_id}
                pf.setdefault("conflicts",[]).append(c); conflicts+=1
            pf.setdefault("observations",[]).append(o); sigs.add(o.get("evidence_signature")); by_field[o.get("field")].append(o); fresh+=1
        have={o.get("field") for o in pf.get("observations",[])}
        pf["missing"]=[f for f in fields if f not in have]
        pf["status"]="CONFLICT" if pf.get("conflicts") else facet_status(pf.get("observations",[]),fields)
    resolved=sum(len({o.get("field") for o in out["context_fur"][n].get("observations",[])}) for n in FACET_FIELDS)
    total=sum(len(v) for v in FACET_FIELDS.values()); cov=resolved/total if total else 0.0
    out["coverage"]={"resolved_fields":resolved,"total_fields":total,"score":round(cov,6)}
    out["acquisition_queue"]=[]
    for n,f in out["context_fur"].items():
        if f.get("missing"):
            out["acquisition_queue"].append({"facet":n,"missing_fields":f["missing"],"priority":"HIGH" if n in {"temporal","geospatial","weather","illumination_astronomy","witness_report","sensors"} else "NORMAL","provider_hints":PROVIDER_HINTS.get(n,[]),"authority":"ACQUISITION_TASK_ONLY"})
    out.setdefault("history",[]).append({"pass_id":pass_id,"coverage":round(cov,6),"fresh_observations":fresh,"conflicts":conflicts})
    return out

def build(records,pass_id): return [build_one(r,pass_id) for r in records]
def merge(prev_rows,new_rows,pass_id):
    pm={x["subject_id"]:x for x in prev_rows}; nm={x["subject_id"]:x for x in new_rows}; out=[]
    for sid in sorted(set(pm)|set(nm)):
        if sid in pm and sid in nm: out.append(merge_one(pm[sid],nm[sid],pass_id))
        elif sid in pm:
            x=json.loads(json.dumps(pm[sid])); x["pass_id"]=pass_id; x.setdefault("history",[]).append({"pass_id":pass_id,"coverage":x.get("coverage",{}).get("score",0),"fresh_observations":0,"conflicts":0,"note":"SUBJECT_NOT_REOBSERVED_THIS_PASS"}); out.append(x)
        else: out.append(nm[sid])
    return out

def receipt(rows,pass_id):
    statuses=defaultdict(int); queued=0; conflicts=0
    for r in rows:
        queued+=len(r.get("acquisition_queue",[]))
        for f in r.get("context_fur",{}).values(): statuses[f.get("status","UNKNOWN")]+=1; conflicts+=len(f.get("conflicts",[]))
    return {"schema":"hawkar.topa.spider.context_fur.receipt.v1","status":"PASS","pass_id":pass_id,"subjects":len(rows),"facet_status_counts":dict(sorted(statuses.items())),"acquisition_tasks":queued,"conflicts":conflicts,"stream_sha256":sh("".join(canon(r)+"\n" for r in rows)),"laws":LAWS,"note":"Coverage measures how much context is populated, not how true or extraordinary a claim is."}

def self_test():
    r={"provider":"NARA","archive_id":"x","title":"Event 1983-12-20 21:30 Ukraine","source_url":"https://example/x","agency":"USAF","relation_tags":["Ukraine"]}
    p1=build([r],"T1")[0]; p2=merge([p1],build([r],"T2"),"T2")[0]
    assert p1["coverage"]["score"]>0 and p2["history"][-1]["fresh_observations"]==0
    assert p2["context_fur"]["weather"]["status"]=="UNKNOWN"
    return {"schema":SCHEMA+".self_test","status":"PASS","replay_not_new_evidence":True,"unknown_weather_preserved":True,"acquisition_queue_present":bool(p2["acquisition_queue"])}

def main():
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest="cmd",required=True); sp.add_parser("self-test")
    b=sp.add_parser("build"); b.add_argument("--records",required=True); b.add_argument("--out",required=True); b.add_argument("--receipt",required=True); b.add_argument("--pass-id",default="FUR-P1")
    m=sp.add_parser("merge"); m.add_argument("--previous",required=True); m.add_argument("--records",required=True); m.add_argument("--out",required=True); m.add_argument("--receipt",required=True); m.add_argument("--pass-id",required=True)
    a=ap.parse_args()
    if a.cmd=="self-test": print(json.dumps(self_test(),ensure_ascii=False,indent=2)); return 0
    new=build(read_jsonl(a.records),a.pass_id)
    rows=new if a.cmd=="build" else merge(read_jsonl(a.previous),new,a.pass_id)
    write_jsonl(a.out,rows); rc=receipt(rows,a.pass_id); Path(a.receipt).write_text(json.dumps(rc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(json.dumps(rc,ensure_ascii=False,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
