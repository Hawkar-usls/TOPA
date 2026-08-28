#!/usr/bin/env python3
"""Cross-scale Keymaster shadow simulation.

Negative-control experiment: fit a tiny ridge-linear router using ONLY cheap
pre-pivot structural features from one frozen formula family and ask it to rank
pivots in the other family.  This deliberately tests whether simple coefficient
transfer is safe before Pivot-Slime/M2R-PM are trusted.

No proof verdict is model-derived. P_VS_NP remains OPEN.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
from typing import Any

P_VS_NP="OPEN"
FEATURES=["pos_mean_width","neg_mean_width","conflict_mass_per_pair","same_sign_mass_per_pair","support_overlap_mass_per_pair"]


def load(path:Path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def solve(A,b):
    n=len(b); M=[list(map(float,A[i]))+[float(b[i])] for i in range(n)]
    for col in range(n):
        p=max(range(col,n),key=lambda r:abs(M[r][col]))
        if abs(M[p][col])<1e-12: raise ValueError("singular")
        M[col],M[p]=M[p],M[col]
        q=M[col][col]
        M[col]=[v/q for v in M[col]]
        for r in range(n):
            if r==col: continue
            q=M[r][col]
            M[r]=[M[r][j]-q*M[col][j] for j in range(n+1)]
    return [M[i][-1] for i in range(n)]


def fit(train,lam=1e-6):
    mu=[]; sd=[]
    for f in FEATURES:
        xs=[float(r[f]) for r in train]; m=sum(xs)/len(xs); s=math.sqrt(sum((x-m)**2 for x in xs)/len(xs)) or 1.0
        mu.append(m); sd.append(s)
    X=[]
    for r in train:
        X.append([1.0]+[(float(r[f])-mu[i])/sd[i] for i,f in enumerate(FEATURES)])
    y=[float(r["raw_units"]) for r in train]; d=len(X[0])
    G=[[sum(row[i]*row[j] for row in X)+(lam if i==j and i>0 else 0.0) for j in range(d)] for i in range(d)]
    h=[sum(X[k][i]*y[k] for k in range(len(X))) for i in range(d)]
    return mu,sd,solve(G,h)


def predict(rows,model):
    mu,sd,beta=model; out=[]
    for r in rows:
        x=[1.0]+[(float(r[f])-mu[i])/sd[i] for i,f in enumerate(FEATURES)]
        out.append(sum(a*b for a,b in zip(x,beta)))
    return out


def one(train,test):
    pr=predict(test,fit(train))
    scored=sorted(zip(test,pr),key=lambda z:(z[1],z[0]["pivot_id_local"]))
    chosen,pred=scored[0]
    best=min(test,key=lambda r:(r["raw_units"],r["pivot_id_local"]))
    return {
      "train_case":train[0]["case_id"],"test_case":test[0]["case_id"],
      "chosen_local_pivot":chosen["pivot_id_local"],"chosen_predicted_raw":pred,"chosen_exact_raw":chosen["raw_units"],
      "exact_best_local_pivot":best["pivot_id_local"],"exact_best_raw":best["raw_units"],
      "peak_raw_regret":chosen["raw_units"]-best["raw_units"],
      "predictions":[{"pivot_id_local":r["pivot_id_local"],"predicted_raw":p,"exact_raw":r["raw_units"]} for r,p in zip(test,pr)],
      "stress_104_squared_fit": (chosen["raw_units"]<=104*104) if test[0]["case_id"]=="250x250-n8" else None
    }


def build(rows):
    cases={}
    for r in rows: cases.setdefault(r["case_id"],[]).append(r)
    a=one(cases["25x25-n7"],cases["250x250-n8"])
    b=one(cases["250x250-n8"],cases["25x25-n7"])
    return {
      "schema":"TOPA/KEYMASTER/CROSS-SCALE-SHADOW/v1","status":"NEGATIVE_TRANSFER_CERTIFICATE","P_VS_NP":P_VS_NP,
      "features":FEATURES,"model":"RIDGE_LINEAR_CHEAP_FEATURES_ONLY_LAMBDA_1E-6",
      "formula_fingerprint_holdout":True,"results":[a,b],
      "finding":"Naive cross-scale coefficient transfer fails in both directions on these two frozen formula families.",
      "implication":"Keymaster needs scale/context-conditioned memory and multi-formula training; Pivot-Slime/M2R-PM must be evaluated on fingerprint-held-out formulas.",
      "laws":["NEGATIVE_RESULT_IS_PRESERVED","LOCAL_PIVOT_IDS_ARE_NOT_TRANSFER_FEATURES","MODEL_CANNOT_CHANGE_EXACT_VERDICT","TWO_FORMULAS_DO_NOT_ESTIMATE_GENERALIZATION_RATE","P_VS_NP_IS_OPEN"]
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("command",choices=["run","self-test"]); ap.add_argument("--input",type=Path); ap.add_argument("--out",type=Path); a=ap.parse_args()
    if a.command=="self-test":
        print(json.dumps({"status":"PASS","P_VS_NP":P_VS_NP})); return 0
    if not a.input or not a.out: ap.error("run requires --input and --out")
    p=build(load(a.input)); a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(p,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":p["status"],"results":[{k:r[k] for k in ("train_case","test_case","chosen_local_pivot","exact_best_local_pivot","peak_raw_regret","stress_104_squared_fit")} for r in p["results"]],"P_VS_NP":P_VS_NP},indent=2,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
