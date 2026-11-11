import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from collections import defaultdict
from loader import load_radif, load_pd
from exp1 import q_of
from math import comb
R = load_radif(); P = load_pd()
def hist(ns, mode, weighted):
    h = np.zeros(24)
    for n in ns: h[q_of(n, mode) % 24] += max(n["dur"], 0.25) if weighted else 1
    if mode != 24: h = h[::2] + h[1::2]
    return h / h.sum()
def sim(a, b, kind):
    if kind == "corr": return np.corrcoef(a, b)[0, 1]
    if kind == "cos": return a @ b / np.linalg.norm(a) / np.linalg.norm(b)
    if kind == "bhatt": return np.sum(np.sqrt(a * b))
for weighted in (True, False):
    for kind in ("corr", "cos", "bhatt"):
        for pooled in ("mean", "pooled"):
            out = []
            for mode in (24, "12flat", "12nat"):
                acc = defaultdict(list)
                for d, _, ns in R: acc[d].append(hist(ns, mode, weighted) * (sum(max(n["dur"], .25) for n in ns) if pooled == "pooled" else 1))
                T = {d: np.sum(v, 0) / np.sum(v) for d, v in acc.items()}
                t1 = t3 = 0
                for lab, pid, ns in P:
                    h = hist(ns, mode, weighted)
                    sc = {c: max(sim(np.roll(h, r), t, kind) for r in range(len(h))) for c, t in T.items()}
                    rank = sorted(sc, key=lambda c: -sc[c])
                    t1 += rank[0] == lab; t3 += lab in rank[:3]
                out.append(f"{mode}:{t1}({t3})")
            print(f"weighted={weighted!s:5} {kind:5} {pooled:6}", "  ".join(out))
p = 1 / 13
for k in (4, 5, 7): print("P(X>=%d | n=12, p=1/13) = %.2g" % (k, sum(comb(12, i) * p**i * (1 - p)**(12 - i) for i in range(k, 13))))
