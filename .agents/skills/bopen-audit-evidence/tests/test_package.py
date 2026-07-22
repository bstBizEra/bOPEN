import unittest
from pathlib import Path
import yaml
class PackageTest(unittest.TestCase):
 def test_name(self):
  r=Path(__file__).resolve().parents[1]; d=yaml.safe_load((r/'bopen.skill.yaml').read_text()); self.assertEqual(d['metadata']['name'],r.name)
 def test_files(self):
  r=Path(__file__).resolve().parents[1]
  for x in ['SKILL.md','bopen.skill.yaml','schemas/input.schema.json','schemas/output.schema.json','evals/cases.yaml','policies/execution-policy.yaml']: self.assertTrue((r/x).is_file(),x)
if __name__=='__main__': unittest.main()
