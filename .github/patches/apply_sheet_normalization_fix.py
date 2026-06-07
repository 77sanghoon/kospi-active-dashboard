from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

reporting_path = ROOT / "kospi_active" / "reporting.py"
reporting = reporting_path.read_text(encoding="utf-8")

if "def _normalize_stock_code" not in reporting:
    reporting = reporting.replace(
        "def normalize_holding_row(row: dict) -> dict:\n",
        "def _normalize_stock_code(value: object) -> str:\n"
        "    text = str(value or \"\").strip()\n"
        "    if text.endswith(\".0\") and text[:-2].isdigit():\n"
        "        text = text[:-2]\n"
        "    if text.isdigit() and 0 < len(text) < 6:\n"
        "        return text.zfill(6)\n"
        "    return text\n\n\n"
        "def normalize_holding_row(row: dict) -> dict:\n",
    )

reporting = reporting.replace(
    '        "stock_code": str(row.get("stock_code") or "").strip(),',
    '        "stock_code": _normalize_stock_code(row.get("stock_code")),',
)
reporting_path.write_text(reporting, encoding="utf-8")

sheets_path = ROOT / "kospi_active" / "sheets_store.py"
sheets = sheets_path.read_text(encoding="utf-8")
sheets = sheets.replace(
    'worksheet.update(values, value_input_option="USER_ENTERED")',
    'worksheet.update(values, value_input_option="RAW")',
)
sheets_path.write_text(sheets, encoding="utf-8")

print("Applied stock-code normalization and RAW Sheets writes.")
