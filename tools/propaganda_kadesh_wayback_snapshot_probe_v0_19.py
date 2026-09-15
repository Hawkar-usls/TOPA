#!/usr/bin/env python3
"""TOPA BR03 Kadesh Wayback snapshot integrity probe v0.19.

Tests exactly two already-resolved captures of the same frozen Scribd document ID
493951399. No source prose is persisted. We store response hashes, marker booleans,
page-number coverage and embedded asset coordinates only. A snapshot/asset is a
transport candidate, never a new source root and never an automatic coding unlock.
"""
from __future__ import annotations
import hashlib,html,json,re,urllib.error,urllib.parse,urllib.request
from pathlib import Path

OUT=Path('research/propaganda-defense/execution/KADESH_WAYBACK_SNAPSHOT_PROBE.v0.19.json')
UA='TOPA-Kadesh-Wayback-Probe/0.19 (+https://github.com/Hawkar-usls/TOPA)'
ORIGINAL='https://www.scribd.com/document/493951399/Wilson-John-The-Texts-of-the-Battle-of-Kadesh'
CAPTURES=[
 {'timestamp':'20250825141753','digest':'FZ4K7Y3KNMXXSNOHCFTP5USDMW2YOVSY','cdx_length':'229746'},
 {'timestamp':'20260111160515','digest':'AX5KLLFPDD65YEFQ3ERSB4LLGWZOE3EY','cdx_length':'216639'},
]

def sha(b):return hashlib.sha256(b).hexdigest()
def get(u,maxb=12*1024*1024,timeout=30):
    req=urllib.request.Request(u,headers={'User-Agent':UA,'Accept':'*/*','Accept-Encoding':'identity'})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            b=r.read(maxb+1)
            return {'ok':True,'status':getattr(r,'status',200),'final_url':r.geturl(),'content_type':r.headers.get('Content-Type'),'bytes':min(len(b),maxb),'sha256':sha(b[:maxb]),'truncated':len(b)>maxb,'body':b[:maxb]}
    except urllib.error.HTTPError as e:
        try:b=e.read(65536)
        except:b=b''
        return {'ok':False,'status':e.code,'error':f'HTTPError: {e}','error_body_bytes':len(b),'error_body_sha256':sha(b)}
    except Exception as e:return {'ok':False,'error':f'{type(e).__name__}: {e}'}
def pub(x):return {k:v for k,v in x.items() if k!='body'}
def norm(b):
    s=b.decode('utf-8','replace')
    s=re.sub(r'\\u([0-9a-fA-F]{4})',lambda m:chr(int(m.group(1),16)),s)
    s=s.replace('\\/','/').replace('\\n',' ')
    s=re.sub(r'(?is)<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',lambda m:' '+m.group(1)+' ',s)
    s=re.sub(r'(?is)<style.*?</style>',' ',s)
    s=re.sub(r'(?s)<[^>]+>',' ',s)
    return re.sub(r'\s+',' ',html.unescape(s)).strip()
def asset_urls(raw):
    s=raw.decode('utf-8','replace').replace('\\/','/')
    urls=re.findall(r'https?://[^"\'<>\\\s]+',s)
    keep=[]
    for u in urls:
        lu=u.lower()
        if any(k in lu for k in ('scribdassets','html.scribd','html5','document_asset','page_num','page-num','contenturl','asset')):
            # strip obvious trailing punctuation only; URL itself is metadata.
            u=u.rstrip('),.;]')
            if u not in keep:keep.append(u)
    return keep[:60]
