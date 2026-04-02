# Training Feedback Survey Analyser

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Pandas](https://img.shields.io/badge/pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Plotly](https://img.shields.io/badge/Plotly-239120?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com/python/)
[![RapidFuzz](https://img.shields.io/badge/RapidFuzz-5A67D8?style=for-the-badge)](https://github.com/maxbachmann/RapidFuzz)
[![OpenPyXL](https://img.shields.io/badge/OpenPyXL-217346?style=for-the-badge&logo=microsoft-excel&logoColor=white)](https://openpyxl.readthedocs.io/)
![CSV · XLSX](https://img.shields.io/badge/input-CSV%20%7C%20XLSX-00A4EF?style=for-the-badge)
![AI insights](https://img.shields.io/badge/AI-datapizza--ai%20%C2%B7%20OpenAI%20%C2%B7%20Anthropic-6366F1?style=for-the-badge)

Production-ready Streamlit app for analysing post-training feedback surveys exported from Microsoft Forms or similar tools.

---

## Quick start

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) set an API key for AI insights
export OPENAI_API_KEY="sk-..."          # or
export ANTHROPIC_API_KEY="sk-ant-..."   # or
export DATAPIZZA_API_KEY="dp-..."

# 4. Run
streamlit run app.py
```

Open http://localhost:8501 in your browser.

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

Set **one** of these environment variables before running:

```
DATAPIZZA_API_KEY   # preferred (datapizza-ai package)
OPENAI_API_KEY      # fallback (gpt-4o-mini)
ANTHROPIC_API_KEY   # fallback (claude-haiku)
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
