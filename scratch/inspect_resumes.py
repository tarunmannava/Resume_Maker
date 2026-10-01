import docx

def dump_doc(path):
    print(f"=== {path} ===")
    doc = docx.Document(path)
    for i, s in enumerate(doc.sections):
        print(f"Section {i}: top={s.top_margin.pt if s.top_margin else None}, bot={s.bottom_margin.pt if s.bottom_margin else None}, left={s.left_margin.pt if s.left_margin else None}, right={s.right_margin.pt if s.right_margin else None}")
    for i, p in enumerate(doc.paragraphs):
        if not p.text.strip():
            continue
        runs_desc = " // ".join([f"[{r.text}] (bold={r.bold}, italic={r.italic}, font={r.font.name}, size={r.font.size.pt if r.font.size else None})" for r in p.runs if r.text])
        print(f"P{i:02d} ({p.style.name}): {runs_desc}")

print("--- TARUN MANNAVA ---")
dump_doc("generated_resumes/TarunMannava.docx")
print("\n--- TARUN MANNAVA SE ---")
dump_doc("generated_resumes/TarunMannava_SE.docx")
