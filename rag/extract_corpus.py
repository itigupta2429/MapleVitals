"""
MapleVitals M2a - Stage 1: mechanical corpus extraction.

Reads the StatCan metadata CSV for table 13-10-0905-01 and emits one
markdown file per concept into rag/corpus/.

Each file has two zones:
  Zone 1  StatCan text, verbatim, with note ID for citation.
  Zone 2  Analyst note. Written by hand. Left as TODO here.

The routing table below is explicit on purpose. Notes are assigned to
files by human judgement, not by the CSV's own grouping, because the CSV
files cross-survey and time-break notes under the indicators they warn
about. See ROUTED_OUT.
"""

import csv
import io
import sys
from datetime import date
from pathlib import Path


TABLE = "13-10-0905-01"
TABLE_URL = "https://www150.statcan.gc.ca/t1/tbl1/en/tv.action?pid=1310090501"
TODAY = date.today().isoformat()
REPO = Path(__file__).resolve().parent.parent      # rag/ -> repo root
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "data" / "health_canada_MetaData.csv"
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else REPO / "rag" / "corpus"

if not SRC.exists():
    sys.exit(f"metadata CSV not found: {SRC}\n"
             f"expected StatCan metadata for table {TABLE} in data/")



# --- routing table -------------------------------------------------------

# Notes pulled OUT of their CSV-assigned indicators because they are
# comparability warnings, not definitions. filename -> (note_ids, title)
COMPARABILITY = {
    "break_2015_redesign":        (["4"],  "2015 CCHS redesign"),
    "break_2020_covid":           (["5"],  "COVID-19 impact on 2020 collection"),
    "break_2022_questionnaire":   (["49"], "2022 questionnaire redesign"),
    "break_2023_coverage":        (["50"], "2023 coverage change"),
    "break_2024_weighting":       (["51"], "2024 weighting calibration change"),
    "break_2024_healthcare_provider_question": (
        ["39"], "2024 revision to the regular healthcare provider question"),
    "compare_cchs_vs_ctads_smoking": (
        ["24"], "Comparing smoking rates across CCHS and CTADS"),
    "compare_cchs_vs_chms_blood_pressure": (
        ["17"], "Comparing high blood pressure across CCHS and CHMS"),
}

# note_id -> (filename it was routed to, one-line reason) for See-also pointers
ROUTED_OUT = {
    "39": ("break_2024_healthcare_provider_question",
           "2024 question revision affects comparability with earlier years"),
    "24": ("compare_cchs_vs_ctads_smoking",
           "cross-survey comparison, not a definition"),
    "17": ("compare_cchs_vs_chms_blood_pressure",
           "cross-survey comparison, not a definition"),
}

METHOD = {
    "method_cchs_sampling":           (["1", "3"], "CCHS source and sample design"),
    "method_denominator_nonresponse": (["2"],      "Non-response handling in the denominator"),
    "method_confidence_intervals":    (["41", "42"], "Confidence intervals"),
    "method_population_counts":       (["47"],     "Population projection counts"),
}

QUALITY = {
    "quality_flags_meaning":       (["44"],       "Quality flags E and F"),
    "quality_symbols_and_rounding": (["45", "46"], "Standard symbols and rounding"),
    "quality_significance_codes":  (["48"],       "Significance direction codes"),
}

