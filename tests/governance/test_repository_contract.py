import unittest
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]

class RepositoryContractTests(unittest.TestCase):
    def test_root_agents_exists(self):
        self.assertTrue((ROOT/'AGENTS.md').is_file())

    def test_scoped_agents_exist(self):
        for d in ['apps','services','packages','contracts','infrastructure','tests','research','docs']:
            self.assertTrue((ROOT/d/'AGENTS.md').is_file(), d)

    def test_research_upstream_is_empty(self):
        allowed={'README.md','.gitkeep'}
        files=[p for p in (ROOT/'research/upstream').rglob('*') if p.is_file() and p.name not in allowed]
        self.assertEqual(files,[])

    def test_contract_json_parses(self):
        for p in (ROOT/'docs/06-contracts').rglob('*.json'):
            json.loads(p.read_text(encoding='utf-8'))

    def test_bootstrap_artifact_present(self):
        text=(ROOT/'BOPEN-BOOT-001.md').read_text(encoding='utf-8')
        self.assertIn('Approved for bootstrap execution',text)
        self.assertIn('does not authorize production',text.lower())

if __name__=='__main__': unittest.main()
