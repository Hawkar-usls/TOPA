"""TOPA Rowan source link only: numerical replay is not biological validation."""
import json,pathlib,unittest
class TestRowanLink(unittest.TestCase):
    def test_link_has_no_model_or_spend_authority(self):
        root=pathlib.Path(__file__).resolve().parents[1]
        doc=json.loads((root/'.janus/ROWAN_INDEPENDENT_SOURCE_LINK.json').read_text(encoding='utf-8'))
        self.assertEqual(doc['schema'],'janus.topa.rowan_independent_replay_source_link.v1')
        self.assertEqual(doc['sourceAuthority'],'Hawkar-usls/janus-meta-registry')
        self.assertEqual(doc['creationSnapshot']['completedPilotMutants'],8)
        self.assertTrue(doc['creationSnapshot']['readCurrentCanonicalBeforeAnyInference'])
        self.assertTrue(all(value is False for value in doc['authority'].values()))
        self.assertFalse(doc['meaning']['modelPromotedToProduction'])
        self.assertEqual(doc['meaning']['publicProcessedAssay'],'NOT_INDEPENDENT_WETLAB')
        self.assertTrue(doc['readOnlyReference']['pipeline'].endswith('PIPELINE_STATE.json'))
if __name__ == '__main__':unittest.main()
