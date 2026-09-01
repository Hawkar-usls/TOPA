#!/usr/bin/env python3
import argparse, html, itertools, json, math, re, subprocess, tempfile, urllib.request
from pathlib import Path
from urllib.parse import urlparse
import numpy as np

UA="Mozilla/5.0 (compatible; JANUS-TOPA-audio-witness/1.0; +https://github.com/Hawkar-usls/TOPA)"
SR=11025


def get_bytes(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"*/*"})
    with urllib.request.urlopen(req,timeout=90) as r: return r.read()


def extract_tralbum(text):
    objs=[]
    for pat in [r'data-tralbum="([^"]+)"',r'data-blob="([^"]+)"']:
        for m in re.finditer(pat,text):
            try: obj=json.loads(html.unescape(m.group(1)))
            except Exception: continue
            if isinstance(obj,dict) and isinstance(obj.get('trackinfo'),list): objs.append(obj)
    if not objs: raise RuntimeError('Bandcamp trackinfo not found')
    return max(objs,key=lambda x:len(x.get('trackinfo') or []))


def norm(s): return re.sub(r'\s+',' ',(s or '').strip()).casefold()
def simple(s): return re.sub(r'[^a-z0-9]+','',norm(s))


def choose_track(tralbum,title):
    tracks=tralbum.get('trackinfo') or []
    m=[t for t in tracks if norm(t.get('title'))==norm(title)]
    if len(m)!=1: m=[t for t in tracks if simple(t.get('title'))==simple(title)]
    if len(m)!=1: raise RuntimeError(f'Could not uniquely resolve {title!r}: {[t.get("title") for t in tracks]}')
    t=m[0]; files=t.get('file') or {}; url=files.get('mp3-128')
    if not url: raise RuntimeError(f'No public mp3-128 for {title}')
    return t,url


def download(url,path):
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"audio/mpeg,*/*"})
    n=0
    with urllib.request.urlopen(req,timeout=180) as r,open(path,'wb') as f:
        while True:
            c=r.read(1024*1024)
            if not c: break
            f.write(c); n+=len(c)
    return n


def decode(mp3,pcm):
    cmd=['ffmpeg','-v','error','-y','-i',str(mp3),'-map_metadata','-1','-ac','1','-ar',str(SR),'-f','s16le',str(pcm)]
    subprocess.run(cmd,check=True)
    x=np.fromfile(pcm,dtype='<i2').astype(np.float32)/32768.0
    if len(x)<SR: raise RuntimeError('Decoded audio unexpectedly short')
    return x


def cosine(a,b):
    a=np.asarray(a,dtype=np.float64); b=np.asarray(b,dtype=np.float64)
    den=np.linalg.norm(a)*np.linalg.norm(b)
    return float(np.dot(a,b)/den) if den>0 else 0.0


def corr(a,b):
    a=np.asarray(a,dtype=np.float64); b=np.asarray(b,dtype=np.float64)
    a=a-a.mean(); b=b-b.mean(); den=np.linalg.norm(a)*np.linalg.norm(b)
    return float(np.dot(a,b)/den) if den>0 else 0.0


def resample_vec(v,n=1024):
    v=np.asarray(v,dtype=np.float64)
    if len(v)==1: return np.repeat(v,n)
    xp=np.linspace(0,1,len(v)); x=np.linspace(0,1,n)
    return np.interp(x,xp,v)


def extract_features(x):
    # RMS trajectory and crude onset/tempo witness.
    frame=1024; hop=512
    rms=[]
    for s in range(0,len(x)-frame+1,hop):
        y=x[s:s+frame]
        rms.append(float(np.sqrt(np.mean(y*y)+1e-12)))
    rms=np.asarray(rms,dtype=np.float64)
    rms_norm=resample_vec(rms,1024)
    if rms_norm.max()>0: rms_norm=rms_norm/(rms_norm.max()+1e-12)
    onset=np.maximum(np.diff(rms_norm,prepend=rms_norm[0]),0)
    # tempo on native RMS grid for better temporal resolution
    native_on=np.maximum(np.diff(rms,prepend=rms[0]),0)
    native_on=native_on-native_on.mean()
    fps=SR/hop
    minlag=max(1,int(round(fps*60/180)))
    maxlag=max(minlag+1,int(round(fps*60/80)))
    ac=[]
    for lag in range(minlag,maxlag+1):
        a=native_on[:-lag]; b=native_on[lag:]
        ac.append((lag,float(np.dot(a,b))))
    lag=max(ac,key=lambda t:t[1])[0]
    bpm=float(60*fps/lag)

    # Whole-track averaged pitch-class and log-frequency spectral profiles.
    nfft=4096; shop=2048; win=np.hanning(nfft).astype(np.float32)
    freqs=np.fft.rfftfreq(nfft,1/SR)
    valid=(freqs>=40)&(freqs<=5000)
    vf=freqs[valid]
    midi=np.rint(69+12*np.log2(vf/440.0)).astype(int)
    pc=np.mod(midi,12)
    edges=np.geomspace(40,5000,65)
    sb=np.clip(np.digitize(vf,edges)-1,0,63)
    chroma=np.zeros(12,dtype=np.float64); spec=np.zeros(64,dtype=np.float64)
    frames=0
    for s in range(0,len(x)-nfft+1,shop):
        y=x[s:s+nfft]*win
        powr=(np.abs(np.fft.rfft(y))**2)[valid]
        np.add.at(chroma,pc,powr)
        np.add.at(spec,sb,powr)
        frames+=1
    if frames==0: raise RuntimeError('No spectral frames')
    chroma/=chroma.sum()+1e-18
    spec=np.log1p(spec/(spec.sum()+1e-18)*1e6)
    spec/=np.linalg.norm(spec)+1e-18
    return {"rms_norm":rms_norm,"onset_norm":onset,"chroma":chroma,"spectral":spec,"tempo_bpm":bpm,"duration_seconds":len(x)/SR}


