# app.py  –  Training Feedback Survey Analyser  (Python 3.12+)
"""
Run:  streamlit run app.py

Secrets for AI insights (local or cloud):
    OPENAI_API_KEY      – used via datapizza-ai OpenAIClient
    ANTHROPIC_API_KEY   – fallback
"""
import io
import json
import os
import re
import unicodedata
import warnings
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from rapidfuzz import fuzz
from rapidfuzz import process as rfprocess

warnings.filterwarnings("ignore")
load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# 1.  TRANSLATIONS
# ─────────────────────────────────────────────────────────────────────────────

TRANSLATIONS: dict[str, dict[str, str]] = {
    "it": {
        "app_title": "Analisi Feedback Formazione",
        "sidebar_upload": "Carica i file del survey",
        "sidebar_language": "Lingua dashboard",
        "sidebar_settings": "Impostazioni avanzate",
        "sidebar_fuzzy_threshold": "Soglia fuzzy matching",
        "sidebar_show_raw": "Mostra anteprima dati grezzi",
        "sidebar_sheet_select": "Seleziona foglio Excel",
        "sidebar_mapping_overrides": "Override mappatura colonne",
        "col_before": "Familiarità PRIMA",
        "col_after": "Familiarità DOPO",
        "col_tta": "Tempo all'applicazione",
        "col_confidence": "Autoefficacia / Sicurezza",
        "col_quality_include": "Colonne qualità (includi/escludi)",
        "upload_prompt": "Trascina qui i file CSV o XLSX",
        "upload_help": "Puoi caricare più file contemporaneamente",
        "detected_mapping": "Mappatura colonne rilevata automaticamente",
        "data_preview": "Anteprima dati grezzi",
        "phase1_title": "Fase 1 — Transizioni Sankey",
        "phase1_desc": "Analisi delle transizioni di familiarità con l'AI prima e dopo le sessioni.",
        "phase1_sankey_table": "Tabella Sankey (Before → After)",
        "phase1_dist_table": "Distribuzione livelli Before / After",
        "phase1_download_excel": "⬇ Scarica Excel Sankey",
        "phase1_chart_sankey": "Diagramma Sankey — Familiarità Before → After",
        "phase1_chart_dist": "Distribuzione Before e After per livello",
        "continue_button": "Continua con l'analisi completa →",
        "phase2_title": "Fase 2 — Analisi Completa",
        "quality_macro_title": "Qualità Formazione — Livello Macro",
        "quality_micro_title": "Qualità Formazione — Livello Micro",
        "tta_title": "Quando applicherai quanto appreso?",
        "tta_chart_title": "Distribuzione Tempo all'Applicazione",
        "insights_title": "Insights sulle Domande Aperte (AI)",
        "insights_button": "Genera Insights con AI",
        "insights_loading": "Generazione insights in corso…",
        "download_macro_csv": "⬇ Scarica CSV Macro",
        "download_micro_csv": "⬇ Scarica CSV Micro",
        "download_tta_csv": "⬇ Scarica CSV Tempo Applicazione",
        "download_full_excel": "⬇ Scarica Report Excel Completo",
        "flourish_macro_long": "Export Flourish — Macro (formato lungo)",
        "flourish_micro_long": "Export Flourish — Micro (formato lungo)",
        "warning_no_files": "Carica almeno un file CSV o XLSX per iniziare.",
        "warning_no_before": "Colonna 'Familiarità PRIMA' non rilevata. Selezionala manualmente.",
        "warning_no_after": "Colonna 'Familiarità DOPO' non rilevata. Selezionala manualmente.",
        "warning_no_quality": "Nessuna colonna di qualità rilevata (pattern Macro [Micro]).",
        "warning_reconciliation": "Riconciliazione: alcuni totali erano discordanti e sono stati corretti.",
        "warning_unexpected_labels": "Etichette non riconosciute rilevate",
        "warning_no_tta": "Colonna 'Tempo all'applicazione' non rilevata. Selezionala manualmente.",
        "anomalies_expander": "⚠️ Anomalie e Avvertenze",
        "debug_expander": "Debug: nomi normalizzati e punteggi di confidenza",
        "source_breakdown": "Dettaglio per file sorgente",
        "col_macro_tag": "Macro",
        "col_micro_tag": "Micro",
        "col_total": "Totale",
        "col_avg": "Punteggio medio (0–3)",
        "col_rating": "Valutazione",
        "col_count": "Conteggio",
        "col_before_label": "Prima",
        "col_after_label": "Dopo",
        "detected_with_confidence": "Confidenza rilevamento",
        "manual_override_hint": "Seleziona manualmente se il rilevamento automatico è incerto",
        "none_option": "(nessuna)",
        "open_text_cols_found": "Colonne testo libero rilevate",
        "ai_config_missing": "Imposta OPENAI_API_KEY o ANTHROPIC_API_KEY in `.env` oppure in `.streamlit/secrets.toml` per generare insights.",
        "insights_open_question": "Domanda aperta",
        "insights_summary": "Sintesi esecutiva",
        "insights_bullets": "Insights principali",
        "insights_sentiment": "Sentiment complessivo",
        "insights_worked": "Cosa ha funzionato",
        "insights_requests": "Richieste emerse",
        "insights_criticisms": "Criticità emerse",
        "insights_evidence": "Tracciabilità risposte",
        "insights_expectations": "Aspettative emerse",
        "source_file_col": "File sorgente",
        "rows_merged": "Righe totali dopo il merge",
        "no_valid_pairs": "Nessuna coppia Before/After valida nel range 1–4.",
        "reconciliation_ok": "Tutti i totali sono coerenti.",
        "level_label": "Livello",
    },
    "en": {
        "app_title": "Training Feedback Analysis",
        "sidebar_upload": "Upload survey files",
        "sidebar_language": "Dashboard language",
        "sidebar_settings": "Advanced settings",
        "sidebar_fuzzy_threshold": "Fuzzy matching threshold",
        "sidebar_show_raw": "Show raw data preview",
        "sidebar_sheet_select": "Select Excel sheet",
        "sidebar_mapping_overrides": "Column mapping overrides",
        "col_before": "Familiarity BEFORE",
        "col_after": "Familiarity AFTER",
        "col_tta": "Time to apply",
        "col_confidence": "Self-efficacy / Confidence",
        "col_quality_include": "Quality columns (include/exclude)",
        "upload_prompt": "Drag CSV or XLSX files here",
        "upload_help": "You can upload multiple files at once",
        "detected_mapping": "Automatically detected column mapping",
        "data_preview": "Raw data preview",
        "phase1_title": "Phase 1 — Sankey Transitions",
        "phase1_desc": "Analysis of AI familiarity transitions before and after the training sessions.",
        "phase1_sankey_table": "Sankey Table (Before → After)",
        "phase1_dist_table": "Before / After Level Distributions",
        "phase1_download_excel": "⬇ Download Sankey Excel",
        "phase1_chart_sankey": "Sankey Diagram — Familiarity Before → After",
        "phase1_chart_dist": "Before and After distributions by level",
        "continue_button": "Continue with full analysis →",
        "phase2_title": "Phase 2 — Full Analysis",
        "quality_macro_title": "Training Quality — Macro Level",
        "quality_micro_title": "Training Quality — Micro Level",
        "tta_title": "When will you apply what you learned?",
        "tta_chart_title": "Time-to-Apply Distribution",
        "insights_title": "Open Question Insights (AI)",
        "insights_button": "Generate AI Insights",
        "insights_loading": "Generating insights…",
        "download_macro_csv": "⬇ Download Macro CSV",
        "download_micro_csv": "⬇ Download Micro CSV",
        "download_tta_csv": "⬇ Download Time-to-Apply CSV",
        "download_full_excel": "⬇ Download Full Excel Report",
        "flourish_macro_long": "Flourish Export — Macro (long format)",
        "flourish_micro_long": "Flourish Export — Micro (long format)",
        "warning_no_files": "Please upload at least one CSV or XLSX file to start.",
        "warning_no_before": "'Familiarity BEFORE' column not detected. Please select it manually.",
        "warning_no_after": "'Familiarity AFTER' column not detected. Please select it manually.",
        "warning_no_quality": "No quality columns detected (pattern: Macro [Micro]).",
        "warning_reconciliation": "Reconciliation: some totals were inconsistent and have been corrected.",
        "warning_unexpected_labels": "Unrecognised labels found",
        "warning_no_tta": "'Time-to-apply' column not detected. Please select it manually.",
        "anomalies_expander": "⚠️ Anomalies and Warnings",
        "debug_expander": "Debug: normalised names and confidence scores",
        "source_breakdown": "Breakdown by source file",
        "col_macro_tag": "Macro",
        "col_micro_tag": "Micro",
        "col_total": "Total",
        "col_avg": "Avg score (0–3)",
        "col_rating": "Rating",
        "col_count": "Count",
        "col_before_label": "Before",
        "col_after_label": "After",
        "detected_with_confidence": "Detection confidence",
        "manual_override_hint": "Select manually if auto-detection is uncertain",
        "none_option": "(none)",
        "open_text_cols_found": "Free-text columns detected",
        "ai_config_missing": "Set OPENAI_API_KEY or ANTHROPIC_API_KEY in `.env` or `.streamlit/secrets.toml` to generate AI insights.",
        "insights_open_question": "Open question",
        "insights_summary": "Executive summary",
        "insights_bullets": "Key insights",
        "insights_sentiment": "Overall sentiment",
        "insights_worked": "What worked",
        "insights_requests": "Requests raised",
        "insights_criticisms": "Criticisms raised",
        "insights_evidence": "Response traceability",
        "insights_expectations": "Expectations raised",
        "source_file_col": "Source file",
        "rows_merged": "Total rows after merge",
        "no_valid_pairs": "No valid Before/After pairs found in range 1–4.",
        "reconciliation_ok": "All totals are consistent.",
        "level_label": "Level",
    },
}


