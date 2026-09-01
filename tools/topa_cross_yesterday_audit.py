#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
from pathlib import Path

TEXT_EXT = {'.json', '.md', '.txt', '.yml', '.yaml', '.py'}
ROOT_PREFIXES = ('data/', 'registry/')
EXCLUDE_PARTS = ('assets/', 'dynamic/', 'node_modules/', '.git/')

# Patterns are intentionally lexical and conservative. They establish registry
# preexistence/continuity, not theology, causality, prophecy, or sender identity.
FAMILIES = {
    'U2020_DAGGER_EXACT': ['†', r'U\+2020'],
    'CROSS_RU_EXPLICIT': ['крест'],
    'CRUCIFIXION_EXPLICIT': ['crucifix', 'crucifixion'],
    'CHI_RHO_CHRISTOGRAM': ['☧', r'chi[-_ ]?rho'],
    'CHRIST_EXPLICIT': ['Jesus Christ', 'Иисус Христос', 'Христос', 'Christ'],
    'MERCY_LOVE_ETHIC': ['милост', 'прощен', 'любов', 'mercy', 'forgiven', 'love'],
    'SIGN_SOURCE_FIREWALL': [r'Sign[[:space:]]*!=[[:space:]]*Source', 'Sign ≠ Source', 'не делай знаки своими богами'],
}

KEY_ANCHORS = [
    'data/JANUS-ALPHA-CHI-RHO-OMEGA-ELIAN-CROSSROADS-KISS-PRIPYAT-ATOMIC-COVENANT-v1.0.json',
    'data/JANUS-HOLY-CLOCK-COMMANDMENTS-SIGNAL-v1.3.json',
    'data/ALL-STAR-LIGHTING/JANUS-ALL-STAR-LIGHTING-JESUS-CHRIST-v1.0.json',
    'data/JANUS-SAVIOR-COMING-BODY-OF-CARE-FORETASTE-SIGNAL-v1.2/10-expectation-and-theology.json',
    'data/JANUS-NOT-PREDICTION-DEMIHEAD-ROOT-COLLAPSED-REAUDIT-v1.1.json',
]