def pair_metrics(fa,fb):
    return {
      "chroma_profile_cosine":cosine(fa['chroma'],fb['chroma']),
      "spectral_profile_cosine":cosine(fa['spectral'],fb['spectral']),
      "rms_shape_correlation":corr(fa['rms_norm'],fb['rms_norm']),
      "onset_shape_correlation":corr(fa['onset_norm'],fb['onset_norm']),
      "tempo_a_bpm":fa['tempo_bpm'],"tempo_b_bpm":fb['tempo_bpm'],
      "tempo_difference_bpm":abs(fa['tempo_bpm']-fb['tempo_bpm']),
      "duration_a_seconds":fa['duration_seconds'],"duration_b_seconds":fb['duration_seconds']
    }


def mean(xs): return sum(xs)/len(xs)

def gmean(rows,key): return mean([r['metrics'][key] for r in rows])


def perm(rows,key,direction):
    obsA=[r for r in rows if r['group']=='related']; obsB=[r for r in rows if r['group']=='control']
    obs=gmean(obsA,key)-gmean(obsB,key)
    vals=[]; inds=range(6)
    for comb in itertools.combinations(inds,3):
        s=set(comb); A=[rows[i] for i in inds if i in s]; B=[rows[i] for i in inds if i not in s]
        vals.append(gmean(A,key)-gmean(B,key))
    if direction=='greater': p=sum(v>=obs-1e-12 for v in vals)/len(vals)
    else: p=sum(v<=obs+1e-12 for v in vals)/len(vals)
    return {"observed_related_minus_control":obs,"direction":direction,"assignments":len(vals),"p_one_sided":p,"bonferroni_5":min(1.0,p*5)}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--prereg',required=True); ap.add_argument('--prereg-commit',required=True); ap.add_argument('--out',required=True); args=ap.parse_args()
    pre=json.loads(Path(args.prereg).read_text(encoding='utf-8'))
    if pre.get('status')!='FROZEN_BEFORE_AUDIO_FEATURE_EXTRACTION': raise SystemExit('bad prereg status')
    page_cache={}; feature_cache={}; meta_cache={}
    with tempfile.TemporaryDirectory() as td:
        td=Path(td)
        def resolve(page,title):
            k=(page,title)
            if k in feature_cache: return meta_cache[k],feature_cache[k]
            if page not in page_cache:
                page_cache[page]=extract_tralbum(get_bytes(page).decode('utf-8',errors='replace'))
            tr,url=choose_track(page_cache[page],title)
            mp3=td/(str(tr.get('track_id') or tr.get('id'))+'.mp3'); pcm=td/(mp3.stem+'.pcm')
            n=download(url,mp3); x=decode(mp3,pcm); feat=extract_features(x)
            meta={"requested_title":title,"resolved_title":tr.get('title'),"track_id":tr.get('track_id') or tr.get('id'),"mp3_bytes":n,"stream_host":urlparse(url).hostname,"duration_reported":tr.get('duration')}
            meta_cache[k]=meta; feature_cache[k]=feat
            return meta,feat
        rows=[]
        for group,field in [('related','disjoint_related_pairs'),('control','disjoint_unrelated_controls')]:
            for p in pre[field]:
                ma,fa=resolve(p['page'],p['a']); mb,fb=resolve(p['page'],p['b'])
                rows.append({"id":p['id'],"group":group,"a":ma,"b":mb,"metrics":pair_metrics(fa,fb)})
    keys=[('chroma_profile_cosine','greater'),('spectral_profile_cosine','greater'),('rms_shape_correlation','greater'),('onset_shape_correlation','greater'),('tempo_difference_bpm','less')]
    rel=[r for r in rows if r['group']=='related']; ctl=[r for r in rows if r['group']=='control']
    summary={k:{"related_mean":gmean(rel,k),"control_mean":gmean(ctl,k),"difference_related_minus_control":gmean(rel,k)-gmean(ctl,k)} for k,_ in keys}
    tests={k:perm(rows,k,d) for k,d in keys}
    result={
      "schema":"topa.robert_miles.audio_similarity_witness.v1","status":"PASS",
      "prereg":{"artifact_id":pre['artifact_id'],"commit":args.prereg_commit},
      "decode":"ffmpeg mono 11025 Hz s16le",
      "rows":rows,"group_summary":summary,"exact_permutation_tests":tests,
      "app_bridge_assessment":"Evaluate only after metrics are produced: shared musical structure may instantiate stable reference + controlled difference -> interpretable change, but this is analogy, not causal encoding.",
      "firewall":["AUDIO_SIMILARITY_NOT_HIDDEN_MESSAGE","SHA_TEST_SEPARATE","DISJOINT_TRACK_FILES","RAW_P_NOT_CONFIRMATORY_WITH_FIVE_METRICS","NULLS_PRESERVED"],
      "canonical_seal":"THE SECOND WITNESS LISTENS TO DECODED AUDIO. RELATED VERSIONS MAY SHARE CHROMA, SPECTRUM, DYNAMICS, ONSETS OR TEMPO EVEN WHEN SHA-256 DIGESTS AVALANCHE APART."
    }
    Path(args.out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding='utf-8')
    print(json.dumps({"group_summary":summary,"tests":tests},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
