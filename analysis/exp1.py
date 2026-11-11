"""Experiment 1: pitch-class template matching, transposition-invariant.
Train: Radif Corpus (229 non-metric gushehs, 13 classes). Test: 12 pishdaramads.
Conditions: 24-step (quarter-tone aware) vs 12-step (koron/sori read as naturals).
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, json
from collections import defaultdict, Counter
from sklearn.model_selection import StratifiedKFold
from loader import load_radif, load_pd

FAMILY = {"Shur": "Shur", "Abuata": "Shur", "Dashti": "Shur", "Bayat-e tork": "Shur", "Afshari": "Shur", "Bayat-e kord": "Shur",
          "Homayun": "Homayun", "Bayat-e esfahan": "Homayun", "Segah": "Segah", "Chahargah": "Chahargah",
          "Mahur": "Mahur", "Rast-panjgah": "Rast-panjgah", "Nava": "Nava"}

def q_of(n, mode):
    if mode == 24: return n["q"]
    if mode == "12nat": return n["q"] - n["micro"]          # koron/sori -> natural
    if mode == "12flat": return n["q"] + n["micro"] if n["micro"] else n["q"]  # koron -> flat, sori -> sharp (nearest below/above)
def hist(ns, mode):
    h = np.zeros(24)
    for n in ns:
        h[q_of(n, mode) % 24] += max(n["dur"], 0.25)
    if mode != 24: h = h[::2] + h[1::2]
    return h / h.sum()

def templates(items, mode):
    acc = defaultdict(list)
    for d, _, ns in items: acc[d].append(hist(ns, mode))
    return {d: np.mean(v, axis=0) for d, v in acc.items()}

def predict(h, T, rot=True):
    best = {}
    for c, t in T.items():
        rs = range(len(h)) if rot else [0]
        best[c] = max(np.corrcoef(np.roll(h, r), t)[0, 1] for r in rs)
    return sorted(best, key=lambda c: -best[c]), best

if __name__ == "__main__":
    R = load_radif(); P = load_pd()
    y = np.array([d for d, _, _ in R])
    res = {}
    for mode in (24, "12nat", "12flat"):
        # (a) 5-fold CV inside the Radif Corpus (gusheh level)
        accs = []
        for seed in range(5):
            skf = StratifiedKFold(n_splits=4, shuffle=True, random_state=seed)  # smallest class has 4 gushehs
            ok = 0
            for tr, te in skf.split(np.zeros(len(R)), y):
                T = templates([R[i] for i in tr], mode)
                ok += sum(predict(hist(R[i][2], mode), T)[0][0] == R[i][0] for i in te)
            accs.append(ok / len(R))
        # (b) radif -> pishdaramad
        T = templates(R, mode)
        rows = []
        for lab, pid, ns in P:
            rank, sc = predict(hist(ns, mode), T)
            rows.append((pid, lab, rank[0], rank[:3], rank.index(lab) + 1))
        top1 = sum(r[1] == r[2] for r in rows); top3 = sum(r[1] in r[3] for r in rows)
        fam = sum(FAMILY[r[1]] == FAMILY[r[2]] for r in rows)
        res[str(mode)] = dict(cv_mean=float(np.mean(accs)), cv_sd=float(np.std(accs)), top1=top1, top3=top3, family=fam,
                              rows=[(r[0], r[1], r[2], r[4]) for r in rows])
        print(f"\n== {mode}: radif CV acc {np.mean(accs):.3f} ± {np.std(accs):.3f} | pishdaramad top1 {top1}/12 top3 {top3}/12 family {fam}/12")
        for r in rows: print(f"   {r[0]:7s}{r[1]:16s} -> {r[2]:16s} {'OK' if r[1]==r[2] else '  '} rank {r[4]}  top3 {r[3]}")
    json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "exp1.json"), "w"), indent=1)
