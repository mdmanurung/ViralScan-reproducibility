import json,sys,csv,collections
journal,outdir=sys.argv[1],sys.argv[2]
rows=[];keep=[];plan=[]
for line in open(journal):
    try:o=json.loads(line)
    except: continue
    if o.get("type")!="result": continue
    v=o["result"]
    if isinstance(v,str): v=json.loads(v)
    if "sections" in v:
        for s in v["sections"]:
            plan.append(s)
            rows.append(("PLAN.md",f'{s["line_start"]}-{s["line_end"]}',s["title"],s["default_class"],s["reason"]))
            for e in s.get("exceptions",[]): rows.append(("PLAN.md",f'L{e.get("line","")}',f'{e["id"]} (exception in "{s["title"][:40]}")',e["class"],e.get("reason","")))
            for r in s.get("keep_refs",[]): keep.append((s["title"],r["id"],r["referenced_by"]))
    elif "entries" in v:
        ids=[e["id"] for e in v["entries"]]
        name=".living/learnings.md" if sum(i.startswith("L") for i in ids)>len(ids)/2 else ".living/decisions.md"
        for e in v["entries"]:
            rows.append((name,"",e["id"]+" "+e.get("title",""),e["class"],e["reason"]))
            if e.get("keep_refs"): keep.append((name,e["id"],e["keep_refs"]))
    elif "files" in v:
        for f in v["files"]:
            rows.append((f["path"],"","",f["class"],f["reason"]))
            if f.get("keep_refs"): keep.append(("files",f["path"],f["keep_refs"]))
csv.writer(open(f"{outdir}/triage.tsv","w",newline=""),delimiter="\t").writerows([["file","where","item","class","reason"]]+rows)
csv.writer(open(f"{outdir}/triage_keep_refs.tsv","w",newline=""),delimiter="\t").writerows([["area","id","referenced_by"]]+keep)
print(len(rows),"rows",len(keep),"keep_refs")
for f in ("PLAN.md",".living/decisions.md",".living/learnings.md"):
    print(f,dict(collections.Counter(r[3] for r in rows if r[0]==f)))
print("-- PLAN sections (main)")
for s in sorted(plan,key=lambda s:s["line_start"]): print(f'{s["line_start"]:>5}-{s["line_end"]:<5} {s["default_class"]:10s} exc={len(s.get("exceptions",[])):<3d} {s["title"][:70]}')
