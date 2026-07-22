#!/usr/bin/env python3
from pathlib import Path
import argparse
REQUIRED=['Context', 'Decision', 'Consequences', 'Alternatives', 'Status']
def main():
 p=argparse.ArgumentParser(); p.add_argument('artifact'); a=p.parse_args(); path=Path(a.artifact)
 if not path.is_file(): print('ERROR: missing',path); return 2
 text=path.read_text(encoding='utf-8',errors='replace').lower(); missing=[x for x in REQUIRED if x.lower() not in text]
 if missing: print('FAIL: missing '+', '.join(missing)); return 1
 print(f'PASS: {path} contains {len(REQUIRED)} required control terms'); return 0
if __name__=='__main__': raise SystemExit(main())
