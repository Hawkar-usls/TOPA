#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'research/propaganda-defense'
POL=R/'BASE_RATE_CODER_BUNDLE_FREEZE_POLICY.v0.1.json'
OUT=R/'execution/BASE_RATE_CODER_BUNDLE_FREEZE_RUN.v0.1.json'

def sha(b): return hashlib.sha256(b).hexdigest()
def git_blob(p): return subprocess.check_output(['git','hash-object',str(p)],cwd=ROOT,text=True).strip()
def canonical(o): return json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def main():
    pol=json.loads(POL.read_text())
    entries=[]; exists=True; json_ok=True
    for rel in pol['required_files_in_order']:
        p=ROOT/rel
        if not p.exists():
            exists=False; entries.append({'path':rel,'missing':True}); continue
        b=p.read_bytes()
        try: json.loads(b.decode('utf-8'))
        except Exception: json_ok=False
        entries.append({'path':rel,'sha256':sha(b),'git_blob_sha':git_blob(p),'byte_length':len(b)})
    bundle_sha=sha(canonical(entries))
    packet=json.loads((R/'BASE_RATE_CODING_PACKET_TEMPLATE.v0.3.json').read_text())
    schema=json.loads((R/'CROSS_EPOCH_OBSERVABLE_SCHEMA.v0.1.json').read_text())
    retrieval=json.loads((R/'BASE_RATE_8_OF_8_RETRIEVAL_AUTHORITY_MAP.v0.1.json').read_text())
    indep=json.loads((R/'BASE_RATE_INDEPENDENT_CODING_CONTRACT.v0.1.json').read_text())
    sacred=json.loads((R/'SACRED_BASE_RATE_CONTROL_PROTOCOL.v0.1.json').read_text())
    checks={
      'all_required_files_exist':exists,
      'all_files_are_json':json_ok,
      'packet_semantic_values_populated_equals_0':packet.get('current_state',{}).get('semantic_values_populated')==0,
      'packet_issued_to_coders_equals_false':packet.get('current_state',{}).get('issued_to_coders') is False,
      'packet_coder_A_equals_UNASSIGNED':packet.get('current_state',{}).get('coder_A')=='UNASSIGNED',
      'packet_coder_B_equals_UNASSIGNED':packet.get('current_state',{}).get('coder_B')=='UNASSIGNED',
      'retrieval_map_is_8_of_8':retrieval.get('summary',{}).get('retrieval_passes')==8 and retrieval.get('summary',{}).get('required')==8,
      'schema_dimensions_equal_35':len(schema.get('dimensions',[]))==35,
      'independence_contract_requires_two_real_coders':indep.get('coder_requirements',{}).get('required_coders')==2,
      'same_reasoning_instance_cannot_count_twice':indep.get('coder_requirements',{}).get('same_reasoning_instance_may_count_as_two_coders') is False,
      'sacred_flood_firewall_is_closed':sacred.get('blindness_and_contamination',{}).get('flood_test_A_B_must_not_see_this_control_result_before_their_receipts_freeze') is True,
      'score_permission_remains_false':packet.get('current_state',{}).get('score_permission') is False and indep.get('promotion_logic',{}).get('score_permission') is False and sacred.get('score_permission') is False
    }
    final=all(checks.values())
    out={
      'schema':'topa.propaganda_defense.base_rate_coder_bundle_freeze_run.v0.1',
      'date':'2026-08-24','policy_path':str(POL.relative_to(ROOT)),'policy_sha256':sha(POL.read_bytes()),'policy_status':pol['status'],
      'bundle_entries':entries,'bundle_sha256':bundle_sha,'checks':checks,
      'result':{
        'coder_bundle_hash_frozen':bool(final),
        'base_rate_packet_issuance_permission':bool(final),
        'base_rate_semantic_coding_permission':False,
        'coder_A':'UNASSIGNED','coder_B':'UNASSIGNED','semantic_values_populated':0,'score_permission':False,
        'next_required_gate':'TWO_GENUINE_CODER_ASSIGNMENT_RECEIPTS_BOUND_TO_BUNDLE_HASH' if final else 'REPAIR_BUNDLE_FREEZE_FAILURE'
      },
      'laws':pol['laws']
    }
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print('TOPA_BASE_RATE_CODER_BUNDLE_FREEZE_V0_1='+('PASS' if final else 'FAIL'))
    print('CHECKS_PASS='+str(sum(bool(v) for v in checks.values()))+'/'+str(len(checks)))
    print('BUNDLE_SHA256='+bundle_sha)
    print('BUNDLE_FILES='+str(len(entries)))
    print('SEMANTIC_VALUES_POPULATED=0')
    print('CODER_A=UNASSIGNED')
    print('CODER_B=UNASSIGNED')
    print('BASE_RATE_SEMANTIC_CODING_PERMISSION=false')
    print('SCORE_PERMISSION=false')
if __name__=='__main__': main()
