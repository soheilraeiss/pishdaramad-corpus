"""Loaders with exact microtonal pitch.

Pitch unit: quarter-tone steps (C4 = 120), as in the Radif Corpus CSV.
Pishdaramad MusicXML: koron alter -0.61 -> -1 step, sori +0.39 -> +1 step.
Each note: dict(q=pitch in quarter tones, dur=duration in sixteenths (float),
micro = -1 koron / +1 sori / 0, grace=bool, measure=int, onset=float in sixteenths)
"""
import csv, glob, os, re
import xml.etree.ElementTree as ET

RADIF = os.environ.get("RADIF_CSV", "RadifCorpus/CSV")   # folder "CSV" of the Radif Corpus (Zenodo 15742125)
PD_DIR = os.environ.get("PD_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scores"))                                 # folder with the 12 MusicXML files
STEP = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

PD = [
    ("pd_01", "Shur", os.path.join(PD_DIR, "pd_01_shur_khaleghi.musicxml")),
    ("pd_14", "Abuata", os.path.join(PD_DIR, "pd_14_abuata_marufi.musicxml")),
    ("pd_22", "Bayat-e tork", os.path.join(PD_DIR, "pd_22_bayattork_saba.musicxml")),
    ("pd_29", "Afshari", os.path.join(PD_DIR, "pd_29_afshari_darvish.musicxml")),
    ("pd_44", "Dashti", os.path.join(PD_DIR, "pd_44_dashti_mahjubi.musicxml")),
    ("pd_54", "Segah", os.path.join(PD_DIR, "pd_54_segah_shahnazi.musicxml")),
    ("pd_66", "Chahargah", os.path.join(PD_DIR, "pd_66_chahargah_neydavud.musicxml")),
    ("pd_76", "Mahur", os.path.join(PD_DIR, "pd_76_mahur_shahnazi.musicxml")),
    ("pd_86", "Homayun", os.path.join(PD_DIR, "pd_86_homayun_vaziri.musicxml")),
    ("pd_93", "Bayat-e esfahan", os.path.join(PD_DIR, "pd_93_esfahan_forutan.musicxml")),
    ("pd_99", "Nava", os.path.join(PD_DIR, "pd_99_nava_azhang.musicxml")),
    ("pd_101", "Rast-panjgah", os.path.join(PD_DIR, "pd_101_rast_azhang.musicxml")),
]
RADIF_NAME = {
    "01 - Shur": "Shur", "02 - Bayat-e-kord": "Bayat-e kord", "03 - Dashti": "Dashti",
    "04 - Bayat-e-Tork": "Bayat-e tork", "05 - Abuata": "Abuata", "06 - Afshari": "Afshari",
    "07 - Segah": "Segah", "08 - Nava": "Nava", "09 - Homayun": "Homayun",
    "10 - Bayat-e Esfahan": "Bayat-e esfahan", "11 - Chahargah": "Chahargah",
    "12 - Mahur": "Mahur", "13 - Rast - Panjgah": "Rast-panjgah",
}


def load_radif():
    """-> list of (dastgah, gusheh name, notes)"""
    out = []
    for d in sorted(os.listdir(RADIF)):
        if d not in RADIF_NAME:
            continue
        for f in sorted(glob.glob(os.path.join(RADIF, d, "*.csv"))):
            if "pathway" in f:
                continue
            notes, t = [], 0.0
            with open(f, newline="", encoding="utf-8-sig") as fh:
                rd = csv.reader(fh)
                next(rd)
                for row in rd:
                    if not row or row[0] in ("[", "]", ""):
                        continue
                    lab = row[0].strip()
                    try:
                        q = int(float(row[2])); dur = float(row[1])
                    except ValueError:
                        continue
                    m = re.match(r"^([A-G])([b#]?)(k|\+1|-1|s)?", lab)
                    micro = 0
                    if q % 2:  # odd number of quarter tones: a microtonal degree
                        micro = -1 if (m and m.group(3) in ("k", "-1")) else 1
                    notes.append(dict(q=q, dur=dur, micro=micro, grace=False, measure=0, onset=t, lab=lab))
                    t += dur
            out.append((RADIF_NAME[d], os.path.basename(f)[:-4], notes))
    return out


def load_musicxml(path):
    root = ET.parse(path).getroot()
    part = root.find("part")
    div, notes, t = 1, [], 0.0
    for meas in part.findall("measure"):
        num = int(re.sub(r"\D", "", meas.get("number")) or 0)
        for el in meas:
            if el.tag == "attributes" and el.find("divisions") is not None:
                div = int(el.findtext("divisions"))
            if el.tag == "backup":
                t -= int(el.findtext("duration")) / div * 4
            if el.tag == "forward":
                t += int(el.findtext("duration")) / div * 4
            if el.tag != "note":
                continue
            grace = el.find("grace") is not None
            dur = 0.0 if grace else int(el.findtext("duration")) / div * 4
            chord = el.find("chord") is not None
            p = el.find("pitch")
            if p is not None:
                alter = float(p.findtext("alter") or 0)
                micro = 0
                if abs(alter - round(alter)) > 0.01:
                    micro = -1 if alter < 0 else 1
                semis = 12 * (int(p.findtext("octave")) + 1) + STEP[p.findtext("step")]
                q = semis * 2 + (round(alter * 2) if micro == 0 else micro + 2 * int(alter - (micro * 0.61 if micro < 0 else 0.39 * micro)))
                # tie: skip the continuation note, add its duration to the start note
                tie_stop = any(tt.get("type") == "stop" for tt in el.findall("tie"))
                onset = t - (notes[-1]["dur"] if chord and notes else 0) if chord else t
                if tie_stop and notes and notes[-1]["q"] == q:
                    notes[-1]["dur"] += dur
                else:
                    notes.append(dict(q=q, dur=dur, micro=micro, grace=grace, measure=num, onset=onset,
                                      cents=semis * 100 + alter * 100, chord=chord))
            if not chord:
                t += dur
    return notes


def load_pd():
    return [(lab, pid, load_musicxml(p)) for pid, lab, p in PD]


if __name__ == "__main__":
    from collections import Counter
    R = load_radif()
    print("radif gushehs:", len(R), "notes:", sum(len(n) for _, _, n in R))
    print(Counter(d for d, _, _ in R))
    labs = Counter(n["lab"] for _, _, ns in R for n in ns)
    print("labels:", sorted(labs.items(), key=lambda x: -x[1])[:60])
    print("micro share radif:", sum(1 for _, _, ns in R for n in ns if n["micro"]) / sum(len(n) for _, _, n in R))
    odd = Counter((n["lab"], n["q"] % 24) for _, _, ns in R for n in ns if n["q"] % 2)
    print("odd-q labels:", odd.most_common(40))
    P = load_pd()
    for lab, pid, ns in P:
        print(pid, lab, len(ns), "koron", sum(n["micro"] < 0 for n in ns), "sori", sum(n["micro"] > 0 for n in ns),
              "grace", sum(n["grace"] for n in ns), "chordnotes", sum(n.get("chord", False) for n in ns),
              "q-range", min(n["q"] for n in ns), max(n["q"] for n in ns))
