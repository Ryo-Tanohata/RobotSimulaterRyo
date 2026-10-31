# Paper 2 (draft): A Strictness Dial and Content-Matched Shifts

**Title (new, 2026-10-31):** "A Strictness Dial and Content-Matched Shifts: Two Layers of Variation in LLM Respondents to a 2016 Japanese Survey of Everyday Rights Violations".
**Alternative (old title):** "Personality Words or Life Circumstances? Probing Human-Like Rule-Bending in LLM Respondents with a 2016 Japanese Survey of Everyday Rights Violations".

The 54 items on everyday rights violations from the 2016 survey of the author's 2017 master's thesis, answered by 920 simulated respondents
(Claude Sonnet / Haiku / Opus) in four pre-registered survey experiments (Exp. 1: commit `2c8f966c`, Exp. 2: `b88ad84c`,
follow-up 2b: `2b8ffb0b`, follow-up 2c: `154ae7f0`), plus an exploratory dictionary coding of 1,150 reasons, and a pre-registered village
transfer test (Exp. 3: `b1c1ae8a`; 3 arms × 3 simulated years, null result).

**Organizing claim:** LLM respondent variation has two layers. (1) A model-level *strictness dial*: the first principal component is,
in every condition, nearly the respondent's mean answer (|r| ≥ 0.98) and points in nearly the same direction across all six
life-circumstance conditions (|cos| 0.86–0.95). Personality words inflate it (0.39); life circumstances bring it into the human range
(0.23–0.26); surroundings content and personal histories do not reshape it. (2) *Local, content-matched shifts*: each input moves
exactly the matching items and appears as a clean single-domain later component, unlike the human components, which mix domains.
Open question: is the human first component also general strictness? (The thesis raw data are not available, so it cannot be checked.)

Structure: 1 Introduction · 2 Related work · 3 Methods (conditions table incl. E1, D2r, F1, F2) · 4 Results (4.1 Exp 1, 4.2 Exp 2 +
reasons, 4.3 Follow-up 2b, 4.4 Follow-up 2c, 4.5 Exp 3 village; one hypothesis table each; village hypotheses labelled V-H1–V-H5, V-H2b)
· 5 Discussion (5.1 Two layers: Fig. 5 and Table 7 "what moved the first component vs only matching items"; consequences; open question)
· 6 Limitations · 7 Ethics · 8 Data and code availability.

## Files

| File | What |
|---|---|
| `main.tex` | The paper (`article`, natbib + `plainnat`, same style as paper 1) |
| `refs.bib` | Bibliography (every entry checked by web search on 2026-10-29/30; see below) |
| `figures/make_figures.py` | Regenerates the 6 English figures from `sim/society/tools/survey/out/`, `out_exp2/` (read-only); `fig_layers` uses values copied from `out/`, `out_exp2/`, `out_exp2b/`, `out_exp2c/` summaries. `--ja` writes the Japanese PNGs to `figures_ja/` |
| `figures/make_tables.py` | Writes `figures/items_table.tex` (Appendix: 54 items, English gloss, norm, LLM means) |
| `figures/fig_*.pdf` / `.png` | Figures used by `main.tex` (PDF) and previews (PNG) |
| `main.pdf` | Built draft (22 pages) |
| `要約_ja.md` | Short Japanese summary for the author |

Sources of the numbers: `docs/research/humanity/paper2_exp1_results.md`, `paper2_exp2_results.md`, `paper2_exp2b_results.md`,
`paper2_exp2c_results.md`, `paper2_exp3_results.md`; `sim/society/tools/survey/out/summary.md`, `out_exp2/summary.md`,
`out_exp2/reasons_summary.md`, `out_exp2b/summary.md`, `out_exp2c/summary.md`; `docs/research/humanity/data/exp3/summary.md`.
`fig_pc1` is no longer used in `main.tex` (its content is panel (a) of `fig_layers`); the file is kept unchanged.

## Build

```bash
cd paper/paper2
python3 figures/make_figures.py && python3 figures/make_tables.py   # optional (needs matplotlib)
latexmk -pdf main.tex      # or: pdflatex main && bibtex main && pdflatex main && pdflatex main
latexmk -c
```