def T(key: str, lang: str) -> str:
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)


def get_secret(name: str) -> str | None:
    try:
        if name in st.secrets:
            value = st.secrets[name]
            if isinstance(value, str) and value.strip():
                return value.strip()
    except Exception:
        pass

    value = os.getenv(name)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 2.  CANONICAL LABEL MAPPINGS
# ─────────────────────────────────────────────────────────────────────────────

RATING_LABEL_MAP: dict[str, str] = {
    "insufficiente": "Insufficient", "insufficient": "Insufficient",
    "sufficiente": "Sufficient",    "sufficient": "Sufficient",
    "buono": "Good",                "good": "Good",
    "eccellente": "Excellent",      "excellent": "Excellent",
    "ottimo": "Excellent",          "ottime": "Excellent",
    "molto buono": "Excellent",
    "insuff": "Insufficient",       "suff": "Sufficient",
    "buon": "Good",                 "eccel": "Excellent", "ottim": "Excellent",
    "1": "Insufficient", "2": "Sufficient", "3": "Good", "4": "Excellent",
}

CANONICAL_RATINGS: list[str] = ["Insufficient", "Sufficient", "Good", "Excellent"]

RATING_SCORES: dict[str, int] = {
    "Insufficient": 0, "Sufficient": 1, "Good": 2, "Excellent": 3,
}

RATING_DISPLAY: dict[str, dict[str, str]] = {
    "it": {"Insufficient": "Insufficiente", "Sufficient": "Sufficiente",
           "Good": "Buono", "Excellent": "Eccellente"},
    "en": {"Insufficient": "Insufficient", "Sufficient": "Sufficient",
           "Good": "Good", "Excellent": "Excellent"},
}

TTA_LABEL_MAP: dict[str, str] = {
    "subito": "Immediately",           "immediately": "Immediately",
    "entro un mese": "Within a month", "within a month": "Within a month",
    "entro 1 mese": "Within a month",
    "entro 3-6 mesi": "Within 3–6 months",
    "entro 3-6mesi": "Within 3–6 months",
    "entro 3 6 mesi": "Within 3–6 months",
    "within 3-6 months": "Within 3–6 months",
    "entro un anno": "Within a year",  "within a year": "Within a year",
    "entro 1 anno": "Within a year",
    "mai": "Never",                    "never": "Never",
    "non so ancora": "Not sure yet",   "non so": "Not sure yet",
    "not sure yet": "Not sure yet",    "non lo so": "Not sure yet",
    "1": "Immediately", "2": "Within a month",
    "3": "Within 3–6 months", "4": "Within a year", "5": "Never",
}

TTA_CANONICAL_ORDER: list[str] = [
    "Immediately", "Within a month", "Within 3–6 months",
    "Within a year", "Never", "Not sure yet",
]

TTA_DISPLAY: dict[str, dict[str, str]] = {
    "it": {
        "Immediately": "Subito", "Within a month": "Entro un mese",
        "Within 3–6 months": "Entro 3–6 mesi", "Within a year": "Entro un anno",
        "Never": "Mai", "Not sure yet": "Non so ancora",
    },
    "en": {
        "Immediately": "Immediately", "Within a month": "Within a month",
        "Within 3–6 months": "Within 3–6 months", "Within a year": "Within a year",
        "Never": "Never", "Not sure yet": "Not sure yet",
    },
}

LEVEL_LABELS: dict[int, str] = {
    1: "1 – Beginner", 2: "2 – Basic", 3: "3 – Intermediate", 4: "4 – Advanced",
}

CHART_COLORS: dict[str, str] = {
    "Insufficient": "#e74c3c", "Sufficient": "#f39c12",
    "Good": "#3498db", "Excellent": "#2ecc71",
}


