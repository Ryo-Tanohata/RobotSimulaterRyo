# Paper 1 (draft): Does an LLM Village Retrace Human History?

Observational study of the existing river-valley LLM-agent run (days 0–13079, paused in G9). No new simulation was run for this paper.

## Files

| File | What |
|---|---|
| `main.tex` | The paper (arXiv-style LaTeX, `article` class, natbib + `plainnat`) |
| `refs.bib` | Bibliography (every entry checked on 2026-10-29; see below) |
| `figures/make_figures.py` | Regenerates the 4 English figures from `sim/society/data/records/season_village.jsonl` (read-only) |
| `figures/fig_*.pdf` / `.png` | Figures used by `main.tex` (PDF) and previews (PNG) |
| `main.pdf` | Built draft (20 pages) |
| `要約_ja.md` | Short Japanese summary for the author |

## Build

```bash
cd paper/paper1
python3 figures/make_figures.py      # optional: regenerate figures (needs matplotlib)
latexmk -pdf main.tex                # or: pdflatex main && bibtex main && pdflatex main && pdflatex main
latexmk -c                           # remove build files
```

Needs a TeX Live with `latex-extra` (tabularx, xurl, enumitem, natbib) and `lmodern`.
On Ubuntu: `apt-get install texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended texlive-bibtex-extra lmodern latexmk`.
For arXiv upload: submit `main.tex`, `refs.bib` (or the generated `main.bbl`), and `figures/*.pdf`.

## Citations: verified vs dropped

Verified (author, year, title, venue checked by web search against DOI/publisher/catalogue records on 2026-10-29):
Park et al. 2023 (UIST); Altera.AL et al. 2024 (arXiv 2411.00114); Piatti et al. 2024 (NeurIPS);
Horton 2023 (NBER WP 31122); Aher, Arriaga & Kalai 2023 (ICML); Argyle et al. 2023 (Political Analysis);
Mei et al. 2024 (PNAS); Akata et al. 2025 (Nature Human Behaviour); Sharma et al. 2024 (ICLR);
Carneiro 1970 (Science); Scott 2017; Graeber & Wengrow 2021; Boehm 1999; Johnson 1982 (pp. 389–421);
Turchin et al. 2013 (PNAS); Hirschman 1970; Kohler et al. 2017 (Nature); Bogaard, Fochesato & Bowles 2019 (Antiquity);
Flannery 2002 (American Antiquity); Englund 2011 (Oxford Handbook, pp. 32–50); Schmandt-Besserat 1992;
Henrich et al. 2005 (BBS 28: 795–855 — note: not 795–815); Bowles 2011 (PNAS); Bocquet-Appel 2002 (Current Anthropology);
Boserup 1965; Ogburn & Thomas 1922; Keeley 1996.

Not cited (mentioned in the project notes but not verified, or not needed): Henrich et al. 2006 (Science), Renfrew et al. 1968 (obsidian),
Goody 1977, Sorokin 1942, Dietler & Hayden 2001, Hayden (aggrandizers), Marcus (dynamic model), Ur et al. 2007/2011, Fried.
Archaeological dates in Table 2 are taken from the project's research notes (`docs/research/`); they are labelled and should be checked against primary sources before submission.

## TODO for the author (本人)

1. **Email** on the title page (`\todo{email}` in `main.tex`).
2. **arXiv category and endorsement**: primary `cs.MA` (multi-agent) or `cs.CY` (computers and society); cross-list `cs.AI`/`cs.CL` maybe. First-time submitters to a category usually need an endorsement.
3. **Model versions**: which exact Claude Haiku / Sonnet / Opus versions were behind the workflow aliases (2026-09-30 to 2026-10-29). Marked `[TODO]` in Section 3.3.
4. **Total cost**: token totals for Society 1.0, G1–G6 and G9 are not consolidated in the logs; add a total (and money cost if you want). Marked `[TODO]` in Section 3.8.
5. **Archive**: make a tagged release / Zenodo DOI of the repository at the analysed commit (`82f49d7f`) and cite it in "Data and code availability".
6. **Check numbers** against your own reading, especially Table 2 (historical dates from project notes, some labelled [mem]), Table 5, and the G8 numbers.
7. **Title**: choose between the current title and alternatives (e.g. "Retracing the Neolithic? …").
8. **Run status**: the paper describes the run as paused at day 13079. If the village is run further before submission, keep the paper's cut-off at 13079 or update all numbers.
9. Remove the red `[TODO]` macros (`\todo{}`) before submitting.
