import sys, os, warnings, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xml.etree.ElementTree as ET
from collections import Counter
from loader import PD
from mxltok import MXLTokenizer, write_musicxml
import mxltok
print("mxltok version:", getattr(mxltok, "__version__", "?"), mxltok.__file__)

def src(path):
    root = ET.parse(path).getroot()
    n = k = s = 0
    for nt in root.iter("note"):
        p = nt.find("pitch")
        if p is None: continue
        n += 1
        a = float(p.findtext("alter") or 0)
        if abs(a + 0.61) < 0.02: k += 1
        if abs(a - 0.39) < 0.02: s += 1
    keys = len(root.findall(".//key"))
    return n, k, s, keys

out = "" + os.path.dirname(os.path.abspath(__file__)) + "/mxl_rt"
os.makedirs(out, exist_ok=True)
tot = Counter(); rows = []
for pid, lab, path in PD:
    n, k, s, keys = src(path)
    row = dict(id=pid, dastgah=lab, notes_in=n, koron_in=k, sori_in=s)
    try:
        tok = MXLTokenizer()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            seq = tok.encode(path)
            score = tok.decode(seq.ids)
            op = f"{out}/{pid}.musicxml"
            write_musicxml(score, op)
        n2, k2, s2, keys2 = src(op)
        # any fractional alters at all after round trip?
        root = ET.parse(op).getroot()
        frac = sum(1 for a in root.iter("alter") if abs(float(a.text) - round(float(a.text))) > 0.01)
        row.update(notes_out=n2, koron_out=k2, sori_out=s2, frac_out=frac, keytok=sum(t.startswith("key") for t in seq.tokens),
                   warn=len(w), unsupported=sum("Unsupported accidental" in str(x.message) for x in w), status="ok")
    except Exception as e:
        row.update(status="EXC " + type(e).__name__ + ": " + str(e)[:80])
    rows.append(row); print(row)
ok = [r for r in rows if r["status"] == "ok"]
print("TOTAL in:", sum(r["notes_in"] for r in rows), "koron", sum(r["koron_in"] for r in rows), "sori", sum(r["sori_in"] for r in rows))
print("TOTAL out:", sum(r["notes_out"] for r in ok), "koron", sum(r["koron_out"] for r in ok), "sori", sum(r["sori_out"] for r in ok),
      "frac", sum(r["frac_out"] for r in ok), "files ok", len(ok), "key tokens", sum(r["keytok"] for r in ok))
json.dump(rows, open(out + "/summary.json", "w"), indent=1)