def translate_label(label: str, lang: str, category: str = "rating") -> str:
    if category == "rating":
        return RATING_DISPLAY.get(lang, RATING_DISPLAY["en"]).get(label, label)
    if category == "tta":
        return TTA_DISPLAY.get(lang, TTA_DISPLAY["en"]).get(label, label)
    return label


# ─────────────────────────────────────────────────────────────────────────────
# 3.  NORMALISATION
# ─────────────────────────────────────────────────────────────────────────────

def normalize_col_name(name: str) -> str:
    nfkd = unicodedata.normalize("NFD", str(name))
    name = "".join(c for c in nfkd if unicodedata.category(c) != "Mn")
    name = name.lower()
    name = re.sub(r"[\u2013\u2014\u2012\u2212\-]+", "-", name)
    name = re.sub(r"[^\w\s\[\]\-]", " ", name)
    return re.sub(r"\s+", " ", name).strip()


def _norm_val(raw: Any) -> str:
    s = unicodedata.normalize("NFD", str(raw).strip())
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower().strip()


# ─────────────────────────────────────────────────────────────────────────────
# 4.  COLUMN DETECTION
# ─────────────────────────────────────────────────────────────────────────────

_KW: dict[str, list[str]] = {
    "before": ["prima", "before", "pre", "iniziale", "inizio", "initial", "start", "precedente"],
    "after":  ["dopo", "after", "post", "finale", "fine", "final", "conclusione", "end"],
    "familiarity": [
        "familiarita", "familiarity", "familiarizz", "conoscenza",
        "ai", "intelligenza artificiale", "artificial intelligence", "livello", "level",
    ],
    "tta": [
        "quando", "when",
        "pensi di applicare", "pensi di appl",
        "prevedi di", "pianifichi di",
        "metti in pratica", "hai intenzione di", "intendi applicare",
        "practice", "timeline",
    ],
    "confidence": [
        "sicuro", "sicura", "sicuri",
        "piu sicuro", "piu sicura",
        "ti senti", "mi sento", "senti",
        "quanto ti senti",
        "sicurezza", "confidence", "confident",
        "autoefficacia", "self-efficacy",
        "feel more", "feel confident",
    ],
    "open_text": [
        "aspettative", "expectations", "commenti", "comments", "commento",
        "miglior", "sugger", "feedback", "libero", "free",
        "note", "notes", "piaciuto", "liked", "enjoyed",
        "altro", "other", "descr", "spieg", "justif",
        "cosa hai", "cosa ti", "what did", "what would", "osservaz",
        "aspettavi", "superato", "deluso", "giustifica",
        "cosa possiamo migliorare", "commenti liberi",
    ],
}


def _kw_score(text: str, kws: list[str]) -> float:
    return min(sum(1 for k in kws if k in text) / max(len(kws) * 0.15, 1), 1.0)


def _fuzzy_best(text: str, kws: list[str]) -> float:
    if not kws:
        return 0.0
    r = rfprocess.extractOne(text, kws, scorer=fuzz.partial_ratio)
    return (r[1] / 100.0) if r else 0.0


def _non_empty_sample(df: pd.DataFrame, col: str, limit: int = 60) -> pd.Series:
    sample = df[col].dropna().astype(str).map(str.strip)
    sample = sample[sample.ne("")]
    return sample.head(limit)


