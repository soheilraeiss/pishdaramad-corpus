# Analyses

Scripts behind Section 4 of the MIR Day poster. Python 3.10+, `numpy`, `scikit-learn`; `torch` for `gnn.py`; `mxltok` for `tool_mxltok.py`.

The scores are read from `../scores` by default. For the trailer test, download the Radif Corpus v1.0.0 (https://zenodo.org/records/15742125), unzip it, and point `RADIF_CSV` to its `CSV` folder.

```bash
pip install numpy scikit-learn
python stats.py                                  # 1 in 5 microtones, 31% off-grid steps
RADIF_CSV=/path/to/RadifCorpus/CSV python exp1.py   # trailer test: 7 / 7 / 4 of 12
RADIF_CSV=/path/to/RadifCorpus/CSV python sens.py   # same test, 12 method variants
pip install git+https://github.com/andreamust/MxlTok && python tool_mxltok.py
```

| File | Does |
|---|---|
| `loader.py` | Reads the MusicXML scores and the Radif Corpus CSV with exact microtonal pitch (quarter-tone steps; koron −0.61 → −1 step, sori +0.39 → +1 step). |
| `stats.py` | Counts koron/sori notes and melodic steps off the semitone grid. |
| `exp1.py` | Trailer test: one duration-weighted 24-bin pitch profile per radif dastgāh; each pishdarāmad is matched by correlation over all transpositions. Three conditions: quarter-tone aware, koron read as flat, koron read as natural. |
| `sens.py` | Robustness check of `exp1.py` over 12 method variants. |
| `gnn.py` | A first small GNN (not on the poster; kept for future work). |
| `tool_mxltok.py` | Encodes and decodes the scores with MxlTok and counts what survives. |

Twelve pieces is a small sample: read every number as indicative.