## Citations: verified vs dropped

Verified (author, year, title, venue; web search against publisher / DOI / ACL Anthology / PMLR / NBER / arXiv / catalogue records):
Argyle et al. 2023 (Political Analysis 31(3):337–351); Horton 2023 (NBER WP 31122); Aher, Arriaga & Kalai 2023 (ICML, arXiv 2208.10264);
Dillion et al. 2023 (Trends in Cognitive Sciences 27(7):597–600); Santurkar et al. 2023 (ICML, PMLR 202:29971–30004);
Bisbee et al. 2024 (Political Analysis 32(4):401–416); Wang, Morgenstern & Dickerson (arXiv 2402.01908; cited as preprint — a journal
version may exist but was not confirmed); Mei et al. 2024 (PNAS); Serapio-García et al. (arXiv 2307.00184; cited as preprint, the
journal version was not confirmed; author order varies between listings); Jiang et al. 2024 (Findings of NAACL, pp. 3605–3627);
Hu & Collier 2024 (ACL, pp. 10289–10307); Maslow 1943 (Psychological Review 50(4):370–396); Freud 1923 / Standard Edition vol. XIX (1961).

Dropped / not cited: van der Linden et al. 2010 (Big Five intercorrelations; not needed), McCrae & Costa 1989 (MBTI labels were not used
in prompts), Henrich et al. 2005 (no economic games here).

**Sacks quote:** "We must humanize technology before it dehumanizes us" could NOT be found in Oliver Sacks's writings or interviews by
web search. A near-identical sentence is widely attributed to Rana el Kaliouby (Affectiva) in talks from ~2018. The paper cites the
sentence "as quoted in the thesis" with a footnote saying this.

**Status (2026-10-31):** not to be submitted to arXiv yet (author's decision); kept submission-ready.

## TODO for the author (本人)

1. **Email** on the title page (`\todo{email}`).
2. **Sacks quote**: which source did the thesis use? Keep the footnote, or replace it with the real source (or drop the attribution).
3. **Thesis reference**: check the romanised title / English translation and the exact school name in `refs.bib` (`tanohata2017thesis`).
4. **Model versions** behind the `sonnet` / `haiku` / `opus` aliases on 2026-10-29 (Section 3.2).
5. **Consent / ethics**: confirm the 2016 survey wording and that publishing aggregates (the thesis's Table 3 values) is fine (Section 7).
6. **Archive**: tagged release / Zenodo DOI of the repository at the analysed commits.
7. **Title**: choose between the new title ("A Strictness Dial and Content-Matched Shifts: …") and the old one ("Personality Words or
   Life Circumstances? …"; see top). Both say "2016 survey" (the survey was run in 2016; the thesis is 2017); alternative:
   "… with a 2017 survey of everyday rights violations".
8. **English item glosses** (Appendix Table 8) are Claude's translations, not validated; check them.
9. **Reasons coding** (Section 4.2, last paragraph) is exploratory and single-coder (Claude). A second human coder on a sample would strengthen it.
10. Remove red `[TODO]` macros before submission; choose arXiv category (e.g. `cs.CL` or `cs.CY`).
11. ~~**Interview-derived passages (本人が目で確かめる)**~~ **Checked by the author 2026-10-31 (see `docs/research/humanity/thesis2017_interview_check.md`); re-check if changed.**: these use findings that came from the 2016 interviews (not raw quotes): Section 1 and 4.2 reasons paragraphs / Fig. reasons (the thesis's "seven ways of thinking"), Section 4.2 H9 paragraph ("students cited money"), Section 5.1 "Consequence (b)" paragraph on "weak position" and "ease" (moved there from the old Discussion on 2026-10-31; meaning unchanged, one exploratory sentence on ease/weakness from Exp 2b added in parentheses — not interview-derived). Rule (2026-10-30): nothing interview-derived is used without the author's visual check.

**Human raw data:** the raw data of the thesis survey are not available (the author confirmed on 2026-10-31). This is not a TODO; the paper states it as the main limitation and an open question (Section 5.1, Section 6).
