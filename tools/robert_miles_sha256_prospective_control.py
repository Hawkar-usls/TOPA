#!/usr/bin/env python3
import argparse, hashlib, html, itertools, json, math, random, re, urllib.request
from pathlib import Path
from urllib.parse import urlparse

UA = "Mozilla/5.0 (compatible; JANUS-TOPA-prospective-sha/1.0; +https://github.com/Hawkar-usls/TOPA)"


def get_bytes(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read()


def get_text(url):
    return get_bytes(url).decode("utf-8", errors="replace")


def extract_tralbum(text):
    objs = []
    for pat in [r'data-tralbum="([^"]+)"', r'data-blob="([^"]+)"']:
        for m in re.finditer(pat, text):
            raw = html.unescape(m.group(1))
            try:
                obj = json.loads(raw)
            except Exception:
                continue
            if isinstance(obj, dict) and isinstance(obj.get("trackinfo"), list):
                objs.append(obj)
    if not objs:
        raise RuntimeError("Bandcamp trackinfo not found")
    return max(objs, key=lambda x: len(x.get("trackinfo") or []))


def normalize_title(s):
    return re.sub(r"\s+", " ", (s or "").strip()).casefold()


def choose_track(tralbum, title):
    target = normalize_title(title)
    tracks = tralbum.get("trackinfo") or []
    exact = [t for t in tracks if normalize_title(t.get("title")) == target]
    if len(exact) != 1:
        # permit apostrophe/case/punctuation normalization but never fuzzy semantic substitution
        simple = lambda x: re.sub(r"[^a-z0-9]+", "", normalize_title(x))
        exact = [t for t in tracks if simple(t.get("title")) == simple(title)]
    if len(exact) != 1:
        raise RuntimeError(f"Could not uniquely resolve {title!r}; candidates={[t.get('title') for t in tracks]}")
    t = exact[0]
    files = t.get("file") or {}
    if not files.get("mp3-128"):
        raise RuntimeError(f"No public mp3-128 for {title}")
    return t, files["mp3-128"]


def hash_url(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "audio/mpeg,*/*"})
    h = hashlib.sha256(); n = 0
    with urllib.request.urlopen(req, timeout=180) as r:
        meta = {"content_type": r.headers.get("Content-Type"), "etag": r.headers.get("ETag"), "last_modified": r.headers.get("Last-Modified")}
        while True:
            chunk = r.read(1024*1024)
            if not chunk: break
            h.update(chunk); n += len(chunk)
    meta.update({"sha256": h.hexdigest(), "bytes": n, "host": urlparse(url).hostname})
    return meta


def hamming(a,b):
    return sum((x^y).bit_count() for x,y in zip(bytes.fromhex(a), bytes.fromhex(b)))


def fixed_matches(a,b):
    return sum(x==y for x,y in zip(a,b))


def lcs_substring(a,b):
    # longest common contiguous substring; deterministic tie break: lexicographically smallest, then earliest positions
    best = (0, "", None, None)
    for i in range(len(a)):
        for j in range(len(b)):
            k=0
            while i+k<len(a) and j+k<len(b) and a[i+k]==b[j+k]: k+=1
            if k > best[0]: best=(k,a[i:i+k],i,j)
            elif k == best[0] and k>0:
                cand=(a[i:i+k],i,j)
                cur=(best[1],best[2],best[3])
                if cand < cur: best=(k,a[i:i+k],i,j)
    return {"length": best[0], "substring": best[1], "a_start_1indexed": None if best[2] is None else best[2]+1, "b_start_1indexed": None if best[3] is None else best[3]+1}


def metrics(a,b):
    l=lcs_substring(a,b)
    return {"hamming":hamming(a,b),"lcs_length":l["length"],"lcs":l,"fixed_hex_matches":fixed_matches(a,b),"lcs_ge_5":int(l["length"]>=5)}


def mean(xs): return sum(xs)/len(xs) if xs else None


def group_summary(rows):
    return {
        "n": len(rows),
        "mean_hamming": mean([r["metrics"]["hamming"] for r in rows]),
        "mean_lcs_length": mean([r["metrics"]["lcs_length"] for r in rows]),
        "mean_fixed_hex_matches": mean([r["metrics"]["fixed_hex_matches"] for r in rows]),
        "count_lcs_ge_5": sum(r["metrics"]["lcs_ge_5"] for r in rows),
    }


def perm_p(rows, labels, stat_fn, direction):
    vals=[]
    idx=range(len(rows))
    obsA=[rows[i] for i,l in enumerate(labels) if l=="related"]
    obsB=[rows[i] for i,l in enumerate(labels) if l=="control"]
    obs=stat_fn(obsA)-stat_fn(obsB)
    for comb in itertools.combinations(idx, 5):
        s=set(comb)
        A=[rows[i] for i in idx if i in s]
        B=[rows[i] for i in idx if i not in s]
        vals.append(stat_fn(A)-stat_fn(B))
    if direction=="greater": p=sum(v>=obs-1e-12 for v in vals)/len(vals)
    else: p=sum(v<=obs+1e-12 for v in vals)/len(vals)
    return {"observed_difference_related_minus_control":obs,"direction":direction,"exact_assignments":len(vals),"p_one_sided":p}