# Indicator definition files, keyed by the note set the CSV assigns them.
DEF_FILES = {
    "6":                 ("def_perceived_general_health",     "Perceived health"),
    "7":                 ("def_perceived_mental_health",      "Perceived mental health"),
    "8":                 ("def_perceived_life_stress",        "Perceived life stress"),
    "9;10;11;12;13;14":  ("def_body_mass_index",              "Body mass index, adjusted self-reported"),
    "15":                ("def_arthritis",                    "Arthritis"),
    "16":                ("def_diabetes",                     "Diabetes"),
    "17;18":             ("def_high_blood_pressure",          "High blood pressure"),
    "19":                ("def_mood_disorder",                "Mood disorder"),
    "20":                ("def_anxiety_disorder",             "Anxiety disorder"),
    "21;22;23;24;25":    ("def_smoking",                      "Current smoker"),
    "26":                ("def_cannabis_use",                 "Cannabis use, past 12 months"),
    "27":                ("def_cannabis_frequency",           "Cannabis frequency of use"),
    "28":                ("def_ecigarette_ever",              "Ever used e-cigarette or vaping device"),
    "29":                ("def_ecigarette_past30days",        "Used e-cigarette or vaping device, past 30 days"),
    "30":                ("def_heavy_drinking",               "Heavy drinking"),
    "31;32":             ("def_breastfeeding_initiation",     "Breast milk feeding initiation"),
    "31;33;34":          ("def_exclusive_breastfeeding",      "Exclusive breastfeeding, at least 6 months"),
    "35":                ("def_fruit_vegetable_consumption",  "Fruit and vegetable consumption"),
    "36":                ("def_sense_of_belonging",           "Sense of belonging to local community"),
    "37":                ("def_life_satisfaction",            "Life satisfaction"),
    "38;39":             ("def_regular_healthcare_provider",  "Has a regular healthcare provider"),
    "40":                ("def_influenza_immunization",       "Influenza immunization, past 12 months"),
}

ANALYST_PLACEHOLDER = "_Not yet written._"


def load(path):
    raw = path.read_text(encoding="utf-8-sig")
    rows = list(csv.reader(io.StringIO(raw)))
    notes, indicators = {}, []
    in_notes = False
    for r in rows:
        if not r:
            continue
        if r[0] == "Note ID":
            in_notes = True
            continue
        if r[0] == "Correction ID":
            in_notes = False
        if in_notes and r[0].isdigit() and len(r) > 1:
            notes[r[0]] = r[1].strip()
        if len(r) > 6 and r[0] == "4" and r[1]:
            indicators.append((r[1], r[6]))
    return notes, indicators


def write_file(slug, title, note_ids, notes, category, members=None, see_also=None):
    lines = [
        f"# {title}",
        "",
        f"SOURCE: Statistics Canada, table {TABLE} (Canadian Community Health Survey).",
        f"NOTE IDS: {', '.join(note_ids)}",
        f"URL: {TABLE_URL}",
        f"RETRIEVED: {TODAY}",
        f"CATEGORY: {category}",
    ]
    if members:
        lines.append("TABLE MEMBERS: " + "; ".join(members))
    lines += ["", "## StatCan text (verbatim)", ""]
    for nid in note_ids:
        body = notes.get(nid)
        if not body:
            continue
        lines.append(f"**Note {nid}.** {body}")
        lines.append("")
    if see_also:
        lines += ["## See also", ""]
        for fname, reason in see_also:
            lines.append(f"- `{fname}.md` ({reason})")
        lines.append("")
    lines += ["## Analyst note (MapleVitals, not Statistics Canada)", "",
              ANALYST_PLACEHOLDER]
    OUT.joinpath(f"{slug}.md").write_text("\n".join(lines), encoding="utf-8")
    return slug


def main():
    notes, indicators = load(SRC)
    OUT.mkdir(parents=True, exist_ok=True)
    written = []

    by_noteset = {}
    for name, noteset in indicators:
        by_noteset.setdefault(noteset, []).append(name)

    for noteset, (slug, title) in DEF_FILES.items():
        ids = noteset.split(";")
        keep = [i for i in ids if i not in ROUTED_OUT]
        moved = [ROUTED_OUT[i] for i in ids if i in ROUTED_OUT]
        written.append(write_file(
            slug, title, keep, notes, "indicator definition",
            members=by_noteset.get(noteset, []),
            see_also=moved or None))

    for group, category in ((METHOD, "methodology"),
                            (QUALITY, "data quality"),
                            (COMPARABILITY, "comparability")):
        for slug, (ids, title) in group.items():
            written.append(write_file(slug, title, ids, notes, category))

    used = set()
    for noteset in DEF_FILES:
        used.update(noteset.split(";"))
    for group in (METHOD, QUALITY, COMPARABILITY):
        for ids, _ in group.values():
            used.update(ids)
    orphans = sorted(set(notes) - used, key=int)

    print(f"wrote {len(written)} files to {OUT}/")
    print(f"notes in metadata: {len(notes)}   notes used: {len(used)}")
    print(f"ORPHANED NOTES (in metadata, in no corpus file): {orphans or 'none'}")


if __name__ == "__main__":
    main()
