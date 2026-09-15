#!/usr/bin/env python3
"""TOPA BR03 Kadesh Common Crawl query-builder reverse audit v0.18.

Diagnostic/discovery only. The frozen Wilson 1927 identity and locus do not change.
No source prose or WARC payload is stored. We first prove the CDX query path with
positive controls, then compare exact/prefix/wildcard forms for the SAME numeric
Scribd document IDs over representative 2019-2026 indexes. A record only enables
a later bounded payload test; it does not unlock coding.
"""
from __future__ import annotations
import hashlib, json, re, urllib.error, urllib.parse, urllib.request
from pathlib import Path

OUT = Path('research/propaganda-defense/execution/KADESH_CC_QUERY_AUDIT.v0.18.json')
UA = 'TOPA-Kadesh-CC-Query-Audit/0.18 (+https://github.com/Hawkar-usls/TOPA)'
COLLINFO = 'https://index.commoncrawl.org/collinfo.json'
WAYBACK = 'https://web.archive.org/cdx/search/cdx'
DOCS = {
    '462138503': 'The-Texts-of-the-Battle-of-Kadesh',
    '493951399': 'Wilson-John-The-Texts-of-the-Battle-of-Kadesh',
}
YEARS = list(range(2019, 2027))


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def get(url: str, timeout: int = 35, maxb: int = 8 * 1024 * 1024):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': '*/*'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            b = r.read(maxb + 1)
            return {
                'ok': True,
                'status': getattr(r, 'status', 200),
                'final_url': r.geturl(),
                'content_type': r.headers.get('Content-Type'),
                'bytes': min(len(b), maxb),
                'sha256': sha(b[:maxb]),
                'truncated': len(b) > maxb,
                'body': b[:maxb],
            }
    except urllib.error.HTTPError as e:
        try:
            b = e.read(65536)
        except Exception:
            b = b''
        return {
            'ok': False,
            'status': e.code,
            'error': f'HTTPError: {e}',
            'error_body_bytes': len(b),
            'error_body_sha256': sha(b),
        }
    except Exception as e:
        return {'ok': False, 'error': f'{type(e).__name__}: {e}'}


def pub(x):
    return {k: v for k, v in x.items() if k != 'body'}


def parse_json_lines(x):
    recs = []
    if not x.get('ok'):
        return recs
    for line in x['body'].decode('utf-8', 'replace').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            j = json.loads(line)
            if isinstance(j, dict):
                recs.append({k: j.get(k) for k in (
                    'urlkey', 'timestamp', 'url', 'status', 'mime', 'mime-detected',
                    'digest', 'length', 'offset', 'filename'
                ) if k in j})
        except Exception:
            pass
    return recs


def query(api, params):
    u = api + '?' + urllib.parse.urlencode(params)
    x = get(u)
    return {'url': u, 'request': pub(x), 'records': parse_json_lines(x)}


def select_indexes(coll):
    groups = {y: [] for y in YEARS}
    for item in coll:
        cid = item.get('id', '')
        m = re.match(r'CC-MAIN-(\d{4})-', cid)
        if not m:
            continue
        y = int(m.group(1))
        if y in groups and item.get('cdx-api'):
            groups[y].append({'id': cid, 'api': item['cdx-api']})
    # collinfo is newest-first; choose one representative crawl per year,
    # closest to mid-year by numeric crawl suffix when possible.
    selected = []
    for y in YEARS:
        xs = groups[y]
        if not xs:
            continue
        def score(item):
            m = re.search(r'-(\d+)$', item['id'])
            n = int(m.group(1)) if m else 26
            return abs(n - 26)
        selected.append(sorted(xs, key=score)[0])
    return selected


def main():
    cx = get(COLLINFO, maxb=4 * 1024 * 1024)
    coll = []
    if cx.get('ok'):
        try:
            coll = json.loads(cx['body'].decode('utf-8'))
        except Exception:
            coll = []
    indexes = select_indexes(coll)

    # Documented positive control: Common Crawl docs show example.com queries on CDX.
    doc_api = 'https://index.commoncrawl.org/CC-MAIN-2026-17-index'
    pc = query(doc_api, {'url': 'example.com', 'output': 'json', 'limit': '1'})
    positive_control_pass = bool(pc['request'].get('ok') and pc['records'])

    historical = []
    total_target_records = 0
    for idx in indexes:
        row = {'index': idx, 'health': {}, 'targets': []}
        health = query(idx['api'], {'url': 'example.com', 'output': 'json', 'limit': '1'})
        row['health'] = {
            'request': health['request'],
            'record_count': len(health['records']),
            'pass': bool(health['request'].get('ok') and health['records'])
        }
        for docid, slug in DOCS.items():
            forms = {
                'EXACT_CANONICAL': {
                    'url': f'https://www.scribd.com/document/{docid}/{slug}',
                    'output': 'json', 'limit': '50'
                },
                'MATCHTYPE_PREFIX': {
                    'url': f'https://www.scribd.com/document/{docid}/',
                    'output': 'json', 'matchType': 'prefix', 'limit': '200'
                },
                'WILDCARD_PATH': {
                    'url': f'www.scribd.com/document/{docid}/*',
                    'output': 'json', 'limit': '200'
                },
                'WILDCARD_SCHEMELESS': {
                    'url': f'scribd.com/document/{docid}/*',
                    'output': 'json', 'limit': '200'
                }
            }
            results = {}
            seen = {}
            for name, params in forms.items():
                q = query(idx['api'], params)
                # keep only metadata; deduplicate by timestamp/url/digest
                recs = []
                for r in q['records']:
                    if docid not in (r.get('url') or ''):
                        continue
                    key = (r.get('timestamp'), r.get('url'), r.get('digest'))
                    if key in seen:
                        continue
                    seen[key] = True
                    recs.append(r)
                results[name] = {'request': q['request'], 'record_count': len(recs), 'records': recs[:50]}
                total_target_records += len(recs)
            row['targets'].append({'document_id': docid, 'forms': results})
        historical.append(row)

    # Retry only the previously transport-failed second numeric ID at Wayback.
    wb_params = {
        'url': 'www.scribd.com/document/493951399/*',
        'output': 'json',
        'filter': ['statuscode:200', 'mimetype:text/html'],
        'collapse': 'digest',
        'fl': 'timestamp,original,statuscode,mimetype,digest,length',
        'from': '2019', 'to': '2026'
    }
    wb_url = WAYBACK + '?' + urllib.parse.urlencode(wb_params, doseq=True)
    wb = get(wb_url)
    wb_rows = []
    if wb.get('ok'):
        try:
            a = json.loads(wb['body'].decode('utf-8'))
            if a:
                hdr = a[0]
                wb_rows = [dict(zip(hdr, r)) for r in a[1:]]
        except Exception:
            pass

    healthy_indexes = sum(1 for x in historical if x['health']['pass'])
    target_record_indexes = sum(1 for x in historical if any(
        f['record_count'] > 0 for t in x['targets'] for f in t['forms'].values()
    ))
    query_builder_validated = positive_control_pass and healthy_indexes >= max(1, len(indexes) // 2)

    out = {
        'schema': 'topa.propaganda_defense.kadesh_cc_query_audit.v0.18',
        'date': '2026-08-24',
        'status': 'DIAGNOSTIC_ONLY',
        'frozen': {
            'authority': 'John A. Wilson / AJSL / University of Chicago / JSTOR',
            'doi': '10.1086/370157',
            'jstor_stable_id': '528771',
            'locus': 'THE POEM, journal pp.266-278; Record excluded',
            'changed': False
        },
        'positive_control': pc,
        'positive_control_pass': positive_control_pass,
        'selected_historical_indexes': indexes,
        'historical_index_health_pass_count': healthy_indexes,
        'historical': historical,
        'wayback_retry_493951399': {
            'request': pub(wb),
            'capture_count': len(wb_rows),
            'captures': wb_rows[:30]
        },
        'summary': {
            'query_builder_validated': query_builder_validated,
            'historical_indexes_selected': len(indexes),
            'historical_index_health_pass_count': healthy_indexes,
            'indexes_with_target_records': target_record_indexes,
            'target_record_observations_before_cross_form_dedup': total_target_records,
            'wayback_493951399_capture_count': len(wb_rows),
            'br03_retrieval_pass': False,
            'semantic_values_populated': 0,
            'base_rate_coding_permission': False,
            'score_permission': False
        },
        'next_gate': 'If and only if query_builder_validated and target CDX records exist, retrieve only candidate WARC coordinates in a separate v0.19 payload-integrity probe. Otherwise preserve the validated negative sampling result and do not infer universal absence.',
        'laws': [
            'POSITIVE_CONTROL_PRECEDES_NEGATIVE_INFERENCE',
            'ONE_REPRESENTATIVE_INDEX_PER_YEAR != EXHAUSTIVE_ARCHIVE_SEARCH',
            'CDX_RECORD != LOCUS_CONTENT',
            'ARCHIVE_COPY != INDEPENDENT_WITNESS',
            'NUMERIC_DOCUMENT_ID_FROZEN_SLUG_MAY_VARY',
            'NO_WARC_CONTENT_PERSISTED_IN_DISCOVERY_PASS',
            'NO_SEMANTIC_CODING',
            'NO_SCORE'
        ]
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
    print('TOPA_KADESH_CC_QUERY_AUDIT_V0_18=COMPLETE')
    print('POSITIVE_CONTROL_PASS=' + str(positive_control_pass).lower())
    print('QUERY_BUILDER_VALIDATED=' + str(query_builder_validated).lower())
    print(f'HISTORICAL_INDEX_HEALTH={healthy_indexes}/{len(indexes)}')
    print('INDEXES_WITH_TARGET_RECORDS=' + str(target_record_indexes))
    print('WAYBACK_493951399_CAPTURES=' + str(len(wb_rows)))
    print('BR03_RETRIEVAL_PASS=false')
    print('BASE_RATE_CODING_PERMISSION=false')
    print('SCORE_PERMISSION=false')

if __name__ == '__main__':
    main()