def _is_open_text(df: pd.DataFrame, col: str, norm: str) -> bool:
    sample = _non_empty_sample(df, col)
    if len(sample) == 0:
        return False

    lengths = sample.str.len()
    words = sample.str.split().str.len()
    mean_len = lengths.mean()
    unique_ratio = sample.nunique() / max(len(sample), 1)
    long_share = lengths.ge(25).mean()
    numeric_ratio = pd.to_numeric(sample.str.replace(",", ".", regex=False), errors="coerce").notna().mean()
    datetime_ratio = pd.to_datetime(sample, errors="coerce").notna().mean()
    dateish_ratio = sample.str.contains(r"\d{4}[/\-]\d{1,2}[/\-]\d{1,2}|\d{1,2}:\d{2}", regex=True).mean()
    keyword_score = max(_kw_score(norm, _KW["open_text"]), _fuzzy_best(norm, _KW["open_text"]))
    looks_discrete = sample.nunique() <= max(6, len(sample) // 2) and unique_ratio <= 0.35

    if numeric_ratio >= 0.5 or datetime_ratio >= 0.8 or dateish_ratio >= 0.8:
        return False

    return not looks_discrete and (
        keyword_score >= 0.3
        or mean_len >= 35
        or long_share >= 0.35
        or (unique_ratio >= 0.85 and words.mean() >= 4)
    )


def _is_bracket(norm: str) -> tuple[bool, str, str]:
    m = re.match(r"^(.+?)\s*\[(.+?)\]\s*$", norm)
    return (True, m.group(1).strip(), m.group(2).strip()) if m else (False, "", "")


def detect_columns(df: pd.DataFrame, fuzzy_threshold: float = 0.4) -> dict[str, Any]:
    cols = [c for c in df.columns if c != "_source_file"]
    normalized = {c: normalize_col_name(c) for c in cols}
    scores: dict[str, dict[str, float]] = {c: {} for c in cols}
    open_text_cols: list[str] = []
    quality_cols: list[str] = []

    for col in cols:
        norm = normalized[col]

        # Score by name first so strong role matches survive the
        # quality/open-text filters. Some survey schemas use square brackets
        # for BEFORE/AFTER labels too, so bracketed columns are not always
        # quality questions.
        fam = max(_kw_score(norm, _KW["familiarity"]), _fuzzy_best(norm, _KW["familiarity"]))
        bef = max(_kw_score(norm, _KW["before"]),      _fuzzy_best(norm, _KW["before"]))
        aft = max(_kw_score(norm, _KW["after"]),       _fuzzy_best(norm, _KW["after"]))
        tta = max(_kw_score(norm, _KW["tta"]),         _fuzzy_best(norm, _KW["tta"]))
        cnf = max(_kw_score(norm, _KW["confidence"]),  _fuzzy_best(norm, _KW["confidence"]))
        role_scores = {
            "before": fam * bef if fam else bef * 0.3,
            "after":  fam * aft if fam else aft * 0.3,
            "tta": tta, "confidence": cnf,
        }
        scores[col] = role_scores

        best_role_score = max(role_scores.values())

        if _is_bracket(norm)[0] and best_role_score < fuzzy_threshold:
            quality_cols.append(col)
            continue

        if _is_open_text(df, col, norm) and best_role_score < fuzzy_threshold:
            open_text_cols.append(col)
            continue

    eligible = [c for c in cols if c not in open_text_cols and c not in quality_cols]

    detections: dict[str, str | None] = {}
    col_confidence: dict[str, float] = {}

    for role in ("before", "after", "tta", "confidence"):
        ranked = sorted(
            ((c, scores[c].get(role, 0.0)) for c in eligible),
            key=lambda x: x[1], reverse=True,
        )
        if ranked and ranked[0][1] >= fuzzy_threshold:
            detections[role] = ranked[0][0]
            col_confidence[role] = ranked[0][1]
        else:
            detections[role] = None
            col_confidence[role] = ranked[0][1] if ranked else 0.0

    if detections["before"] and detections["before"] == detections["after"]:
        for role in ("before", "after"):
            ranked = sorted(
                ((c, scores[c].get(role, 0.0)) for c in eligible),
                key=lambda x: x[1], reverse=True,
            )
            detections[role] = ranked[0][0] if ranked else None
            col_confidence[role] = ranked[0][1] if ranked else 0.0
        if detections["before"] == detections["after"]:
            weaker = "after" if col_confidence.get("before", 0) >= col_confidence.get("after", 0) else "before"
            detections[weaker] = None

    return {
        "before": detections.get("before"),
        "after":  detections.get("after"),
        "tta":    detections.get("tta"),
        "confidence": detections.get("confidence"),
        "confidence_col": detections.get("confidence"),
        "quality_cols": quality_cols,
        "open_text_cols": open_text_cols,
        "scores": scores,
        "normalized": normalized,
        "col_confidence": col_confidence,
    }


def extract_macro_micro(col: str) -> tuple[str, str]:
    for s in (col, normalize_col_name(col)):
        m = re.match(r"^(.+?)\s*\[(.+?)\]\s*$", s.strip())
        if m:
            return m.group(1).strip(), m.group(2).strip()
    return col, ""


# ─────────────────────────────────────────────────────────────────────────────
# 5.  LABEL MAPPING
# ─────────────────────────────────────────────────────────────────────────────

def map_rating_label(raw: Any) -> str | None:
    if pd.isna(raw):
        return None
    norm = _norm_val(raw)
    if norm in RATING_LABEL_MAP:
        return RATING_LABEL_MAP[norm]
    stripped = re.sub(r"^\d+\s*[-\u2013\u2014]\s*", "", norm).strip()
    if stripped != norm:
        if stripped in RATING_LABEL_MAP:
            return RATING_LABEL_MAP[stripped]
        r = rfprocess.extractOne(stripped, list(RATING_LABEL_MAP), scorer=fuzz.ratio)
        if r and r[1] >= 78:
            return RATING_LABEL_MAP[r[0]]
    r = rfprocess.extractOne(norm, list(RATING_LABEL_MAP), scorer=fuzz.ratio)
    return RATING_LABEL_MAP[r[0]] if r and r[1] >= 80 else None


def map_tta_label(raw: Any) -> str | None:
    if pd.isna(raw):
        return None
    norm = _norm_val(raw)
    if norm in TTA_LABEL_MAP:
        return TTA_LABEL_MAP[norm]
    stripped = re.sub(r"^\d+\s*[-\u2013\u2014]\s*", "", norm).strip()
    if stripped != norm:
        if stripped in TTA_LABEL_MAP:
            return TTA_LABEL_MAP[stripped]
        r = rfprocess.extractOne(stripped, list(TTA_LABEL_MAP), scorer=fuzz.ratio)
        if r and r[1] >= 72:
            return TTA_LABEL_MAP[r[0]]
    r = rfprocess.extractOne(norm, list(TTA_LABEL_MAP), scorer=fuzz.ratio)
    return TTA_LABEL_MAP[r[0]] if r and r[1] >= 75 else None


def safe_to_int(val: Any) -> int | None:
    if pd.isna(val):
        return None
    try:
        v = int(float(str(val).strip()))
        return v if 1 <= v <= 4 else None
    except (ValueError, TypeError):
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 6.  PHASE 1 — SANKEY & DISTRIBUTIONS
# ─────────────────────────────────────────────────────────────────────────────

def build_sankey_table(df: pd.DataFrame, before_col: str, after_col: str) -> pd.DataFrame:
    tmp = df[[before_col, after_col]].copy()
    tmp.columns = ["_b", "_a"]
    tmp["Before"] = tmp["_b"].apply(safe_to_int)
    tmp["After"]  = tmp["_a"].apply(safe_to_int)
    tmp = tmp.dropna(subset=["Before", "After"])
    tmp = tmp[tmp["Before"].between(1, 4) & tmp["After"].between(1, 4)]
    sankey = tmp.groupby(["Before", "After"]).size().reset_index(name="Value")
    return sankey[sankey["Value"] > 0].reset_index(drop=True)


def build_distributions_table(df: pd.DataFrame, before_col: str, after_col: str) -> pd.DataFrame:
    bc = df[before_col].apply(safe_to_int).value_counts()
    ac = df[after_col].apply(safe_to_int).value_counts()
    return pd.DataFrame([
        {"Level": lvl, "Label": LEVEL_LABELS[lvl],
         "Before": int(bc.get(lvl, 0)), "After": int(ac.get(lvl, 0))}
        for lvl in [1, 2, 3, 4]
    ])


# ─────────────────────────────────────────────────────────────────────────────
# 7.  PHASE 2 — QUALITY TABLES
# ─────────────────────────────────────────────────────────────────────────────

def build_micro_quality_table(
    df: pd.DataFrame, quality_cols: list[str]
) -> tuple[pd.DataFrame, list[str]]:
    anomalies: list[str] = []
    records = []
    for col in quality_cols:
        macro, micro = extract_macro_micro(col)
        counts = {r: 0 for r in CANONICAL_RATINGS}
        unexpected: list[str] = []
        for raw in df[col].dropna():
            c = map_rating_label(raw)
            if c:
                counts[c] += 1
            else:
                unexpected.append(str(raw))
        if unexpected:
            anomalies.append(f"'{col}' etichette non riconosciute: {set(unexpected)}")
        total = sum(counts.values())
        avg = sum(RATING_SCORES[r] * counts[r] for r in CANONICAL_RATINGS) / total if total else 0.0
        records.append({
            "Macro tag": macro, "Micro tag": micro, "_source_col": col,
            **counts, "Total ratings": total, "Avg score (0–3)": round(avg, 3),
        })
    return pd.DataFrame(records), anomalies


def reconcile_quality_counts(
    df: pd.DataFrame, micro_table: pd.DataFrame
) -> tuple[pd.DataFrame, list[str]]:
    warns: list[str] = []
    if "_source_col" not in micro_table.columns:
        return micro_table, warns
    corrected = []
    for _, row in micro_table.iterrows():
        col = row["_source_col"]
        if col not in df.columns:
            corrected.append(row)
            continue
        rc = {r: 0 for r in CANONICAL_RATINGS}
        for raw in df[col].dropna():
            c = map_rating_label(raw)
            if c:
                rc[c] += 1
        raw_total = sum(rc.values())
        if raw_total != row["Total ratings"] or sum(row[r] for r in CANONICAL_RATINGS) != row["Total ratings"]:
            warns.append(f"Corretto '{col}': tabella={row['Total ratings']}, ricalcolo={raw_total}")
            avg = sum(RATING_SCORES[r] * rc[r] for r in CANONICAL_RATINGS) / raw_total if raw_total else 0.0
            new_row = row.copy()
            new_row.update({**rc, "Total ratings": raw_total, "Avg score (0–3)": round(avg, 3)})
            corrected.append(new_row)
        else:
            corrected.append(row)
    return pd.DataFrame(corrected), warns


def rebuild_macro_from_micro(micro_df: pd.DataFrame) -> pd.DataFrame:
    agg = micro_df.groupby("Macro tag")[CANONICAL_RATINGS + ["Total ratings"]].sum().reset_index()
    agg["Avg score (0–3)"] = agg.apply(
        lambda r: round(sum(RATING_SCORES[x] * r[x] for x in CANONICAL_RATINGS) / r["Total ratings"], 3)
        if r["Total ratings"] else 0.0, axis=1,
    )
    return agg


# ─────────────────────────────────────────────────────────────────────────────
# 8.  FLOURISH EXPORTS
# ─────────────────────────────────────────────────────────────────────────────

def build_flourish_macro_long(macro_df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame([
        {"Macro tag": row["Macro tag"], "Rating": r, "Count": row[r]}
        for _, row in macro_df.iterrows() for r in CANONICAL_RATINGS
    ])


def build_flourish_micro_long(micro_df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame([
        {"Macro tag": row["Macro tag"], "Micro tag": row["Micro tag"], "Rating": r, "Count": row[r]}
        for _, row in micro_df.iterrows() for r in CANONICAL_RATINGS
    ])


# ─────────────────────────────────────────────────────────────────────────────
# 9.  TIME TO APPLY
# ─────────────────────────────────────────────────────────────────────────────

def build_tta_table(df: pd.DataFrame, tta_col: str) -> tuple[pd.DataFrame, list[str]]:
    counts = {k: 0 for k in TTA_CANONICAL_ORDER}
    unexpected: list[str] = []
    for raw in df[tta_col].dropna():
        c = map_tta_label(raw)
        if c:
            counts[c] = counts.get(c, 0) + 1
        else:
            unexpected.append(str(raw))
    return pd.DataFrame([{"When": k, "Count": v} for k, v in counts.items()]), unexpected


# ─────────────────────────────────────────────────────────────────────────────
# 10. AI INSIGHTS  (datapizza-ai OpenAIClient → Anthropic fallback)
# ─────────────────────────────────────────────────────────────────────────────

def _find_first_context_col(df: pd.DataFrame, keywords: list[str], excluded: set[str] | None = None) -> str | None:
    excluded = excluded or set()
    for col in df.columns:
        if col in excluded:
            continue
        norm = normalize_col_name(col)
        if any(keyword in norm for keyword in keywords):
            return col
    return None


def _build_open_question_records(df: pd.DataFrame, col: str) -> list[dict[str, str]]:
    mask = df[col].notna() & df[col].astype(str).str.strip().ne("")
    if not mask.any():
        return []

    time_col = _find_first_context_col(
        df,
        ["cronolog", "timestamp", "submitted", "data", "ora", "date", "time"],
        excluded={col},
    )
    edition_col = _find_first_context_col(df, ["edizione", "edition", "classe", "class"], excluded={col})

    records: list[dict[str, str]] = []
    for idx, row in df.loc[mask].iterrows():
        respondent_id = f"R{idx + 1:03d}"
        source = str(row.get("_source_file", "?")).strip() or "?"
        context: list[str] = [f"respondent_id={respondent_id}", f"source={source}"]

        if edition_col and pd.notna(row.get(edition_col)):
            context.append(f"edition={str(row[edition_col]).strip()}")
        if time_col and pd.notna(row.get(time_col)):
            context.append(f"time={str(row[time_col]).strip()}")

        records.append({
            "respondent_id": respondent_id,
            "source": source,
            "context": " | ".join(context),
            "text": str(row[col]).strip(),
        })
    return records


def _open_question_mode(col: str) -> str:
    norm = normalize_col_name(col)
    if "aspettative" in norm and not any(term in norm for term in ("soddisf", "superato", "deluso", "giustifica")):
        return "expectations"
    return "default"


def _insight_prompt(col: str, records: list[dict[str, str]], lang: str) -> str:
    lang_instr = "Rispondi in italiano." if lang == "it" else "Respond in English."
    bullets = "\n".join(f"  - {record['context']} | text={record['text']}" for record in records[:300])
    mode = _open_question_mode(col)

    if mode == "expectations":
        return f"""You are analysing open-text responses from a post-training feedback survey.
Question: "{col}"

Responses (context + text):
{bullets}

{lang_instr}

Return a JSON object with keys:
- "mode": "expectations"
- "summary": short executive summary focused only on the expectations expressed by the class
- "expectations": list of 4 to 8 concise expectation themes; each bullet must mention the relevant respondent_id values in parentheses

Rules:
- Do not include sentiment.
- Do not include what worked, criticisms, requests, or traceability tables.
- Focus only on the expectations that participants had before or at the start of the sessions.
- Merge similar expectations into concise themes.
- Base every claim only on the provided responses.

Output only valid JSON, no markdown fences."""

    return f"""You are analysing open-text responses from a post-training feedback survey.
Question: "{col}"

Responses (context + text):
{bullets}

{lang_instr}

Return a JSON object with keys:
- "summary": one-line executive summary
- "bullets": list of exactly 3 concise insights; each insight must mention the relevant respondent_id values in parentheses
- "sentiment": "positive" | "mixed" | "negative"
- "worked": list of up to 3 appreciated aspects
- "criticisms": list of up to 3 criticisms or frustrations
- "requests": list of up to 3 improvement requests
- "evidence": list of 3 to 6 objects with keys "respondent_id", "source", "excerpt", "takeaway", "sentiment"

Rules:
- Base every claim only on the provided responses.
- Trace who said what: use the provided respondent_id values.
- Highlight class sentiment, what worked, what was appreciated, the main requests, and the main criticisms.
- Keep excerpts short and verbatim.

Output only valid JSON, no markdown fences."""


def generate_insights(
    df: pd.DataFrame, open_text_cols: list[str], lang: str
) -> list[dict[str, Any]]:
    oai_key = get_secret("OPENAI_API_KEY")
    ant_key = get_secret("ANTHROPIC_API_KEY")
    results = []

    for col in open_text_cols:
        records = _build_open_question_records(df, col)
        if not records:
            continue

        prompt = _insight_prompt(col, records, lang)
        mode = _open_question_mode(col)
        result: dict[str, Any] = {
            "question": col,
            "mode": mode,
            "summary": None,
            "expectations": [],
            "bullets": [],
            "sentiment": None,
            "worked": [],
            "criticisms": [],
            "requests": [],
            "evidence": [],
            "error": None,
        }
        raw_text: str | None = None

        if oai_key and raw_text is None:
            try:
                from datapizza.clients.openai import OpenAIClient
                client = OpenAIClient(
                    api_key=oai_key, model="gpt-4o-mini",
                    system_prompt="You are a helpful data analyst. Always respond with valid JSON.",
                )
                raw_text = client.invoke(input=prompt, max_tokens=1024).text
            except Exception as exc:
                result["error"] = f"datapizza-ai: {exc}"

        if ant_key and raw_text is None:
            try:
                from datapizza.clients.anthropic import AnthropicClient
                raw_text = AnthropicClient(api_key=ant_key).invoke(input=prompt, max_tokens=1024).text
            except Exception as exc:
                result["error"] = f"Anthropic: {exc}"

        if raw_text:
            try:
                m = re.search(r"\{.*\}", raw_text, re.DOTALL)
                parsed = json.loads(m.group() if m else raw_text)
                result.update(
                    mode=parsed.get("mode", mode),
                    summary=parsed.get("summary"),
                    expectations=parsed.get("expectations", []),
                    bullets=parsed.get("bullets", []),
                    sentiment=parsed.get("sentiment"),
                    worked=parsed.get("worked", []),
                    criticisms=parsed.get("criticisms", []),
                    requests=parsed.get("requests", []),
                    evidence=parsed.get("evidence", []),
                )
            except Exception:
                result["summary"] = raw_text

        results.append(result)
    return results


# ─────────────────────────────────────────────────────────────────────────────
# 11. EXCEL EXPORT
# ─────────────────────────────────────────────────────────────────────────────

def _to_excel(*sheets: tuple[str, pd.DataFrame | None]) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        for name, frame in sheets:
            if frame is not None and not frame.empty:
                frame.to_excel(w, sheet_name=name[:31], index=False)
    return buf.getvalue()


def _csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# 12. DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────

def load_file(uploaded_file, sheet_name: str | None = None) -> pd.DataFrame:
    name = uploaded_file.name.lower()
    raw = uploaded_file.read()
    if name.endswith(".csv"):
        for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
            for sep in (",", ";", "\t"):
                try:
                    df = pd.read_csv(io.BytesIO(raw), encoding=enc, sep=sep)
                    if len(df.columns) > 1:
                        return df
                except Exception:
                    continue
        return pd.read_csv(io.BytesIO(raw))
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(raw), **({"sheet_name": sheet_name} if sheet_name else {}))
    raise ValueError(f"Unsupported file: {uploaded_file.name}")


def get_sheet_names(uploaded_file) -> list[str]:
    raw = uploaded_file.read()
    uploaded_file.seek(0)
    try:
        return pd.ExcelFile(io.BytesIO(raw)).sheet_names
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# 13. CHARTS
# ─────────────────────────────────────────────────────────────────────────────

def render_sankey(sankey_df: pd.DataFrame, lang: str) -> go.Figure:
    bl = [f"{T('col_before_label', lang)} L{i}" for i in range(1, 5)]
    al = [f"{T('col_after_label', lang)} L{i}"  for i in range(1, 5)]
    sources, targets, values = [], [], []
    for _, row in sankey_df.iterrows():
        sources.append(int(row["Before"]) - 1)
        targets.append(int(row["After"])  - 1 + 4)
        values.append(int(row["Value"]))
    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(pad=20, thickness=24, line=dict(color="white", width=0.5),
                  label=bl + al, color=["#3498db"] * 4 + ["#2ecc71"] * 4),
        link=dict(source=sources, target=targets, value=values,
                  color=["rgba(52,152,219,0.3)"] * len(sources)),
    ))
    fig.update_layout(title_text=T("phase1_chart_sankey", lang), font_size=13,
                      height=520, margin=dict(t=60, b=20, l=20, r=20))
    return fig


