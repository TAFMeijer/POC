"""
Health Facility Matching Script – Guinea-Bissau
================================================
Matches 491 facility records (Region, AS/district, CS/name) from Sheet 1
against 288 official MFL entries from Sheet 2 using Google Gemini 2.5 Flash.

Usage:
    export GOOGLE_API_KEY="your_key_here"
    python3 match_facilities.py           # full run (491 rows)
    python3 match_facilities.py --test    # test: first 20 rows only, prints to console

Output:
    GNB_MFL_matched.xlsx  — original data + match columns
    matching_progress.jsonl — per-row cache; delete to force full re-run
"""

import os
import json
import re
import time
import argparse
import warnings
import traceback
import unicodedata
import pandas as pd

# Suppress noisy SSL/Python-version warnings from google-auth and urllib3
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
try:
    import urllib3
    urllib3.disable_warnings()
except Exception:
    pass

from google import genai
from google.genai import types

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
EXCEL_FILE    = "GNB MFL.xlsx"
OUTPUT_FILE   = "GNB_MFL_matched.xlsx"
PROGRESS_FILE = "matching_progress.jsonl"
MODEL         = "gemini-2.5-flash-lite"
BATCH_SIZE    = 20          # records per API call (~25 calls total for 491 rows)
MAX_RETRIES   = 4
RETRY_DELAY   = 5           # seconds base delay (doubles on each retry)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def ts() -> str:
    """Current time as [HH:MM:SS] prefix for prints."""
    from datetime import datetime
    return datetime.now().strftime("[%H:%M:%S]")


def strip_accents(text: str) -> str:
    """Normalise accented characters to ASCII for display comparison."""
    if not isinstance(text, str):
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


def parse_mfl_entry(raw: str) -> dict:
    """
    Parse an MFL string like:
        'Bafata/Bafata:-Bafata_Centro Materno Infantil de Bafata'
    into structured fields.
    """
    region, district, sector, name = "", "", "", raw
    if "/" in raw:
        region, rest = raw.split("/", 1)
        if ":-" in rest:
            district, rest2 = rest.split(":-", 1)
            if "_" in rest2:
                sector, name = rest2.split("_", 1)
            else:
                name = rest2
        else:
            district = rest
    return {
        "raw": raw,
        "region": region.strip(),
        "district": district.strip(),
        "sector": sector.strip(),
        "name": name.strip(),
    }


def load_data() -> tuple[pd.DataFrame, list[dict], str, set]:
    """Load both sheets and return (sheet1_df, mfl_list, mfl_context_string, mfl_raw_set)."""
    wb = pd.ExcelFile(EXCEL_FILE)
    df = pd.read_excel(wb, sheet_name=0, header=0)
    df.columns = ["Region", "AS", "CS"]
    df = df.dropna(how="all").reset_index(drop=True)

    mfl_raw_col = pd.read_excel(wb, sheet_name=1, header=0).iloc[:, 0].dropna().tolist()
    mfl_list = [parse_mfl_entry(str(m)) for m in mfl_raw_col if str(m) != "MFL"]
    mfl_raw_set = {m["raw"] for m in mfl_list}  # for hallucination validation

    # Build a numbered reference list for the prompt
    lines = []
    for i, m in enumerate(mfl_list, 1):
        lines.append(f"{i:3d}. [{m['region']} / {m['district']}] {m['name']}  (raw: {m['raw']})")
    mfl_context = "\n".join(lines)

    return df, mfl_list, mfl_context, mfl_raw_set


def load_progress() -> dict[int, dict]:
    """Load cached results from previous run. Keys are 0-based row indices."""
    cache = {}
    if not os.path.exists(PROGRESS_FILE):
        return cache
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                cache[rec["row_index"]] = rec
            except json.JSONDecodeError:
                pass
    return cache


