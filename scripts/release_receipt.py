import hashlib
import json
from pathlib import Path
import sys

folder=Path(sys.argv[1]).resolve()
entries=[]
for path in folder.glob('*.exe'):
    with path.open('rb') as stream:
        digest=hashlib.file_digest(stream,'sha256').hexdigest()
    entries.append({'file':path.name,'bytes':path.stat().st_size,'sha256':digest})
(folder/'receipt.json').write_text(json.dumps(entries,indent=2),encoding='utf-8')
(folder/'SHA256.txt').write_text('\n'.join(f'{entry["sha256"]}  {entry["file"]}' for entry in entries)+'\n',encoding='utf-8')
print(json.dumps(entries,indent=2))