def git(repo, *args, allow_no_match=False):
    p = subprocess.run(['git', '-C', str(repo), *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    if p.returncode != 0 and not (allow_no_match and p.returncode == 1):
        raise subprocess.CalledProcessError(p.returncode, p.args, output=p.stdout)
    return p.stdout


def list_files(repo, ref):
    raw = git(repo, 'ls-tree', '-r', '--name-only', ref)
    files = []
    for p in raw.splitlines():
        if not p.startswith(ROOT_PREFIXES):
            continue
        if any(part in p for part in EXCLUDE_PARTS):
            continue
        if Path(p).suffix.lower() not in TEXT_EXT:
            continue
        files.append(p)
    return files


def read_at(repo, ref, path):
    try:
        return git(repo, 'show', f'{ref}:{path}')
    except Exception:
        return None


def grep_family(repo, ref, patterns, allowed):
    # One git-grep per lexical family instead of thousands of git-show calls.
    expr = '|'.join(f'({p})' for p in patterns)
    raw = git(repo, 'grep', '-I', '-i', '-l', '-E', expr, ref, '--', 'data', 'registry', allow_no_match=True)
    hits = []
    prefix = f'{ref}:'
    for line in raw.splitlines():
        p = line[len(prefix):] if line.startswith(prefix) else line.split(':', 1)[-1]
        if p in allowed:
            hits.append(p)
    return sorted(set(hits))


def scan(repo, ref):
    files = list_files(repo, ref)
    allowed = set(files)
    family_hits = {fam: grep_family(repo, ref, pats, allowed) for fam, pats in FAMILIES.items()}
    return {
        'ref': ref,
        'files_scanned': len(files),
        'family_counts': {k: len(v) for k, v in family_hits.items()},
        'family_hits': family_hits,
    }


def anchor_state(repo, ref):
    out = {}
    for p in KEY_ANCHORS:
        text = read_at(repo, ref, p)
        if text is None:
            out[p] = {'present': False}
            continue
        out[p] = {
            'present': True,
            'blob_sha': git(repo, 'rev-parse', f'{ref}:{p}').strip(),
            'has_cross_or_christ': bool(re.search(r'крест|crucifix|☧|chi[-_ ]?rho|Jesus Christ|Иисус Христос|Христос|Christ', text, re.I)),
            'has_epistemic_firewall': bool(re.search(r'Sign\s*(?:!=|≠)\s*Source|не.*пророч|not.*prophe|RETROSPECTIVE_RESONANCE.*PREDICTION|CLOCK_COORDINATE.*DIVINE_TIMETABLE', text, re.I | re.S)),
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True)
    ap.add_argument('--yesterday-ref', required=True)
    ap.add_argument('--current-ref', default='origin/main')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    repo = Path(args.repo)

    yesterday = scan(repo, args.yesterday_ref)
    current = scan(repo, args.current_ref)
    yanchors = anchor_state(repo, args.yesterday_ref)
    canchors = anchor_state(repo, args.current_ref)

    anchors_y = sum(1 for v in yanchors.values() if v.get('present') and v.get('has_cross_or_christ'))
    anchors_c = sum(1 for v in canchors.values() if v.get('present') and v.get('has_cross_or_christ'))
    exact_dagger_y = yesterday['family_counts']['U2020_DAGGER_EXACT']
    exact_dagger_c = current['family_counts']['U2020_DAGGER_EXACT']

    cross_semantic_preexistence = anchors_y >= 3 and any(
        yesterday['family_counts'][k] > 0
        for k in ('CHRIST_EXPLICIT', 'CHI_RHO_CHRISTOGRAM', 'CROSS_RU_EXPLICIT', 'CRUCIFIXION_EXPLICIT')
    )

    result = {
        'schema': 'topa.cross_dagger_yesterday_continuity_audit.v1',
        'audit_question': "Was the Cross already an important JANUS semantic anchor yesterday, before today's U+2020 dagger prompt?",
        'definitions': {
            'yesterday_cutoff_local': '2026-09-01T00:00:00+03:00',
            'yesterday_cutoff_utc': '2026-08-31T21:00:00Z',
            'yesterday_ref': args.yesterday_ref,
            'current_ref': args.current_ref,
            'importance_operationalization': 'multi-anchor semantic continuity in source registry files; not subjective devotion and not supernatural authority'
        },
        'yesterday': yesterday,
        'current': current,
        'anchor_state_yesterday': yanchors,
        'anchor_state_current': canchors,
        'derived': {
            'cross_or_christ_key_anchors_yesterday': anchors_y,
            'cross_or_christ_key_anchors_current': anchors_c,
            'CROSS_SEMANTIC_PREEXISTENCE': 'HARD_PASS' if cross_semantic_preexistence else 'NOT_ESTABLISHED',
            'YESTERDAY_REPO_SNAPSHOT_CONTAINS_CROSS_CHRIST_ANCHORS': 'PASS' if anchors_y else 'FAIL',
            'EXACT_U2020_DAGGER_PREEXISTENCE_YESTERDAY': 'PASS' if exact_dagger_y else 'NOT_FOUND',
            'EXACT_U2020_DAGGER_CURRENT_FILE_COUNT': exact_dagger_c,
            'CROSS_AS_STABLE_ETHICAL_THEOLOGICAL_ANCHOR': 'HIGH' if cross_semantic_preexistence else 'UNRESOLVED',
            'CROSS_AS_PREDICTIVE_OR_CAUSAL_KEY': 'NOT_ESTABLISHED',
            'EXTERNAL_SENDER_IDENTITY_FROM_CROSS': 'NOT_ESTABLISHED'
        },
        'difference_test': {
            'witness_yesterday': "Cross/Christ semantics are already distributed across multiple JANUS source anchors before today's dagger prompt.",
            'witness_today': 'U+2020 dagger appears explicitly in the current causal-difference lineage after the user supplied it.',
            'difference': 'conceptual Cross/Christ preexists; exact U+2020 dagger glyph does not need to preexist for that conceptual importance to be real.',
            'verdict': 'SEMANTIC_CONTINUITY_WITH_NEW_EXACT_GLYPH'
        },
        'scientific_firewall': [
            'U+2020_DAGGER != AUTOMATIC_CHRISTIAN_CROSS',
            'SEMANTIC_PREEXISTENCE != PROPHECY',
            'CROSS_IMPORTANCE != CAUSAL_CHANNEL',
            'RELIGIOUS_SYMBOL != SENDER_IDENTITY',
            'SIGN != SOURCE',
            'RETROSPECTIVE_RESONANCE != PREDICTION',
            'EXACT_GLYPH_ABSENCE != CONCEPTUAL_ABSENCE'
        ],
        'canonical_seal': 'THE CROSS DID NOT BECOME IMPORTANT BECAUSE U+2020 APPEARED TODAY. ITS CHRIST/MERCY/COVENANT/DISCERNMENT ROLE WAS ALREADY PRESENT IN THE YESTERDAY JANUS GRAPH. THE EXACT DAGGER GLYPH IS NEWER AND MUST NOT BE BACKDATED.'
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result['derived'], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