def render_distributions(dist_df: pd.DataFrame, lang: str) -> go.Figure:
    fig = go.Figure([
        go.Bar(name=T("col_before_label", lang), x=dist_df["Label"], y=dist_df["Before"], marker_color="#3498db"),
        go.Bar(name=T("col_after_label",  lang), x=dist_df["Label"], y=dist_df["After"],  marker_color="#2ecc71"),
    ])
    fig.update_layout(barmode="group", title=T("phase1_chart_dist", lang),
                      xaxis_title=T("level_label", lang), yaxis_title=T("col_count", lang), height=400)
    return fig


def render_macro_chart(macro_df: pd.DataFrame, lang: str) -> go.Figure:
    fig = go.Figure([
        go.Bar(name=translate_label(r, lang), x=macro_df["Macro tag"], y=macro_df[r], marker_color=CHART_COLORS[r])
        for r in CANONICAL_RATINGS
    ])
    fig.update_layout(barmode="stack", title=T("quality_macro_title", lang),
                      xaxis_title=T("col_macro_tag", lang), yaxis_title=T("col_count", lang),
                      height=460, legend_title_text=T("col_rating", lang))
    return fig


def render_micro_chart(micro_df: pd.DataFrame, lang: str) -> go.Figure:
    plot_df = micro_df.drop(columns=["_source_col"], errors="ignore").sort_values("Avg score (0–3)")
    labels = [f"{r['Macro tag']} / {r['Micro tag']}" for _, r in plot_df.iterrows()]
    fig = go.Figure(go.Bar(
        x=plot_df["Avg score (0–3)"], y=labels, orientation="h",
        marker_color="#3498db", text=[f"{v:.2f}" for v in plot_df["Avg score (0–3)"]],
        textposition="outside",
    ))
    fig.update_layout(title=T("quality_micro_title", lang), xaxis_title=T("col_avg", lang),
                      xaxis_range=[0, 3.2], height=max(350, len(labels) * 38 + 100), margin=dict(l=200))
    return fig