def random_digest(rng):
    return bytes(rng.getrandbits(8) for _ in range(32)).hex()


def mc_null(n, seed):
    rng=random.Random(seed)
    lcs_counts={}; fixed_counts={}; hams=[]
    ge5=0
    for _ in range(n):
        a=random_digest(rng); b=random_digest(rng)
        m=metrics(a,b)
        l=m["lcs_length"]; f=m["fixed_hex_matches"]
        lcs_counts[str(l)]=lcs_counts.get(str(l),0)+1
        fixed_counts[str(f)]=fixed_counts.get(str(f),0)+1
        hams.append(m["hamming"])
        ge5 += (l>=5)
    return {
        "n":n,"seed":seed,
        "mean_hamming":mean(hams),
        "prob_lcs_ge_5":ge5/n,
        "lcs_length_histogram":lcs_counts,
        "fixed_hex_match_histogram":fixed_counts
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--prereg",required=True)
    ap.add_argument("--prereg-commit",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    prereg=json.loads(Path(args.prereg).read_text(encoding="utf-8"))
    if prereg.get("status") != "FROZEN_BEFORE_NEW_HASH_RETRIEVAL": raise SystemExit("prereg status invalid")
    seed=int(args.prereg_commit[:16],16)
    page_cache={}; track_cache={}
    def resolve(page,title):
        key=(page,title)
        if key in track_cache: return track_cache[key]
        if page not in page_cache: page_cache[page]=extract_tralbum(get_text(page))
        tr,url=choose_track(page_cache[page],title)
        meta=hash_url(url)
        out={"requested_title":title,"resolved_title":tr.get("title"),"track_id":tr.get("track_id") or tr.get("id"),"duration_seconds_reported":tr.get("duration"),"source_page":page,"stream_format":"mp3-128","stream":meta}
        track_cache[key]=out
        return out
    rows=[]
    for group,field in [("related","prospective_related_pairs"),("control","same_catalog_unrelated_controls")]:
        for p in prereg[field]:
            A=resolve(p["page"],p["a"]); B=resolve(p["page"],p["b"])
            rows.append({"id":p["id"],"group":group,"a":A,"b":B,"metrics":metrics(A["stream"]["sha256"],B["stream"]["sha256"])})
    rel=[r for r in rows if r["group"]=="related"]; ctl=[r for r in rows if r["group"]=="control"]
    labels=[r["group"] for r in rows]
    stat_h=lambda rr: mean([x["metrics"]["hamming"] for x in rr])
    stat_l=lambda rr: mean([x["metrics"]["lcs_length"] for x in rr])
    stat_f=lambda rr: mean([x["metrics"]["fixed_hex_matches"] for x in rr])
    stat_g=lambda rr: mean([x["metrics"]["lcs_ge_5"] for x in rr])
    result={
      "schema":"topa.robert_miles.sha256_prospective_control.v1",
      "status":"PASS",
      "prereg":{"artifact_id":prereg["artifact_id"],"commit":args.prereg_commit,"known_children_excluded_from_inference":True},
      "rows":rows,
      "group_summary":{"related":group_summary(rel),"control":group_summary(ctl)},
      "exact_permutation_tests":{
        "hamming_lower_in_related":perm_p(rows,labels,stat_h,"less"),
        "lcs_higher_in_related":perm_p(rows,labels,stat_l,"greater"),
        "fixed_matches_higher_in_related":perm_p(rows,labels,stat_f,"greater"),
        "lcs_ge5_fraction_higher_in_related":perm_p(rows,labels,stat_g,"greater")
      },
      "uniform_sha256_monte_carlo":mc_null(100000,seed),
      "firewall":["CHILDREN_97254_NOT_IN_PROSPECTIVE_STATISTICS","SHA256_NOT_AUDIO_FINGERPRINT","PAIR_SHARING_MEANS_PERMUTATION_P_DESCRIPTIVE","VISIBLE_PATTERN_NOT_MESSAGE","NULL_MUST_BE_PRESERVED"],
      "canonical_seal":"THE QUESTION WAS FROZEN BEFORE THE NEW DIGESTS. RELATED VERSIONS EITHER DEPART FROM SAME-PIPELINE CONTROLS ON THE FIXED METRICS OR THEY DO NOT; BOTH OUTCOMES ARE DATA."
    }
    Path(args.out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"group_summary":result["group_summary"],"exact_permutation_tests":result["exact_permutation_tests"],"mc":result["uniform_sha256_monte_carlo"]},ensure_ascii=False,indent=2))

if __name__=="__main__": main()
