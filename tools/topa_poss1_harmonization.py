#!/usr/bin/env python3
"""TOPA POSS-I closed/open harmonization engine v1.

Frozen estimand per cohort:
    artifact-score-weighted candidate rate per actual observing opportunity

Raw artifact scores are never overwritten or called calibrated probabilities.
The same calendar/window/opportunity statistic is used for every cohort.
Significance is evaluated with exhaustive circular shifts of the frozen
nuclear-event calendar against fixed observations and fixed outcomes.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import statistics
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any

from topa_json_rails import JsonlWriter, iter_records, raw_sha256, write_json_atomic


def parse_date(x: Any) -> dt.date:
    return dt.date.fromisoformat(str(x)[:10])


def get_field(obj: Any, dotted: str) -> Any:
    cur = obj
    for token in dotted.split("."):
        if isinstance(cur, dict) and token in cur:
            cur = cur[token]
        else:
            raise KeyError(f"missing field {dotted!r}")
    return cur


def daterange(start: dt.date, end: dt.date) -> list[dt.date]:
    return [start + dt.timedelta(days=i) for i in range((end-start).days + 1)]


def load_event_dates(path: str, field: str, start: dt.date, end: dt.date) -> list[dt.date]:
    dates=set()
    for row in iter_records(path):
        d=parse_date(get_field(row,field))
        if start <= d <= end: dates.add(d)
    out=sorted(dates)
    if not out: raise ValueError("nuclear event manifest has no events in study window")
    return out


def score_summary(values: list[float]) -> dict[str, Any]:
    if not values: return {"n":0}
    mean=statistics.fmean(values)
    var=statistics.fmean([(x-mean)**2 for x in values])
    unique=len(set(values))
    return {
        "n":len(values),"min":min(values),"max":max(values),"mean":mean,
        "population_sd":math.sqrt(var),"distinct_values":unique,
        "distinct_fraction":unique/len(values),"zeros":sum(x==0 for x in values),
        "ones":sum(x==1 for x in values),
        "semantic_note":"RAW_ARTIFACT_SCORE__NOT_CALIBRATED_PROBABILITY"
    }


def load_cohort(spec: dict[str, Any], allowed_dates: set[dt.date] | None=None) -> dict[str, Any]:
    cpath=spec["candidates_path"]; opath=spec["opportunity_path"]
    dfield=spec.get("candidate_date_field","date_obs")
    sfield=spec.get("raw_score_field","artifact_score_raw")
    odfield=spec.get("opportunity_date_field","date_obs")
    ofield=spec.get("opportunity_field","opportunity")
    idfield=spec.get("candidate_id_field","candidate_id")
    nightly_count=defaultdict(int); nightly_weight=defaultdict(float)
    threshold_counts={float(t):defaultdict(int) for t in spec.get("score_thresholds",[])}
    scores=[]; score_hash=hashlib.sha256(); candidate_rows=0; excluded=0
    for row in iter_records(cpath):
        date=parse_date(get_field(row,dfield))
        if allowed_dates is not None and date not in allowed_dates:
            excluded+=1; continue
        score=float(get_field(row,sfield))
        if not math.isfinite(score): raise ValueError(f"non-finite raw artifact score on {date}")
        if score < 0.0 or score > 1.0:
            raise ValueError(f"raw artifact score outside [0,1] on {date}: {score}; do not silently clip")
        cid=row.get(idfield,f"row:{candidate_rows}") if isinstance(row,dict) else f"row:{candidate_rows}"
        candidate_rows+=1; nightly_count[date]+=1; nightly_weight[date]+=score; scores.append(score)
        score_hash.update(f"{date.isoformat()}\t{cid}\t{score:.17g}\n".encode())
        for threshold,counts in threshold_counts.items():
            if score >= threshold: counts[date]+=1
    opportunity=defaultdict(float); opportunity_rows=0
    for row in iter_records(opath):
        date=parse_date(get_field(row,odfield))
        if allowed_dates is not None and date not in allowed_dates: continue
        value=float(get_field(row,ofield))
        if not math.isfinite(value) or value < 0: raise ValueError(f"invalid observing opportunity on {date}: {value}")
        opportunity[date]+=value; opportunity_rows+=1
    observed=sorted(d for d,o in opportunity.items() if o>0)
    if not observed: raise ValueError(f"{spec['id']}: no positive observing opportunity")
    orphan=sorted(d for d in nightly_count if opportunity[d] <= 0)
    if orphan: raise ValueError(f"{spec['id']}: candidate dates without positive opportunity: {orphan[:20]}")
    return {
        "id":spec["id"],"candidate_rows":candidate_rows,"candidate_rows_excluded_by_date_filter":excluded,
        "opportunity_rows":opportunity_rows,"nightly_count":nightly_count,"nightly_weight":nightly_weight,
        "threshold_counts":threshold_counts,"opportunity":opportunity,"observed_dates":observed,
        "score_summary":score_summary(scores),"score_stream_sha256":score_hash.hexdigest(),
        "candidate_file_raw_sha256":raw_sha256(cpath),"opportunity_file_raw_sha256":raw_sha256(opath),
        "raw_score_field":sfield
    }


def exposed_dates_for_shift(base_events,start,n_days,shift,window_days):
    out=set()
    for event in base_events:
        idx=(event-start).days; shifted=(idx+shift)%n_days
        for delta in range(-window_days,window_days+1):
            j=(shifted+delta)%n_days; out.add(start+dt.timedelta(days=j))
    return out


def rate_ratio(nightly,opportunity,observed_dates,exposed):
    ye=yu=oe=ou=0.0; ne=nu=0
    for d in observed_dates:
        y=float(nightly.get(d,0.0)); o=float(opportunity[d])
        if d in exposed: ye+=y; oe+=o; ne+=1
        else: yu+=y; ou+=o; nu+=1
    if oe<=0 or ou<=0: return {"valid":False,"reason":"zero exposed or unexposed opportunity"}
    re=ye/oe; ru=yu/ou; rr=re/ru if ru>0 else math.inf
    return {"valid":True,"exposed_observed_dates":ne,"unexposed_observed_dates":nu,
            "exposed_outcome":ye,"unexposed_outcome":yu,"exposed_opportunity":oe,"unexposed_opportunity":ou,
            "rate_exposed":re,"rate_unexposed":ru,"rate_ratio":rr}


def exact_shift_test(nightly,opportunity,observed_dates,event_dates,start,end,window_days):
    n_days=(end-start).days+1
    observed_exposure=exposed_dates_for_shift(event_dates,start,n_days,0,window_days)
    obs=rate_ratio(nightly,opportunity,observed_dates,observed_exposure)
    if not obs.get("valid"): raise ValueError(f"observed statistic invalid: {obs}")
    observed_rr=float(obs["rate_ratio"]); all_rr=[]; invalid=0
    for shift in range(n_days):
        exp=exposed_dates_for_shift(event_dates,start,n_days,shift,window_days)
        res=rate_ratio(nightly,opportunity,observed_dates,exp)
        if not res.get("valid"): invalid+=1; continue
        all_rr.append(float(res["rate_ratio"]))
    if not all_rr: raise ValueError("all circular-shift null statistics invalid")
    ge=sum(rr>=observed_rr for rr in all_rr); median=statistics.median(all_rr)
    log_obs=abs(math.log(observed_rr/median)) if observed_rr>0 and median>0 else math.inf
    two=sum((abs(math.log(rr/median)) if rr>0 and median>0 else math.inf)>=log_obs for rr in all_rr)
    return {"observed":obs,"null":{"method":"EXHAUSTIVE_CIRCULAR_SHIFT_OF_FROZEN_NUCLEAR_CALENDAR",
            "calendar_days":n_days,"valid_shifts":len(all_rr),"invalid_shifts":invalid,
            "null_rr_median":median,"null_rr_mean":statistics.fmean(all_rr),
            "p_upper_exact":ge/len(all_rr),"p_two_sided_log_distance_from_null_median":two/len(all_rr)}}


def evaluate_cohort(cohort,event_dates,start,end,window_days):
    weighted=exact_shift_test(cohort["nightly_weight"],cohort["opportunity"],cohort["observed_dates"],event_dates,start,end,window_days)
    raw_count=exact_shift_test(cohort["nightly_count"],cohort["opportunity"],cohort["observed_dates"],event_dates,start,end,window_days)
    thresholds={}
    for threshold,counts in cohort["threshold_counts"].items():
        thresholds[str(threshold)]=exact_shift_test(counts,cohort["opportunity"],cohort["observed_dates"],event_dates,start,end,window_days)
    return {"cohort_id":cohort["id"],"records":{"candidate_rows":cohort["candidate_rows"],
            "opportunity_rows":cohort["opportunity_rows"],"observed_dates":len(cohort["observed_dates"])},
            "provenance":{"candidate_file_raw_sha256":cohort["candidate_file_raw_sha256"],
            "opportunity_file_raw_sha256":cohort["opportunity_file_raw_sha256"],"score_stream_sha256":cohort["score_stream_sha256"]},
            "raw_score_distribution":cohort["score_summary"],"primary_artifact_score_weighted_rate":weighted,
            "secondary_unweighted_candidate_rate":raw_count,"secondary_prespecified_score_thresholds":thresholds,
            "claim_ceiling":"TEMPORAL_ASSOCIATION_UNDER_FROZEN_EXPOSURE_NORMALIZED_STATISTIC_ONLY"}


def run_config(config):
    start=parse_date(config["study_start"]); end=parse_date(config["study_end"])
    window_days=int(config.get("nuclear_window_days",1))
    events=load_event_dates(config["nuclear_manifest_path"],config.get("nuclear_date_field","date"),start,end)
    cohorts=[load_cohort(spec) for spec in config["cohorts"]]
    results=[evaluate_cohort(c,events,start,end,window_days) for c in cohorts]
    intersection_results=[]
    if len(cohorts)>=2:
        intersection=set(cohorts[0]["observed_dates"])
        for c in cohorts[1:]: intersection &= set(c["observed_dates"])
        if intersection:
            for spec in config["cohorts"]:
                c=load_cohort(spec,allowed_dates=intersection)
                intersection_results.append(evaluate_cohort(c,events,start,end,window_days))
    return {"schema":"hawkar.topa.poss1_closed_open_harmonization.receipt.v1",
            "experiment_id":config.get("experiment_id","TOPA_POSS1_CLOSED_OPEN_HARMONIZATION_01"),
            "status":"EXECUTED_ON_SUPPLIED_COHORTS","study_window":[start.isoformat(),end.isoformat()],
            "nuclear_window_days":window_days,"nuclear_event_dates_in_window":len(events),
            "nuclear_manifest_raw_sha256":raw_sha256(config["nuclear_manifest_path"]),"cohorts":results,
            "common_observed_date_intersection":{"executed":bool(intersection_results),"cohorts":intersection_results},
            "score_policy":{"raw_score_immutable":True,"raw_score_called_probability":False,
            "calibration_performed_here":False,"distribution_collapse_possible_here":False,
            "note":"Calibration, if later added, must be a sidecar view and must never replace raw scores."},
            "decision_guard":{"positive_in_one_cohort_only":"DATASET_SPECIFIC__NO_GENERAL_PROMOTION",
            "positive_in_both_under_same_test":"STRENGTHENS_ASSOCIATION_ONLY__NOT_CAUSATION",
            "null_after_shared_opportunity_normalization":"GENERAL_NUCLEAR_WINDOW_CLAIM_NOT_SUPPORTED_BY_THIS_TEST",
            "uap_or_nhi_inference":"FORBIDDEN"}}


def self_test():
    with tempfile.TemporaryDirectory(prefix="topa-poss1-harm-") as td:
        root=Path(td); start=dt.date(1950,1,1); end=dt.date(1950,1,12)
        nuclear=root/"nuclear.jsonl.gz"
        with JsonlWriter(nuclear) as w: w.write({"date":"1950-01-05","event":"TEST"})
        specs=[]
        for cohort_id in ["A","B"]:
            cand=root/f"{cohort_id}.jsonl.bz2"; opp=root/f"{cohort_id}.opp.ndjson.gz"
            with JsonlWriter(cand) as w:
                cid=0
                for day in daterange(start,end):
                    for _ in range(2):
                        cid+=1; score=0.9 if abs((day-dt.date(1950,1,5)).days)<=1 else 0.2
                        w.write({"candidate_id":f"{cohort_id}-{cid}","date_obs":day.isoformat(),"artifact_score_raw":score})
            with JsonlWriter(opp) as w:
                for day in daterange(start,end): w.write({"date_obs":day.isoformat(),"opportunity":10.0})
            specs.append({"id":cohort_id,"candidates_path":str(cand),"opportunity_path":str(opp),"score_thresholds":[0.8]})
        result=run_config({"experiment_id":"SELF_TEST","study_start":start.isoformat(),"study_end":end.isoformat(),
                           "nuclear_window_days":1,"nuclear_manifest_path":str(nuclear),"cohorts":specs})
        assert len(result["cohorts"])==2 and result["common_observed_date_intersection"]["executed"] is True
        for c in result["cohorts"]: assert c["primary_artifact_score_weighted_rate"]["observed"]["rate_ratio"]>1.0
        return {"schema":"hawkar.topa.poss1_harmonization.self_test.v1","status":"PASS","cohorts":2,
                "compressed_json_rails":True,"common_date_intersection":True}


def main():
    p=argparse.ArgumentParser(description="TOPA POSS-I closed/open harmonization"); sp=p.add_subparsers(dest="cmd",required=True)
    q=sp.add_parser("run"); q.add_argument("config"); q.add_argument("--out"); sp.add_parser("self-test"); a=p.parse_args()
    if a.cmd=="self-test": result=self_test()
    else:
        with open(a.config,"rt",encoding="utf-8") as fh: config=json.load(fh)
        result=run_config(config)
        if a.out: write_json_atomic(a.out,result)
    print(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())
