<div align="center">

# Training Feedback Survey Analyser

<p>
  Clean, bilingual Streamlit dashboard for analysing pre/post training survey exports from Microsoft Forms and similar tools.
</p>

<p>
  <img src="https://img.shields.io/badge/Python-3.12%2B-111827?style=flat&logo=python&logoColor=white" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/Streamlit-App-EA580C?style=flat&logo=streamlit&logoColor=white" alt="Streamlit app">
  <img src="https://img.shields.io/badge/Input-CSV%20%7C%20XLSX-0F766E?style=flat" alt="CSV and XLSX input">
  <img src="https://img.shields.io/badge/Charts-Plotly-1D4ED8?style=flat&logo=plotly&logoColor=white" alt="Plotly charts">
  <img src="https://img.shields.io/badge/Export-Excel%20%2B%20CSV-166534?style=flat" alt="Excel and CSV export">
  <img src="https://img.shields.io/badge/AI-OpenAI%20%7C%20Anthropic-6D28D9?style=flat" alt="AI insights">
</p>

<p>
  <a href="#quick-start">Quick start</a> •
  <a href="#deploy-on-streamlit-community-cloud">Deploy</a> •
  <a href="#features">Features</a> •
  <a href="#excel-report-sheets">Excel output</a>
</p>

</div>

> Built for survey teams who need a fast way to merge files, auto-detect columns, validate training quality, and export stakeholder-ready outputs without rewriting survey schemas every time.

## Highlights

| Detect | Analyse | Explain |
|---|---|---|
| Keyword + fuzzy heuristics map columns even when survey labels change. | Sankey transitions, macro/micro quality views, and time-to-apply tables come out in one flow. | Optional AI summaries turn open text into concise findings with traceability. |

| Export | Local-first | Team-friendly |
|---|---|---|
| Download CSV slices, Flourish-ready extracts, and a multi-sheet Excel workbook. | Portable launcher creates the virtualenv and installs dependencies automatically. | English and Italian UI make the app easier to share across mixed teams. |

---

## Quick start

The easiest path for you or anyone who forks this repo is the portable launcher:

```bash
# 1. Run the app with Python 3.12+
python3.12 run_app.py
# Windows: py -3.12 run_app.py
```

Open http://localhost:8501 in your browser.

`run_app.py` is path-independent: it creates `.venv` if missing, installs `requirements.txt` when needed, and launches Streamlit through the virtualenv's interpreter. That means forks and clones can live in any folder name without breaking `pip` or `streamlit` entrypoints.

### Manual setup

If you prefer the classic workflow, this also works:

```bash
python3.12 -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

### Optional AI setup

For local development, create `.streamlit/secrets.toml` from [.streamlit/secrets.toml.example](.streamlit/secrets.toml.example) or use a local `.env`.

```toml
OPENAI_API_KEY = "sk-..."
# or
ANTHROPIC_API_KEY = "sk-ant-..."
```

---

## Deploy on Streamlit Community Cloud

This repo is already structured in the right way for Community Cloud:

- `app.py` is the entrypoint in the repository root.
- `requirements.txt` is in the repository root.
- The app now supports both local `.env` values and Streamlit `st.secrets`.

### Recommended deploy flow

1. Push the repository to GitHub.
2. Open Streamlit Community Cloud and click `Create app`.
3. Select your repository, branch, and set the main file path to `app.py`.
4. Open `Advanced settings` and choose Python `3.12` before deploying.
5. In the `Secrets` field, paste the contents of your local `.streamlit/secrets.toml` if you want AI insights enabled.
6. Click `Deploy`.

### If Streamlit says you can't publish

Check these first:

- The repo must be on GitHub, because Community Cloud deploys from GitHub repositories.
- If the repo is private, Streamlit's docs say the developer needs admin permissions on that repository to deploy from it.
- Make sure you are in the correct Streamlit workspace for the GitHub user or organization that owns the repo.
- If AI is enabled, add `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` in Community Cloud secrets; otherwise the app still runs, but AI insights stay disabled.
- If build logs show a dependency failure, verify `requirements.txt` is complete and that the app is launched from the repo root.

### Local secrets vs cloud secrets

- Local: `.streamlit/secrets.toml` or `.env`
- Cloud: paste the same TOML content into the app's `Advanced settings` -> `Secrets`

---

## Features

| Feature | Details |
|---|---|
| **File upload** | CSV (UTF-8, Latin-1, semicolon-separated) and XLSX (multi-sheet) |
| **Column detection** | Keyword + fuzzy heuristics with manual override UI |
| **Phase 1 – Sankey** | Before → After familiarity transitions, interactive Plotly Sankey |
| **Phase 2 – Full analysis** | Macro + Micro quality tables, reconciliation, time-to-apply |
| **AI insights** | Open-question summaries via datapizza-ai / OpenAI / Anthropic |
| **Exports** | CSV per table, full Excel workbook (8 sheets), Flourish-ready CSVs |
| **Languages** | 🇮🇹 Italiano / 🇬🇧 English — switched from the sidebar |

---

## Column detection — how it works

The app never relies on exact column names. Detection happens in three layers:

1. **Pattern matching** — `Macro [Micro]` bracket pattern → quality columns
2. **Keyword heuristics** — normalised keyword buckets per role (`before`, `after`, `tta`, …)
3. **Fuzzy fallback** — `rapidfuzz` partial-ratio scoring with a configurable threshold

If confidence is low (< threshold), the sidebar shows a manual selectbox for override.

---

## Rating label mapping

| Italian | Canonical | Score |
|---|---|---|
| Insufficiente | Insufficient | 0 |
| Sufficiente | Sufficient | 1 |
| Buono | Good | 2 |
| Eccellente | Excellent | 3 |

Unexpected labels are listed in the Anomalies panel rather than silently dropped.

---

## Time-to-apply mapping

| Italian | Canonical |
|---|---|
| Subito | Immediately |
| Entro un mese | Within a month |
| Entro 3–6 mesi | Within 3–6 months |
| Entro un anno | Within a year |
| Mai | Never |

---

## AI Insights

Set **one** of these secrets before running:

```
OPENAI_API_KEY      # OpenAI summaries via datapizza-ai
ANTHROPIC_API_KEY   # Anthropic fallback
```

Per open-text question the app generates:
- 1-line executive summary
- 3 bullet insights (what worked, criticisms, notable quotes with source traceability)
- Overall sentiment (positive / mixed / negative)

---

## Customising for future survey versions

All mappings are centralised at the top of `app.py`:

| Constant | What to change |
|---|---|
| `RATING_LABEL_MAP` | Add new rating label spellings |
| `TTA_LABEL_MAP` | Add new time-to-apply label spellings |
| `_KW` dict | Extend keyword buckets for column detection |
| `TRANSLATIONS` | Add/edit UI strings for Italian and English |
| `RATING_DISPLAY` / `TTA_DISPLAY` | Change display labels per language |

If a new survey introduces a new quality macro category, it will be auto-detected via the `Macro [Micro]` bracket pattern with no code changes needed.

---

## Excel report sheets

| Sheet | Content |
|---|---|
| Sankey | Before → After transition counts |
| Distributions | Level counts Before/After |
| Macro Quality | Aggregated quality by macro tag |
| Micro Quality | Quality per macro + micro tag |
| Time to Apply | TTA frequency table |
| Detected Mapping | Auto-detected column roles |
| Anomalies | Any label or count discrepancies |
| Source Breakdown | Row counts per uploaded file |
