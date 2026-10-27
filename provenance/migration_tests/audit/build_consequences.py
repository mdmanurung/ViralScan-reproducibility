import json,sys,collections
journal,outdir=sys.argv[1],sys.argv[2]
fin=[];dec=[];ver={}
for line in open(journal):
    try:o=json.loads(line)
    except: continue
    if o.get("type")!="result": continue
    v=o["result"]
    if isinstance(v,str): v=json.loads(v)
    if "findings" in v: fin+=v["findings"]
    if "decisions" in v: dec+=v["decisions"]
    if "verdicts" in v:
        for x in v["verdicts"]: ver.setdefault(x["path"],[]).append(x)
brk=[];seen=set()
for f in fin:
    if not f["consequence"].startswith("break"): continue
    k=(f["path"],f["consequence"])
    if k in seen: continue
    seen.add(k)
    vs=ver.get(f["path"],[]); ref=any(x["refuted"] for x in vs) if vs else None
    brk.append((f["consequence"],f["path"],ref,f["evidence"][:300],f["fix"][:400]))
brk.sort()
json.dump({"breaks":brk,"decisions":dec},open(f"{outdir}/consequences.json","w"),indent=1)
L=["# Consequence audit on origin/main (6527e94)\n","| consequence | path | R | fix |\n|---|---|---|---|"]
for c,p,r,e,fx in brk: L.append(f"| {c} | `{p}` | {'R' if r else ''} | {fx.replace('|','/')} |")
L+=["\n## Decisions / untracked-or-new items\n","| class | path | note |\n|---|---|---|"]
for x in dec:
    if x["path"].startswith("tests/") and x["destination"]=="package": continue
    L.append(f"| {x['destination']} | `{x['path'][:80]}` | {x['reason'][:240].replace('|','/')} |")
open(f"{outdir}/CONSEQUENCES.md","w").write("\n".join(L)+"\n")
print(len(brk),"claimed breaks;",sum(1 for b in brk if b[2] is True),"refuted;",len(dec),"decisions")
