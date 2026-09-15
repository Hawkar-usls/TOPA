#!/usr/bin/env python3
"""Execute pre-frozen base-rate packet issuance unlock policy v0.1.

This gate can authorize issuing the same zero-value packet to two genuine independent
coders. It cannot assign coders, populate semantic cells, compare outputs, classify
sacred texts or unlock SCORE.
"""
from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'research/propaganda-defense'
POL=R/'BASE_RATE_PACKET_ISSUANCE_UNLOCK_POLICY.v0.1.json'
OUT=R/'execution/BASE_RATE_PACKET_ISSUANCE_UNLOCK_RUN.v0.1.json'

def sha(b):return hashlib.sha256(b).hexdigest()
def load(name):return json.loads((R/name).read_text())
def git_blob(path):
 return subprocess.check_output(['git','hash-object',str(path)],cwd=ROOT,text=True).strip()
def main():
 pol=load('BASE_RATE_PACKET_ISSUANCE_UNLOCK_POLICY.v0.1.json')
 ret=load('BASE_RATE_8_OF_8_RETRIEVAL_AUTHORITY_MAP.v0.1.json')
 loci=load('ANCIENT_BASE_RATE_EXACT_SUBLOCUS_FREEZE.v0.1.json')
 desc=load('ANCIENT_BASE_RATE_DESCRIPTOR_COMMITMENTS.v0.1.json')
 schema=load('CROSS_EPOCH_OBSERVABLE_SCHEMA.v0.1.json')
 pkt=load('BASE_RATE_CODING_PACKET_TEMPLATE.v0.3.json')
 indep=load('BASE_RATE_INDEPENDENT_CODING_CONTRACT.v0.1.json')
 sacred=load('SACRED_BASE_RATE_CONTROL_PROTOCOL.v0.1.json')
 pkt_path=R/'BASE_RATE_CODING_PACKET_TEMPLATE.v0.3.json'; ind_path=R/'BASE_RATE_INDEPENDENT_CODING_CONTRACT.v0.1.json'
 ids=[c.get('id') for c in ret.get('controls',[])]
 pass_controls=[c for c in ret.get('controls',[]) if c.get('status')=='PASS']
 source_roots=[c.get('source_root_count') for c in ret.get('controls',[])]
 semantic_receipt_candidates=[]
 for p in R.glob('*.json'):
  n=p.name.upper()
  if any(k in n for k in ('CODER_A_RECEIPT','CODER_B_RECEIPT','DISAGREEMENT_MANIFEST','ARBITRATED_MATRIX','SEMANTIC_MATRIX')):
   semantic_receipt_candidates.append(p.name)
 for p in (R/'execution').glob('*.json') if (R/'execution').exists() else []:
  n=p.name.upper()
  if any(k in n for k in ('CODER_A_RECEIPT','CODER_B_RECEIPT','DISAGREEMENT_MANIFEST','ARBITRATED_MATRIX','SEMANTIC_MATRIX')):
   semantic_receipt_candidates.append('execution/'+p.name)
 checks={
  'retrieval_map_status_contains_EIGHT_OF_EIGHT':'EIGHT_OF_EIGHT' in ret.get('status',''),
  'retrieval_map_has_exactly_8_unique_PASS_controls':len(pass_controls)==8 and len(set(ids))==8 and len(ids)==8,
  'every_control_source_root_count_equals_1':source_roots==[1]*8,
  'transport_mirrors_add_zero_independent_roots':ret.get('summary',{}).get('transport_mirrors_counted_as_independent_roots')==0,
  'exact_locus_summary_is_8_of_8':loci.get('summary',{}).get('exact_control_loci_frozen')==8 and loci.get('summary',{}).get('required')==8,
  'descriptor_summary_is_8_of_8':desc.get('summary',{}).get('descriptor_commitments')=='8/8 FROZEN' and desc.get('summary',{}).get('exact_loci')=='8/8 FROZEN',
  'cross_epoch_schema_has_exactly_35_dimensions':len(schema.get('dimensions',[]))==35 and [x.get('id') for x in schema.get('dimensions',[])]==[f'X{i:02d}' for i in range(1,36)],
  'packet_has_exactly_8_controls_and_35_features':len(pkt.get('controls',[]))==8 and len(pkt.get('feature_ids',[]))==35,
  'packet_semantic_values_populated_equals_0':pkt.get('current_state',{}).get('semantic_values_populated')==0 and pkt.get('feature_cell_contract',{}).get('value') is None,
  'packet_issued_to_coders_is_false':pkt.get('current_state',{}).get('issued_to_coders') is False,
  'packet_coder_A_is_UNASSIGNED':pkt.get('current_state',{}).get('coder_A')=='UNASSIGNED',
  'packet_coder_B_is_UNASSIGNED':pkt.get('current_state',{}).get('coder_B')=='UNASSIGNED',
  'packet_git_blob_matches_policy':git_blob(pkt_path)==pol['required_authorities']['packet_git_blob_sha'],
  'independence_contract_git_blob_matches_policy':git_blob(ind_path)==pol['required_authorities']['independence_contract_git_blob_sha'],
  'independence_contract_required_coders_equals_2':indep.get('coder_requirements',{}).get('required_coders')==2,
  'same_reasoning_instance_may_count_as_two_is_false':indep.get('coder_requirements',{}).get('same_reasoning_instance_may_count_as_two_coders') is False,
  'arbitration_is_prefrozen_before_disagreements':indep.get('arbitration_pre_freeze',{}).get('arbitration_occurs_only_after_A_and_B_receipts_are_both_frozen') is True and indep.get('arbitration_pre_freeze',{}).get('override_requires_written_evidence_reason') is True,
  'sacred_firewall_blocks_flood_A_B_exposure':sacred.get('blindness_and_contamination',{}).get('flood_test_A_B_must_not_see_this_control_result_before_their_receipts_freeze') is True and pkt.get('sacred_firewall',{}).get('may_be_shown_to_flood_coder_A_before_A_receipt_freeze') is False and pkt.get('sacred_firewall',{}).get('may_be_shown_to_flood_coder_B_before_B_receipt_freeze') is False,
  'sacred_protocol_score_permission_is_false':sacred.get('score_permission') is False,
  'no_semantic_coding_receipt_may_preexist':len(semantic_receipt_candidates)==0,
  'retrieval_map_semantic_values_zero':ret.get('summary',{}).get('semantic_values_populated')==0,
  'packet_source_root_firewall':pkt.get('source_root_firewall',{}).get('transport_mirrors_count_as_independent_roots') is False and pkt.get('source_root_firewall',{}).get('archive_timestamps_count_as_independent_roots') is False,
  'unknown_not_absent_lock_present':'UNKNOWN != ABSENT' in pkt.get('locks',[]),
  'no_score_lock_present':'NO_SCORE' in pkt.get('locks',[]) and 'NO_SCORE' in indep.get('laws',[])
 }
 final=all(checks.values())
 packet_sha=sha(pkt_path.read_bytes());ind_sha=sha(ind_path.read_bytes());policy_sha=sha(POL.read_bytes())
 result={
  'ancient_base_rate_external_retrieval':'8/8_FROZEN' if final else 'NOT_UNLOCKED',
  'base_rate_packet_issuance_permission':bool(final),
  'base_rate_semantic_coding_permission':False,
  'coder_A':'UNASSIGNED','coder_B':'UNASSIGNED','semantic_values_populated':0,
  'sacred_target_coding_permission':False,'score_permission':False,
  'next_required_gate':'RECORD_TWO_GENUINE_INDEPENDENT_CODER_ASSIGNMENTS_AND_ISSUE_IDENTICAL_PACKET_HASH' if final else 'REPAIR_GLOBAL_CONSISTENCY_FAILURES'
 }
 out={'schema':'topa.propaganda_defense.base_rate_packet_issuance_unlock_run.v0.1','date':'2026-08-24','policy_path':str(POL.relative_to(ROOT)),'policy_sha256':policy_sha,'policy_status':pol['status'],'authority_hashes':{'packet_sha256':packet_sha,'packet_git_blob_sha':git_blob(pkt_path),'independence_contract_sha256':ind_sha,'independence_contract_git_blob_sha':git_blob(ind_path),'retrieval_map_sha256':sha((R/'BASE_RATE_8_OF_8_RETRIEVAL_AUTHORITY_MAP.v0.1.json').read_bytes()),'exact_loci_sha256':sha((R/'ANCIENT_BASE_RATE_EXACT_SUBLOCUS_FREEZE.v0.1.json').read_bytes()),'descriptors_sha256':sha((R/'ANCIENT_BASE_RATE_DESCRIPTOR_COMMITMENTS.v0.1.json').read_bytes()),'cross_epoch_schema_sha256':sha((R/'CROSS_EPOCH_OBSERVABLE_SCHEMA.v0.1.json').read_bytes())},'checks':checks,'semantic_receipt_candidates':semantic_receipt_candidates,'result':result,'laws':pol['laws']}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 print('TOPA_BASE_RATE_PACKET_ISSUANCE_UNLOCK_V0_1='+('PASS' if final else 'FAIL'))
 print('CHECKS_PASS='+str(sum(bool(x) for x in checks.values()))+'/'+str(len(checks)))
 print('PACKET_SHA256='+packet_sha)
 print('INDEPENDENCE_CONTRACT_SHA256='+ind_sha)
 print('SEMANTIC_RECEIPTS_PREEXIST='+str(len(semantic_receipt_candidates)))
 print('BASE_RATE_PACKET_ISSUANCE_PERMISSION='+str(final).lower())
 print('BASE_RATE_SEMANTIC_CODING_PERMISSION=false')
 print('CODER_A=UNASSIGNED')
 print('CODER_B=UNASSIGNED')
 print('SCORE_PERMISSION=false')
if __name__=='__main__':main()
