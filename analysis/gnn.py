"""Experiment 2: a first small GNN on note graphs with exact intervals on the edges.

Graph per piece: node = note; edges = next / previous note, each labelled with the
melodic interval (quarter-tone steps in the 24-step condition, semitones in the 12-step ones).
Node features: pitch class relative to the piece's most-used pitch class, log duration, grace flag.
Model: 3 GINE-style layers (edge-conditioned sum aggregation), mean+max pooling, linear classifier.
Train: Radif Corpus gushehs (13 classes). Test: 4-fold CV inside the radif, and the 12 pishdaramads.
"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import json, math, numpy as np, torch, torch.nn as nn, torch.nn.functional as F
from sklearn.model_selection import StratifiedKFold
from loader import load_radif, load_pd
from exp1 import q_of, FAMILY
torch.set_num_threads(2)
CLIP = 24  # intervals clipped to +-12 semitones

FEAT = "modal"
def build(ns, mode):
    step = 1 if mode == 24 else 2
    npc = 24 // step
    q = np.array([q_of(n, mode) for n in ns]) // step if mode != 24 else np.array([n["q"] for n in ns])
    dur = np.array([max(n["dur"], 0.25) for n in ns])
    w = np.zeros(npc)
    for a, d in zip(q, dur): w[a % npc] += d
    ref = int(np.argmax(w)) if FEAT == "modal" else 0
    x = np.zeros((len(ns), npc + 2), dtype=np.float32)
    if FEAT != "none": x[np.arange(len(ns)), (q - ref) % npc] = 1
    x[:, npc] = np.log2(dur) / 4
    x[:, npc + 1] = [float(n["grace"]) for n in ns]
    iv = np.clip(np.diff(q), -CLIP // step, CLIP // step)
    src = np.concatenate([np.arange(len(ns) - 1), np.arange(1, len(ns))])
    dst = np.concatenate([np.arange(1, len(ns)), np.arange(len(ns) - 1)])
    nrel = 2 * (CLIP // step) + 1
    rel = np.concatenate([iv + CLIP // step, (-iv) + CLIP // step + nrel])  # forward / backward relation ids
    return x, src, dst, rel, 2 * nrel

def collate(graphs):
    xs, ss, ds, rs, bs, off = [], [], [], [], [], 0
    for i, (x, s, d, r, _) in enumerate(graphs):
        xs.append(x); ss.append(s + off); ds.append(d + off); rs.append(r); bs.append(np.full(len(x), i)); off += len(x)
    t = lambda a, dt: torch.tensor(np.concatenate(a), dtype=dt)
    return t(xs, torch.float32), t(ss, torch.long), t(ds, torch.long), t(rs, torch.long), t(bs, torch.long), len(graphs)

class Net(nn.Module):
    def __init__(self, din, nrel, ncls, h=48, layers=3, p=0.3):
        super().__init__()
        self.inp = nn.Linear(din, h)
        self.rel = nn.ModuleList([nn.Embedding(nrel, h) for _ in range(layers)])
        self.mlp = nn.ModuleList([nn.Sequential(nn.Linear(h, h), nn.ReLU(), nn.Linear(h, h)) for _ in range(layers)])
        self.out = nn.Linear(2 * h, ncls); self.p = p
    def forward(self, x, s, d, r, b, ng):
        h = F.relu(self.inp(x))
        for emb, mlp in zip(self.rel, self.mlp):
            m = F.relu(h[s] + emb(r))
            agg = torch.zeros_like(h).index_add_(0, d, m)
            h = F.dropout(F.relu(mlp(h + agg)), self.p, self.training)
        cnt = torch.zeros(ng).index_add_(0, b, torch.ones(len(b))).clamp(min=1).unsqueeze(1)
        mean = torch.zeros(ng, h.shape[1]).index_add_(0, b, h) / cnt
        mx = torch.full((ng, h.shape[1]), -1e9).scatter_reduce(0, b.unsqueeze(1).expand_as(h), h, "amax")
        return self.out(torch.cat([mean, mx], 1))

def rot(g, k):
    x, s, d, r, nrel = g
    npc = x.shape[1] - 2
    x2 = x.copy(); x2[:, :npc] = np.roll(x[:, :npc], k, axis=1)
    return x2, s, d, r, nrel

def crop(g, rng, lo=48, hi=160):
    if FEAT == "rot": g = rot(g, int(rng.integers(0, g[0].shape[1] - 2)))
    x, s, d, r, nrel = g
    n = len(x)
    L = rng.integers(lo, hi)
    if n <= L: return g
    a = rng.integers(0, n - L)
    keep = (s >= a) & (s < a + L) & (d >= a) & (d < a + L)
    return x[a:a + L], s[keep] - a, d[keep] - a, r[keep], nrel

def train_eval(tr_graphs, ytr, te_sets, ncls, seed, epochs=120):
    torch.manual_seed(seed); rng = np.random.default_rng(seed)
    din, nrel = tr_graphs[0][0].shape[1], tr_graphs[0][4]
    net = Net(din, nrel, ncls); opt = torch.optim.Adam(net.parameters(), lr=3e-3, weight_decay=1e-4)
    cw = torch.tensor(1.0 / np.bincount(ytr, minlength=ncls).clip(min=1), dtype=torch.float32); cw = cw / cw.mean()
    yt = torch.tensor(ytr)
    for ep in range(epochs):
        net.train()
        batch = collate([crop(g, rng) for g in tr_graphs])
        loss = F.cross_entropy(net(*batch), yt, weight=cw)
        opt.zero_grad(); loss.backward(); opt.step()
    net.eval(); outs = []
    with torch.no_grad():
        for gs in te_sets:
            if FEAT == "rot":
                npc = gs[0][0].shape[1] - 2
                outs.append(np.mean([F.softmax(net(*collate([rot(g, k) for g in gs])), 1).numpy() for k in range(npc)], axis=0))
            else:
                outs.append(F.softmax(net(*collate(gs)), 1).numpy())
    return outs

if __name__ == "__main__":
    R = load_radif(); P = load_pd()
    classes = sorted({d for d, _, _ in R}); cid = {c: i for i, c in enumerate(classes)}
    y = np.array([cid[d] for d, _, _ in R]); yp = np.array([cid[l] for l, _, _ in P])
    nseed_cv, nseed_te = int(sys.argv[1]), int(sys.argv[2])
    FEAT = sys.argv[3]; MODES = [24, "12nat", "12flat"] if len(sys.argv) < 5 else [int(m) if m == "24" else m for m in sys.argv[4].split(",")]
    globals()["FEAT"] = FEAT
    res = {}
    for mode in MODES:
        GR = [build(ns, mode) for _, _, ns in R]; GP = [build(ns, mode) for _, _, ns in P]
        cv = []
        for seed in range(nseed_cv):
            ok = 0
            for tr, te in StratifiedKFold(4, shuffle=True, random_state=seed).split(y, y):
                pr = train_eval([GR[i] for i in tr], y[tr], [[GR[i] for i in te]], len(classes), seed)[0]
                ok += int((pr.argmax(1) == y[te]).sum())
            cv.append(ok / len(y)); print(mode, "cv seed", seed, cv[-1], flush=True)
        probs = []
        for seed in range(nseed_te):
            probs.append(train_eval(GR, y, [GP], len(classes), 100 + seed)[0])
        probs = np.array(probs)                       # seeds x 12 x 13
        top1 = (probs.argmax(2) == yp).sum(1)         # per seed
        mean = probs.mean(0); pred = mean.argmax(1)
        rank = [int((np.argsort(-mean[i]) == yp[i]).nonzero()[0][0]) + 1 for i in range(len(P))]
        fam = sum(FAMILY[classes[pred[i]]] == FAMILY[P[i][0]] for i in range(len(P)))
        res[str(mode)] = dict(cv_mean=float(np.mean(cv)), cv_sd=float(np.std(cv)), top1_per_seed=top1.tolist(),
                              top1_mean=float(top1.mean()), top1_sd=float(top1.std()), ens_top1=int((pred == yp).sum()),
                              ens_top3=int(sum(r <= 3 for r in rank)), ens_family=fam,
                              rows=[(P[i][1], P[i][0], classes[pred[i]], rank[i]) for i in range(len(P))])
        print(f"== {mode}: CV {np.mean(cv):.3f}±{np.std(cv):.3f} | pishdaramad top1 per seed {top1.tolist()} mean {top1.mean():.1f} | ensemble top1 {(pred==yp).sum()}/12 top3 {sum(r<=3 for r in rank)}/12 family {fam}/12", flush=True)
        for row in res[str(mode)]["rows"]: print("   ", row)
    json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"gnn_{FEAT}_{MODES[0]}.json"), "w"), indent=1)
