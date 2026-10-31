# Paper 2 (draft): Personality Words or Life Circumstances?

Probing human-like rule-bending in LLM respondents with the 2016 survey of the author's 2017 master's thesis
(54 items on everyday rights violations). Two pre-registered experiments (Exp. 1: commit `2c8f966c`, Exp. 2: `b88ad84c`),
520 simulated respondents (Claude Sonnet / Haiku / Opus), plus an exploratory dictionary coding of 1,150 reasons.

## Files

| File | What |
|---|---|
| `main.tex` | The paper (`article`, natbib + `plainnat`, same style as paper 1) |
| `refs.bib` | Bibliography (every entry checked by web search on 2026-10-29/30; see below) |
| `figures/make_figures.py` | Regenerates the 5 English figures from `sim/society/tools/survey/out/` and `out_exp2/` (read-only) |
| `figures/make_tables.py` | Writes `figures/items_table.tex` (Appendix: 54 items, English gloss, norm, LLM means) |
| `figures/fig_*.pdf` / `.png` | Figures used by `main.tex` (PDF) and previews (PNG) |
| `main.pdf` | Built draft (15 pages) |
| `要約_ja.md` | Short Japanese summary for the author |

Sources of the numbers: `docs/research/humanity/paper2_exp1_results.md`, `paper2_exp2_results.md`,
`sim/society/tools/survey/out/summary.md`, `out_exp2/summary.md`, `out_exp2/reasons_summary.md`.

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

## TODO for the author (本人)

1. **Email** on the title page (`\todo{email}`).
2. **Sacks quote**: which source did the thesis use? Keep the footnote, or replace it with the real source (or drop the attribution).
3. **Thesis reference**: check the romanised title / English translation and the exact school name in `refs.bib` (`tanohata2017thesis`).
4. **Model versions** behind the `sonnet` / `haiku` / `opus` aliases on 2026-10-29 (Section 3.2).
5. **Consent / ethics**: confirm the 2016 survey wording and that publishing aggregates (Table 3 values) is fine (Section 7).
6. **Archive**: tagged release / Zenodo DOI of the repository at the analysed commits.
7. **Title**: current title says "2016 survey" (the survey was run in 2016; the thesis is 2017). Alternative suggested in the brief:
   "… with a 2017 survey of everyday rights violations".
8. **English item glosses** (Appendix Table 3) are Claude's translations, not validated; check them.
9. **Reasons coding** (Section 4.3) is exploratory and single-coder (Claude). A second human coder on a sample would strengthen it.
10. Remove red `[TODO]` macros before submission; choose arXiv category (e.g. `cs.CL` or `cs.CY`).
11. ~~**Interview-derived passages (本人が目で確かめる)**~~ **Checked by the author 2026-10-31 (see `docs/research/humanity/thesis2017_interview_check.md`); re-check if changed.**: these use findings that came from the 2016 interviews (not raw quotes): Section 1 and 4.3 / Fig. reasons (the thesis's "seven ways of thinking"), Section 5 H9 paragraph ("students cited money"), Section 6 paragraph on "weak position" and "ease". Rule (2026-10-30): nothing interview-derived is used without the author's visual check.