def analyze(raw):
    t=norm(raw); low=t.lower(); rawtxt=raw.decode('utf-8','replace').lower()
    nums=sorted({int(x) for x in re.findall(r'(?<!\d)(26[6-9]|27\d|28[0-7])(?!\d)',t)})
    identity={
      'document_id':'493951399' in rawtxt or '493951399' in low,
      'title':'the texts of the battle of kadesh' in low,
      'wilson':'john a. wilson' in low or 'john a wilson' in low or 'wilson john' in low,
      'scribd':'scribd' in low or 'scribd' in rawtxt,
    }
    markers={
      'the_poem':'the poem' in low,
      'the_record':'the record' in low,
      'council_urges_peace':'council urges peace' in low,
      'comment_on_the_texts':'comment on the texts' in low,
    }
    assets=asset_urls(raw)
    identity_ok=identity['document_id'] and identity['title'] and identity['wilson']
    content_candidate=identity_ok and markers['the_poem'] and markers['the_record'] and len(nums)>=10
    return {
      'normalized_chars':len(t),'normalized_sha256':sha(t.encode()),
      'identity':identity,'identity_ok':identity_ok,'markers':markers,
      'page_numbers_seen_266_287':nums,'page_coverage_count':len(nums),
      'embedded_asset_count':len(assets),'embedded_asset_urls':assets,
      'embedded_asset_urlset_sha256':sha('\n'.join(assets).encode()),
      'locus_content_candidate':content_candidate
    }

def main():
    rows=[];content=[];assets=[]
    for c in CAPTURES:
        modes=[]
        # id_ asks for the archived response; if_ is the replay-wrapper variant.
        for modifier in ('id_','if_'):
            u=f"https://web.archive.org/web/{c['timestamp']}{modifier}/{ORIGINAL}"
            x=get(u); r={'modifier':modifier,'url':u,'response':pub(x)}
            if x.get('ok'):
                a=analyze(x['body']);r['analysis']=a
                if a['locus_content_candidate']:content.append({'timestamp':c['timestamp'],'modifier':modifier,'response_sha256':x['sha256'],'analysis':a})
                if a['embedded_asset_count']:
                    assets.append({'timestamp':c['timestamp'],'modifier':modifier,'response_sha256':x['sha256'],'asset_urls':a['embedded_asset_urls'],'asset_urlset_sha256':a['embedded_asset_urlset_sha256']})
            modes.append(r)
        rows.append({'cdx_coordinate':c,'original':ORIGINAL,'replays':modes})
    out={'schema':'topa.propaganda_defense.kadesh_wayback_snapshot_probe.v0.19','date':'2026-08-24','status':'DIAGNOSTIC_ONLY','frozen':{'authority':'John A. Wilson / AJSL / University of Chicago / JSTOR','doi':'10.1086/370157','jstor_stable_id':'528771','transport_document_id':'493951399','locus':'THE POEM, journal pp.266-278; Record excluded','operational_boundary':'Poem content pp.266-277; p.278 retained as THE RECORD exclusion boundary','changed':False},'archive_firewall':{'wayback_authority':0,'scribd_authority':0,'archive_adds_source_root':False,'mirror_adds_source_root':False,'source_root_count_if_admitted':1},'captures':rows,'summary':{'capture_coordinates_tested':len(CAPTURES),'replay_variants_tested':len(CAPTURES)*2,'locus_content_candidates':len(content),'embedded_asset_coordinate_sets':len(assets),'content_candidates':content,'asset_candidates':assets,'br03_retrieval_pass':False,'semantic_values_populated':0,'base_rate_coding_permission':False,'score_permission':False},'next_gate':'If a locus_content_candidate exists, create a separate transport-admission review. If only embedded asset coordinates exist, probe only those exact archived asset coordinates in v0.20 and require identity + frozen boundary validation. If neither exists, preserve this negative and do not broaden document identity.','laws':['WAYBACK_SNAPSHOT != SOURCE_AUTHORITY','SCRIBD_MIRROR != INDEPENDENT_WITNESS','IDENTITY_METADATA != LOCUS_CONTENT','EMBEDDED_ASSET_URL != ASSET_CONTENT','NO_SOURCE_PROSE_PERSISTED','NO_SEMANTIC_CODING','NO_SCORE']}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print('TOPA_KADESH_WAYBACK_SNAPSHOT_PROBE_V0_19=COMPLETE')
    print('LOCUS_CONTENT_CANDIDATES='+str(len(content)))
    print('EMBEDDED_ASSET_COORDINATE_SETS='+str(len(assets)))
    print('BR03_RETRIEVAL_PASS=false')
    print('BASE_RATE_CODING_PERMISSION=false')
    print('SCORE_PERMISSION=false')
if __name__=='__main__':main()