def render_tta_chart(tta_df: pd.DataFrame, lang: str) -> go.Figure:
    labels = [translate_label(w, lang, "tta") for w in tta_df["When"]]
    fig = go.Figure(go.Pie(
        labels=labels, values=tta_df["Count"], hole=0.42,
        marker_colors=["#2ecc71", "#3498db", "#f39c12", "#e74c3c", "#95a5a6", "#bdc3c7"],
        textinfo="label+percent", hoverinfo="label+value+percent",
    ))
    fig.update_layout(title=T("tta_chart_title", lang), height=420)
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# 14. DISPLAY HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _rename_quality(df: pd.DataFrame, lang: str) -> pd.DataFrame:
    return df.rename(columns={
        "Macro tag": T("col_macro_tag", lang), "Micro tag": T("col_micro_tag", lang),
        "Insufficient": translate_label("Insufficient", lang),
        "Sufficient":   translate_label("Sufficient",   lang),
        "Good":         translate_label("Good",         lang),
        "Excellent":    translate_label("Excellent",    lang),
        "Total ratings": T("col_total", lang),
        "Avg score (0–3)": T("col_avg", lang),
    })


# ─────────────────────────────────────────────────────────────────────────────
# 15. MAIN APP
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(page_title="Training Feedback Analysis", page_icon="📊", layout="wide")

    # ── Sidebar ───────────────────────────────────────────────────────────
    with st.sidebar:
        st.title("📊 Controls")
        lang: str = st.selectbox(
            "🌐 " + T("sidebar_language", "en"), ["it", "en"],
            format_func=lambda x: "🇮🇹 Italiano" if x == "it" else "🇬🇧 English",
            key="lang",
        )
        st.markdown("---")
        st.subheader(T("sidebar_upload", lang))
        uploaded_files = st.file_uploader(
            T("upload_prompt", lang), type=["csv", "xlsx", "xls"],
            accept_multiple_files=True, help=T("upload_help", lang),
            label_visibility="collapsed",
        )
        sheet_selections: dict[str, str] = {}
        if uploaded_files:
            for uf in uploaded_files:
                if uf.name.lower().endswith((".xlsx", ".xls")):
                    sheets = get_sheet_names(uf)
                    if len(sheets) > 1:
                        sheet_selections[uf.name] = st.selectbox(
                            f"{T('sidebar_sheet_select', lang)}: {uf.name}",
                            sheets, key=f"sheet_{uf.name}",
                        )
        st.markdown("---")
        with st.expander(T("sidebar_settings", lang)):
            fuzzy_threshold: float = st.slider(T("sidebar_fuzzy_threshold", lang), 0.1, 1.0, 0.40, 0.05)
            show_raw: bool = st.checkbox(T("sidebar_show_raw", lang), value=False)

    st.title(f"📊 {T('app_title', lang)}")

    if not uploaded_files:
        st.info(T("warning_no_files", lang))
        return

    # ── Load & merge ──────────────────────────────────────────────────────
    dfs: list[pd.DataFrame] = []
    for uf in uploaded_files:
        try:
            uf.seek(0)
            frame = load_file(uf, sheet_name=sheet_selections.get(uf.name))
            frame["_source_file"] = uf.name
            dfs.append(frame)
        except Exception as exc:
            st.error(f"`{uf.name}`: {exc}")

    if not dfs:
        st.error("No files could be loaded.")
        return

    merged = pd.concat(dfs, ignore_index=True)
    st.success(f"**{T('rows_merged', lang)}: {len(merged):,}** ({len(dfs)} file(s))")
    if show_raw:
        with st.expander(T("data_preview", lang)):
            st.dataframe(merged.head(100), use_container_width=True)

    # ── Column detection ──────────────────────────────────────────────────
    det = detect_columns(merged, fuzzy_threshold)
    all_cols = [c for c in merged.columns if c != "_source_file"]
    none_opt = T("none_option", lang)
    opts = [none_opt] + all_cols

    def _idx(col: str | None) -> int:
        return all_cols.index(col) + 1 if col and col in all_cols else 0

    with st.sidebar:
        st.markdown("---")
        with st.expander(T("sidebar_mapping_overrides", lang), expanded=True):
            hint = T("manual_override_hint", lang)

            def _sel(key_t: str, det_key: str, confidence_key: str, key: str) -> str | None:
                conf = det["col_confidence"].get(confidence_key, 0)
                v = st.selectbox(f"{T(key_t, lang)}  ·  {conf:.0%}", opts,
                                 index=_idx(det.get(det_key)), help=hint, key=key)
                return None if v == none_opt else v

            before_col = _sel("col_before", "before", "before", "ov_before")
            after_col  = _sel("col_after",  "after",  "after",  "ov_after")
            tta_col    = _sel("col_tta",    "tta",    "tta",    "ov_tta")
            conf_col   = _sel("col_confidence", "confidence_col", "confidence", "ov_conf")

            quality_cols: list[str] = st.multiselect(
                T("col_quality_include", lang),
                options=det["quality_cols"], default=det["quality_cols"], key="ov_quality",
            )

    open_text_cols: list[str] = det["open_text_cols"]

    with st.expander(T("detected_mapping", lang), expanded=True):
        st.table(pd.DataFrame({
            "Role": [T("col_before", lang), T("col_after", lang), T("col_tta", lang), T("col_confidence", lang)],
            "Detected column": [before_col, after_col, tta_col, conf_col],
            "Confidence": [f"{det['col_confidence'].get(r, 0):.0%}" for r in ("before", "after", "tta", "confidence")],
        }))
        if quality_cols:
            st.write(f"**Quality ({len(quality_cols)}):** " + ", ".join(f"`{c}`" for c in quality_cols))
        if open_text_cols:
            st.write(f"**{T('open_text_cols_found', lang)} ({len(open_text_cols)}):** " + ", ".join(f"`{c}`" for c in open_text_cols))

    with st.expander(T("debug_expander", lang)):
        st.dataframe(pd.DataFrame([{
            "Column": c, "Normalised": n,
            **{f"Score {k}": f"{det['scores'].get(c, {}).get(k, 0):.3f}" for k in ("before", "after", "tta", "confidence")},
        } for c, n in det["normalized"].items()]), use_container_width=True)

    # ═══════════════════════════════ PHASE 1 ═════════════════════════════════
    st.markdown("---")
    st.header(f"📈 {T('phase1_title', lang)}")
    st.write(T("phase1_desc", lang))

    if not before_col: st.warning(T("warning_no_before", lang))
    if not after_col:  st.warning(T("warning_no_after",  lang))

    sankey_df = dist_df = None

    if before_col and after_col:
        sankey_df = build_sankey_table(merged, before_col, after_col)
        dist_df   = build_distributions_table(merged, before_col, after_col)

        if sankey_df.empty:
            st.warning(T("no_valid_pairs", lang))
        else:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader(T("phase1_sankey_table", lang))
                st.dataframe(sankey_df, use_container_width=True)
            with c2:
                st.subheader(T("phase1_dist_table", lang))
                st.dataframe(dist_df, use_container_width=True)

            st.plotly_chart(render_sankey(sankey_df, lang), use_container_width=True)
            st.plotly_chart(render_distributions(dist_df, lang), use_container_width=True)

            st.download_button(T("phase1_download_excel", lang),
                               data=_to_excel(("Sankey", sankey_df), ("Distributions", dist_df)),
                               file_name="sankey_phase1.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.markdown("---")
    if "show_phase2" not in st.session_state:
        st.session_state["show_phase2"] = False
    if st.button(T("continue_button", lang), type="primary"):
        st.session_state["show_phase2"] = True
    if not st.session_state["show_phase2"]:
        return

    # ═══════════════════════════════ PHASE 2 ═════════════════════════════════
    st.markdown("---")
    st.header(f"🔬 {T('phase2_title', lang)}")
    all_anomalies: list[str] = []
    macro_df = micro_df = pd.DataFrame()

    if quality_cols:
        raw_micro, micro_anom = build_micro_quality_table(merged, quality_cols)
        all_anomalies.extend(micro_anom)

        micro_df, recon_warns = reconcile_quality_counts(merged, raw_micro)
        if recon_warns:
            st.warning(T("warning_reconciliation", lang))
            for w in recon_warns: st.warning(f"  • {w}")
            all_anomalies.extend(recon_warns)
        else:
            st.success(T("reconciliation_ok", lang))

        macro_df = rebuild_macro_from_micro(micro_df)

        for _, row in macro_df.iterrows():
            if sum(row[r] for r in CANONICAL_RATINGS) != row["Total ratings"]:
                all_anomalies.append(f"Macro '{row['Macro tag']}': somma celle ≠ Totale")
            if not 0.0 <= row["Avg score (0–3)"] <= 3.0:
                all_anomalies.append(f"Macro '{row['Macro tag']}': media fuori range [0,3]")

        st.subheader(T("quality_macro_title", lang))
        st.dataframe(_rename_quality(macro_df, lang), use_container_width=True)
        st.plotly_chart(render_macro_chart(macro_df, lang), use_container_width=True)

        st.subheader(T("quality_micro_title", lang))
        display_micro = micro_df.drop(columns=["_source_col"], errors="ignore")
        st.dataframe(_rename_quality(display_micro, lang), use_container_width=True)
        st.plotly_chart(render_micro_chart(micro_df, lang), use_container_width=True)

        c1, c2 = st.columns(2)
        with c1:
            st.download_button(T("download_macro_csv", lang), _csv(macro_df), "macro_quality.csv", "text/csv")
        with c2:
            st.download_button(T("download_micro_csv", lang), _csv(display_micro), "micro_quality.csv", "text/csv")

        with st.expander(T("flourish_macro_long", lang)):
            fl = build_flourish_macro_long(macro_df)
            st.dataframe(fl, use_container_width=True)
            st.download_button("CSV", _csv(fl), "flourish_macro_long.csv", "text/csv")

        with st.expander(T("flourish_micro_long", lang)):
            fl = build_flourish_micro_long(display_micro)
            st.dataframe(fl, use_container_width=True)
            st.download_button("CSV", _csv(fl), "flourish_micro_long.csv", "text/csv")

        with st.expander(T("source_breakdown", lang)):
            if "_source_file" in merged.columns:
                src = merged["_source_file"].value_counts().reset_index()
                src.columns = [T("source_file_col", lang), T("col_count", lang)]
                st.dataframe(src, use_container_width=True)
    else:
        st.warning(T("warning_no_quality", lang))

    # ── Time to Apply ─────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader(T("tta_title", lang))
    tta_df = pd.DataFrame()

    if tta_col:
        tta_df, unexpected = build_tta_table(merged, tta_col)
        if unexpected:
            msg = f"{T('warning_unexpected_labels', lang)}: {set(unexpected)}"
            st.warning(msg); all_anomalies.append(msg)
        display_tta = tta_df.copy()
        display_tta["When"] = display_tta["When"].apply(lambda w: translate_label(w, lang, "tta"))
        st.dataframe(display_tta, use_container_width=True)
        st.plotly_chart(render_tta_chart(tta_df, lang), use_container_width=True)
        st.download_button(T("download_tta_csv", lang), _csv(display_tta), "time_to_apply.csv", "text/csv")
    else:
        st.warning(T("warning_no_tta", lang))

    if all_anomalies:
        with st.expander(T("anomalies_expander", lang)):
            for a in all_anomalies: st.warning(a)

    # ── AI Insights ───────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader(T("insights_title", lang))
    has_api = bool(get_secret("OPENAI_API_KEY") or get_secret("ANTHROPIC_API_KEY"))

    if not has_api:
        st.info(T("ai_config_missing", lang))
    elif not open_text_cols:
        st.info("Nessuna colonna testo libero." if lang == "it" else "No free-text columns detected.")
    else:
        if st.button(T("insights_button", lang), type="secondary"):
            with st.spinner(T("insights_loading", lang)):
                insights = generate_insights(merged, open_text_cols, lang)
            for ins in insights:
                with st.expander(f"💬 {T('insights_open_question', lang)}: {ins['question']}"):
                    if ins.get("error"):   st.error(ins["error"])
                    if ins.get("summary"): st.markdown(f"**{T('insights_summary', lang)}:** {ins['summary']}")
                    if ins.get("mode") == "expectations":
                        if ins.get("expectations"):
                            st.markdown(f"**{T('insights_expectations', lang)}:**")
                            for item in ins["expectations"]:
                                st.markdown(f"- {item}")
                        continue
                    if ins.get("sentiment"):
                        emoji = {"positive": "😊", "mixed": "😐", "negative": "😟"}.get(ins["sentiment"], "❓")
                        st.markdown(f"**{T('insights_sentiment', lang)}:** {emoji} {ins['sentiment']}")
                    if ins.get("bullets"):
                        st.markdown(f"**{T('insights_bullets', lang)}:**")
                        for b in ins["bullets"]: st.markdown(f"- {b}")
                    if ins.get("worked"):
                        st.markdown(f"**{T('insights_worked', lang)}:**")
                        for item in ins["worked"]:
                            st.markdown(f"- {item}")
                    if ins.get("criticisms"):
                        st.markdown(f"**{T('insights_criticisms', lang)}:**")
                        for item in ins["criticisms"]:
                            st.markdown(f"- {item}")
                    if ins.get("requests"):
                        st.markdown(f"**{T('insights_requests', lang)}:**")
                        for item in ins["requests"]:
                            st.markdown(f"- {item}")
                    if ins.get("evidence"):
                        st.markdown(f"**{T('insights_evidence', lang)}:**")
                        evidence_df = pd.DataFrame(ins["evidence"])
                        if not evidence_df.empty:
                            st.dataframe(evidence_df, use_container_width=True)

    # ── Full Excel export ─────────────────────────────────────────────────
    st.markdown("---")
    src_rec = None
    if "_source_file" in merged.columns:
        src_rec = merged["_source_file"].value_counts().reset_index()
        src_rec.columns = ["Source file", "Rows"]

    full_excel = _to_excel(
        ("Sankey",          sankey_df),
        ("Distributions",   dist_df),
        ("Macro Quality",   macro_df if not macro_df.empty else None),
        ("Micro Quality",   micro_df.drop(columns=["_source_col"], errors="ignore") if not micro_df.empty else None),
        ("Time to Apply",   tta_df if not tta_df.empty else None),
        ("Detected Mapping", pd.DataFrame({
            "Role": [T("col_before", lang), T("col_after", lang), T("col_tta", lang), T("col_confidence", lang)],
            "Column": [before_col, after_col, tta_col, conf_col],
        })),
        ("Anomalies",       pd.DataFrame({"Anomaly": all_anomalies or ["None"]})),
        ("Source Breakdown", src_rec),
    )
    st.download_button(T("download_full_excel", lang), full_excel, "training_feedback_report.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")


if __name__ == "__main__":
    main()