def save_progress(results: list[dict]) -> None:
    """Append a list of result dicts to the progress file."""
    with open(PROGRESS_FILE, "a", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# ─────────────────────────────────────────────
# PROMPT BUILDER
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a health facility data expert for Guinea-Bissau.
Your task is to match input facility records to the official Master Facility List (MFL).

Rules:
- Abbreviations must be expanded: CMI = Centro Materno Infantil, CS = Centro de Saúde, HR = Hospital Regional, HN = Hospital Nacional, PS = Posto de Saúde.
- Ignore accents for comparison (Bafatá = Bafata).
- Use Region and District to filter candidates before comparing names.
- Return ONLY a JSON array — no markdown, no explanation, no backticks.

For each input record, output one JSON object with these fields:
  "row_index"      : the integer row index provided in the input
  "mfl_raw"        : the exact 'raw' string from the MFL list that best matches, or null if no match
  "mfl_name"       : the official facility name from the MFL, or null
  "confidence"     : "HIGH", "MEDIUM", "LOW", or "NO_MATCH"
  "notes"          : brief explanation (1 sentence max) of why you chose this match or why there is no match
"""

def build_user_prompt(batch: list[dict], mfl_context: str) -> str:
    records_json = json.dumps(
        [{"row_index": r["row_index"], "Region": r["Region"], "AS": r["AS"], "CS": r["CS"]}
         for r in batch],
        ensure_ascii=False, indent=2
    )
    return f"""
## Input Records to Match
{records_json}

## Official MFL Reference List (288 entries)
Format: [Region / District] Official Name  (raw: full_mfl_string)

{mfl_context}

Return ONLY a JSON array with one object per input record.
"""


# ─────────────────────────────────────────────
# HALLUCINATION VALIDATION
# ─────────────────────────────────────────────

def validate_results(results: list[dict], mfl_raw_set: set) -> list[dict]:
    """
    Check every result's mfl_raw against the known MFL set.
    Any value not found verbatim is nulled out and flagged as HALLUCINATED
    so it can be filtered in the output Excel.
    """
    hallucinated = 0
    for r in results:
        raw = r.get("mfl_raw")
        if raw and raw not in mfl_raw_set:
            r["mfl_raw"]    = None
            r["mfl_name"]   = None
            r["confidence"] = "HALLUCINATED"
            r["notes"]      = f"Model returned '{raw}' which is not in the MFL list — discarded."
            hallucinated += 1
    if hallucinated:
        print(f"  {ts()} ⚠ {hallucinated} hallucinated MFL entries discarded", flush=True)
    return results


# ─────────────────────────────────────────────
# API CALL WITH RETRY
# ─────────────────────────────────────────────

def call_gemini(client: genai.Client, prompt: str, batch_num: int) -> list[dict]:
    """Call Gemini and parse the JSON response. Retries on failure."""
    delay = RETRY_DELAY
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"  {ts()} → Sending request to Gemini (attempt {attempt})...", flush=True)
            t0 = time.time()
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.0,
                    response_mime_type="application/json",
                ),
            )
            elapsed = time.time() - t0
            print(f"  {ts()} ← Response received in {elapsed:.1f}s ({len(response.text)} chars)", flush=True)
            text = response.text.strip()

            # Strip markdown code fences if the model ignored the instruction
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)

            parsed = json.loads(text)
            if isinstance(parsed, list):
                return parsed
            # If model returned a dict (single record), wrap it
            return [parsed]

        except json.JSONDecodeError as e:
            print(f"  {ts()} ⚠ Batch {batch_num} attempt {attempt}: JSON parse error – {e}", flush=True)
            print(f"  Raw response: {text[:300]}", flush=True)
        except Exception as e:
            print(f"  {ts()} ⚠ Batch {batch_num} attempt {attempt}: {type(e).__name__} – {e}", flush=True)
            traceback.print_exc()

        if attempt < MAX_RETRIES:
            print(f"  {ts()} Retrying in {delay}s...", flush=True)
            time.sleep(delay)
            delay *= 2

    print(f"  {ts()} ✗ Batch {batch_num} failed after {MAX_RETRIES} attempts.", flush=True)
    return []


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def print_test_results(batch: list[dict], results: list[dict]) -> None:
    """Pretty-print test batch results to the console."""
    results_by_idx = {r.get("row_index"): r for r in results if isinstance(r, dict)}
    CONF_ICONS = {"HIGH": "✅", "MEDIUM": "🟡", "LOW": "🔴", "NO_MATCH": "❌"}

    print(f"\n{'─'*100}")
    print(f"  {'#':>3}  {'CONF':7}  {'REGION':10}  {'DISTRICT':15}  {'INPUT NAME':25}  {'MFL MATCH'}")
    print(f"{'─'*100}")

    for record in batch:
        ri  = record["row_index"]
        res = results_by_idx.get(ri, {})
        conf    = res.get("confidence", "NO_MATCH")
        icon    = CONF_ICONS.get(conf, "?")
        mfl_name = res.get("mfl_name") or "—"
        notes    = res.get("notes", "")
        print(f"  {ri:>3}  {icon} {conf:6}  {record['Region']:10}  {record['AS']:15}  {record['CS']:25}  {mfl_name}")
        if notes:
            print(f"           {'':39} ↳ {notes}")

    print(f"{'─'*100}")
    conf_counts = {}
    for r in results:
        c = r.get("confidence", "?")
        conf_counts[c] = conf_counts.get(c, 0) + 1
    print("Summary:", "  ".join(f"{CONF_ICONS.get(k,'?')} {k}: {v}" for k, v in conf_counts.items()))
    print()


def main():
    parser = argparse.ArgumentParser(description="Match health facilities to the MFL using Gemini.")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run one batch of 20 rows only and print results to console (no files written).",
    )
    args = parser.parse_args()

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        api_key = input("Enter your Google API key: ").strip()

    client = genai.Client(api_key=api_key)

    print(f"{ts()} 📂 Loading data...", flush=True)
    df, mfl_list, mfl_context, mfl_raw_set = load_data()
    total = len(df)
    print(f"{ts()}    Sheet 1: {total} records", flush=True)
    print(f"{ts()}    MFL:     {len(mfl_list)} entries ({len(mfl_raw_set)} unique raw strings)", flush=True)

    # ─── TEST MODE: single batch, console output only ───
    if args.test:
        print(f"\n{ts()} 🧪 TEST MODE — running 1 batch of {BATCH_SIZE} rows (no files written)\n", flush=True)
        batch = []
        for idx, row in df.head(BATCH_SIZE).iterrows():
            batch.append({
                "row_index": idx,
                "Region": str(row["Region"]) if pd.notna(row["Region"]) else "",
                "AS":     str(row["AS"])     if pd.notna(row["AS"])     else "",
                "CS":     str(row["CS"])     if pd.notna(row["CS"])     else "",
            })
        prompt = build_user_prompt(batch, mfl_context)
        results = call_gemini(client, prompt, batch_num=1)
        results = validate_results(results, mfl_raw_set)
        print_test_results(batch, results)
        print(f"{ts()} ✅ Test complete. Run without --test to process all rows and save to Excel.", flush=True)
        return

    # ─── FULL RUN ───
    print(f"{ts()} 💾 Loading progress cache...", flush=True)
    cache = load_progress()
    print(f"{ts()}    Already processed: {len(cache)} rows", flush=True)

    # Build list of rows still needing processing
    pending = []
    for idx, row in df.iterrows():
        if idx not in cache:
            pending.append({
                "row_index": idx,
                "Region": str(row["Region"]) if pd.notna(row["Region"]) else "",
                "AS":     str(row["AS"])     if pd.notna(row["AS"])     else "",
                "CS":     str(row["CS"])     if pd.notna(row["CS"])     else "",
            })

    n_pending = len(pending)
    n_batches = (n_pending + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"\n{ts()} 🔄 Processing {n_pending} pending rows in {n_batches} batch(es) of {BATCH_SIZE}...", flush=True)

    for batch_idx in range(n_batches):
        batch = pending[batch_idx * BATCH_SIZE : (batch_idx + 1) * BATCH_SIZE]
        batch_num = batch_idx + 1
        row_nums = [r["row_index"] for r in batch]
        print(f"\n{ts()}   Batch {batch_num}/{n_batches}  (rows {row_nums[0]}–{row_nums[-1]})...", flush=True)

        prompt = build_user_prompt(batch, mfl_context)
        results = call_gemini(client, prompt, batch_num)
        results = validate_results(results, mfl_raw_set)

        # Map results back by row_index
        results_by_idx = {r.get("row_index"): r for r in results if isinstance(r, dict)}

        batch_to_save = []
        for record in batch:
            ri = record["row_index"]
            matched = results_by_idx.get(ri)
            if matched:
                entry = {
                    "row_index":  ri,
                    "Region":     record["Region"],
                    "AS":         record["AS"],
                    "CS":         record["CS"],
                    "mfl_raw":    matched.get("mfl_raw"),
                    "mfl_name":   matched.get("mfl_name"),
                    "confidence": matched.get("confidence", "LOW"),
                    "notes":      matched.get("notes", ""),
                }
            else:
                entry = {
                    "row_index":  ri,
                    "Region":     record["Region"],
                    "AS":         record["AS"],
                    "CS":         record["CS"],
                    "mfl_raw":    None,
                    "mfl_name":   None,
                    "confidence": "NO_MATCH",
                    "notes":      "Batch failed or row missing from response",
                }
            cache[ri] = entry
            batch_to_save.append(entry)

        save_progress(batch_to_save)
        print(f"{ts()}   ✓ Saved {len(batch_to_save)} results", flush=True)

        # Small pause between batches to be polite to the API
        if batch_idx < n_batches - 1:
            time.sleep(1)

    # ─── Build output DataFrame ───
    print("\n📊 Building output Excel file...")
    output_rows = []
    for idx in range(total):
        orig = df.iloc[idx]
        res  = cache.get(idx, {})
        output_rows.append({
            "Region":            orig.get("Region", ""),
            "AS":               orig.get("AS", ""),
            "CS":               orig.get("CS", ""),
            "MFL_Match_Raw":    res.get("mfl_raw", ""),
            "MFL_Official_Name": res.get("mfl_name", ""),
            "Confidence":       res.get("confidence", ""),
            "Notes":            res.get("notes", ""),
        })

    out_df = pd.DataFrame(output_rows)
    out_df.to_excel(OUTPUT_FILE, index=False)

    # ─── Summary ───
    conf_counts = out_df["Confidence"].value_counts().to_dict()
    print(f"\n{ts()} ✅ Done! Results saved to '{OUTPUT_FILE}'", flush=True)
    print(f"{ts()} 📈 Confidence summary:", flush=True)
    for level in ["HIGH", "MEDIUM", "LOW", "NO_MATCH", ""]:
        count = conf_counts.get(level, 0)
        if count:
            label = level if level else "Unknown"
            print(f"   {label:10s}: {count:4d} rows")
    print(f"\n{ts()}    Total: {total} rows processed", flush=True)
    print(f"{ts()} 💡 Tip: To force a full re-run, delete '{PROGRESS_FILE}'", flush=True)


if __name__ == "__main__":
    main()
