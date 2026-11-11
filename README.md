# Pishdarāmad Corpus

A machine-readable corpus of Persian **pishdarāmads**: the composed, metric, instrumental preludes that open a dastgāh performance. To our knowledge, it is the first machine-readable corpus of the metric, composed repertoire of Persian classical music.

**Pilot release: 12 pieces, exactly one per dastgāh / āvāz.** Next: all 101 pieces of the source edition.

Presented at **Barcelona MIR Day, 13 November 2026 (UPF)**:
*Preserving Non-Metric Microtonal Traditions: Towards a Graph Neural Network Framework for Persian Classical Music*, Seyed Soheil Raeisossadati (Music Technology Group, Universitat Pompeu Fabra).

## Contents

| Path | What |
|---|---|
| `scores/` | 12 MusicXML 4.0 files, one per piece |
| `metadata.csv` | one row per piece: book number and page, dastgāh, composer, metre, counts, encoding notes |
| `analysis/` | Python scripts behind the numbers on the poster |

## The 12 pieces

| ID | Dastgāh / āvāz | Composer | Metre | Notes | Koron | Sori |
|---|---|---|---|---|---|---|
| pd_01 | Shur | Ruhollah Khaleghi | 4/4 | 180 | 55 | 0 |
| pd_14 | Abuata | Musa Ma'rufi | 6/4 → 2/4 | 327 | 60 | 0 |
| pd_22 | Bayat-e tork | Abolhassan Saba | 2/4 | 349 | 33 | 0 |
| pd_29 | Afshari | Gholamhossein Darvish (Darvish Khān) | 2/4 | 243 | 31 | 0 |
| pd_44 | Dashti | Reza Mahjubi | 6/4 | 258 | 54 | 0 |
| pd_54 | Segāh | Ali-Akbar Shahnāzi | 2/4 | 416 | 217 | 6 |
| pd_66 | Chahārgāh | Morteza Neydāvud | 2/4 | 331 | 105 | 0 |
| pd_76 | Māhur | Ali-Akbar Shahnāzi | 2/4 | 188 | 0 | 0 |
| pd_86 | Homāyun | Ali-Naqi Vaziri | 3/4 → 2/4 | 647 | 127 | 0 |
| pd_93 | Bayat-e esfahan | Yusef Forutan | 2/4 | 115 | 15 | 0 |
| pd_99 | Navā | Ebrahim Azhang | 2/4 | 505 | 73 | 0 |
| pd_101 | Rāst-panjgāh | Ebrahim Azhang | 2/4 | 231 | 0 | 0 |
| **Total** | 12 | 10 composers | | **3,790** | **770** | **6** |

Māhur and Rāst-panjgāh use no koron: they act as 12-tone controls.

## Encoding

- Standard MusicXML 4.0, so the files open in MuseScore and other notation software.
- **Koron** is written as `<alter>-0.61</alter>` with `<accidental>koron</accidental>`; **sori** as `<alter>0.39</alter>` with `<accidental>sori</accidental>`.
- These values (−61 and +39 cents) are a notation-level constant. Real intonation varies between performers and is left to audio.
- Non-traditional key signatures (e.g. B♭, E♭, A-koron) use `key-step` / `key-alter`.
- Repeats and 1st/2nd endings are kept as written; one- and two-bar repeat signs are written out.

Each score was transcribed from the printed edition and checked note by note against it.

## Source

All scores come from *101 Pishdarāmad*, edited by **Arshad Tahmasbi** (Mahoor Institute of Culture and Art, Tehran). The edition is written for all instruments and avoids instrument-specific markings.

**Audio.** The book's companion CD contains a performance of every piece. The recordings are **not** included in this repository, because the rights belong to their holders. Anyone who owns the CD can pair it with these scores.

## Analyses

See [`analysis/README.md`](analysis/README.md). The scripts reproduce the poster's numbers:
- 1 in 5 notes is a koron or sori; 31% of melodic steps fall off the semitone grid;
- current tools (MxlTok 0.1.0, Partitura 1.9.0) do not yet keep koron/sori;
- the "trailer test": pitch profiles learnt only from the non-metric radif (Radif Corpus) name the dastgāh of 7 of 12 pishdarāmads; 4 of 12 if koron is read as natural.

## Licence

- **Scores and metadata:** [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/). Credit the editor (A. Tahmasbi), the publisher (Mahoor) and this corpus.
- **Code in `analysis/`:** MIT (see `LICENSE-code`).

## Citation

> Raeisossadati, S. S. (2026). *Preserving Non-Metric Microtonal Traditions: Towards a Graph Neural Network Framework for Persian Classical Music*. Late-breaking poster, Barcelona MIR Day, Universitat Pompeu Fabra.

## Related work

- Kanani et al. (2025). Radif Corpus. ISMIR. https://zenodo.org/records/15742125
- Karaosmanoğlu (2012). A Turkish makam music symbolic database (SymbTr). ISMIR.
- Serra, X. (2014). Creating research corpora for the computational study of music: the case of the CompMusic project. AES Conference on Semantic Audio.
