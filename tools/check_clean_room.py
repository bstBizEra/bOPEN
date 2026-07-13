#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
allowed={'README.md','.gitkeep'}
violations=[]
for p in (ROOT/'research/upstream').rglob('*'):
    if p.is_file() and p.name not in allowed:
        violations.append(str(p.relative_to(ROOT)))
if violations:
    print('Clean-room check FAIL')
    print('\n'.join(violations))
    sys.exit(1)
print('Clean-room check PASS')
