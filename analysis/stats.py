import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import re, json, numpy as np
import xml.etree.ElementTree as ET
from collections import Counter
from loader import PD, STEP

def notes_raw(path):
    """every pitched <note> (ties NOT merged, to match the corpus counts), with exact cents"""
    root = ET.parse(path).getroot(); out = []; nm = 0
    for meas in root.find("part").findall("measure"):
        nm += 1
        for el in meas.findall("note"):
            p = el.find("pitch")
            if p is None: continue
            a = float(p.findtext("alter") or 0)
            c = (12 * (int(p.findtext("octave")) + 1) + STEP[p.findtext("step")]) * 100 + round(a * 100)
            out.append(dict(c=c, micro=abs(a - round(a)) > 0.01, chord=el.find("chord") is not None,
                            tiestop=any(t.get("type") == "stop" for t in el.findall("tie")), m=nm,
                            name=p.findtext("step") + ("k" if abs(a + 0.61) < .02 else "s" if abs(a - 0.39) < .02 else {0: "", -1: "b", 1: "#"}[round(a)])))
    return out, nm

tot = Counter(); ivs = Counter(); rows = []
for pid, lab, path in PD:
    ns, nm = notes_raw(path)
    mel = [n for n in ns if not n["chord"]]
    d = [b["c"] - a["c"] for a, b in zip(mel, mel[1:])]
    nonsemi = sum(1 for x in d if x % 100)
    pcs24 = {n["name"] for n in ns}
    pcs12 = {n["name"].rstrip("ks") for n in ns}
    rows.append((pid, lab, len(ns), sum(n["micro"] for n in ns), len(d), nonsemi, len(pcs24), len(pcs12), nm))
    tot["notes"] += len(ns); tot["micro"] += sum(n["micro"] for n in ns); tot["iv"] += len(d); tot["nonsemi"] += nonsemi
    tot["measures"] += nm; tot["chord"] += sum(n["chord"] for n in ns); tot["next_edges"] += len(d)
    for x in d:
        if x % 100: ivs[abs(x)] += 1
    print(f"{pid:7s}{lab:16s} notes {len(ns):4d} micro {sum(n['micro'] for n in ns):4d} ({sum(n['micro'] for n in ns)/len(ns)*100:4.1f}%)  intervals {len(d):4d} non-12TET {nonsemi:4d} ({nonsemi/len(d)*100:4.1f}%)  pitch names 24:{len(pcs24)} -> 12:{len(pcs12)}  {sorted(pcs24)}")
print(dict(tot))
print("share microtonal notes: %.1f%%" % (tot["micro"] / tot["notes"] * 100))
print("share melodic intervals not on the semitone grid: %.1f%%" % (tot["nonsemi"] / tot["iv"] * 100))
print("with koron pieces only (10):", sum(r[5] for r in rows if r[3]) / sum(r[4] for r in rows if r[3]))
print("non-12TET interval sizes (cents: count):", sorted(ivs.items(), key=lambda x: -x[1])[:14])
print("neutral seconds (139+161):", ivs[139] + ivs[161], "| neutral thirds (339+361):", ivs[339] + ivs[361])
print("graph: note nodes", tot["notes"], "measure nodes", tot["measures"], "work nodes", len(PD),
      "| edges: next", tot["next_edges"], "note-in-measure", tot["notes"], "measure-in-work", tot["measures"], "chord(onset)", tot["chord"])
json.dump(dict(rows=rows, tot=dict(tot), ivs=dict(ivs)), open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "stats.json"), "w"))
