#!/usr/bin/env python3
from pathlib import Path
import json, hashlib, re
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
records=[]
for p in sorted((ROOT/'docs').rglob('*')):
    if not p.is_file() or p.name=='DOCUMENT-MANIFEST.json': continue
    data=p.read_bytes()
    text=data.decode('utf-8','replace') if p.suffix in {'.md','.json','.yaml','.yml'} else ''
    title=''
    for line in text.splitlines():
        if line.startswith('# '): title=line[2:].strip(); break
    status=''
    m=re.search(r'\*\*Status:\*\*\s*([^\n]+)',text)
    if m: status=m.group(1).strip()
    records.append({'path':str(p.relative_to(ROOT)).replace('\\','/'),'title':title,'status':status,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
out={'generated':datetime.now(timezone.utc).date().isoformat(),'count':len(records),'documents':records}
(ROOT/'docs/DOCUMENT-MANIFEST.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(f'Wrote {len(records)} records')
