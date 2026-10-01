import json
from pathlib import Path

data = json.load(open('scratch/all_5_docx_dump.json', encoding='utf-8'))

for stack in ['ai', 'node', 'java', 'dotnet', 'python']:
    out = [f"################### {stack.upper()} ###################"]
    for p in data[stack]:
        out.append(f"{p['style']}: {p['text']}")
    Path(f"scratch/{stack}_dump.txt").write_text("\n".join(out), encoding="utf-8")
    print(f"Wrote scratch/{stack}_dump.txt ({len(data[stack])} paragraphs)")
