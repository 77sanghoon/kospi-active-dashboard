from __future__ import annotations

from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[2]
SHEETS_PATH = ROOT / "kospi_active" / "sheets_store.py"
MARKER = "# --- intraday ETF merge update patch ---"

text = SHEETS_PATH.read_text(encoding="utf-8")

if MARKER not in text:
    text += "\n" + dedent(
        r'''
        # --- intraday ETF merge update patch ---
        import re as _intraday_re

        _intraday_original_update_values = GoogleSheetsStore.update_values


        def _intraday_is_trade_date_sheet(sheet_name):
            return bool(_intraday_re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(sheet_name or "")))


        def _intraday_get_spreadsheet(store):
            for attr in ("spreadsheet", "sheet", "_spreadsheet"):
                spreadsheet = getattr(store, attr, None)
                if spreadsheet is not None and hasattr(spreadsheet, "worksheet"):
                    return spreadsheet
            return None


        def _intraday_values_to_rows(values):
            if not values:
                return []
            source_headers = [str(header or "").strip() for header in values[0]]
            rows = []
            for values_row in values[1:]:
                row = {}
                for index, header in enumerate(source_headers):
                    if header:
                        row[header] = values_row[index] if index < len(values_row) else ""
                if any(str(value).strip() for value in row.values()):
                    rows.append(row)
            return rows


        def _intraday_number(value):
            try:
                return float(str(value).replace(",", "") or 0)
            except (TypeError, ValueError):
                return 0.0


        def _intraday_sort_key(row):
            return (
                str(row.get("etf_code") or ""),
                -_intraday_number(row.get("weight")),
                str(row.get("stock_name") or ""),
                str(row.get("stock_code") or ""),
            )


        def _intraday_merge_by_etf(headers, existing_rows, incoming_rows):
            incoming_etfs = {
                str(row.get("etf_code") or "").strip()
                for row in incoming_rows
                if str(row.get("etf_code") or "").strip()
            }
            if not incoming_etfs:
                return incoming_rows

            kept_rows = [
                dict(row)
                for row in existing_rows
                if str(row.get("etf_code") or "").strip() not in incoming_etfs
            ]
            merged_rows = kept_rows + [dict(row) for row in incoming_rows]
            header_set = set(headers)
            normalized_rows = []
            for row in merged_rows:
                normalized_rows.append({header: row.get(header, "") for header in headers if header in header_set})
            return sorted(normalized_rows, key=_intraday_sort_key)


        def _intraday_merge_update_values(self, sheet_name, headers, rows):
            header_list = list(headers or [])
            row_list = [dict(row) for row in (rows or [])]
            if (
                not _intraday_is_trade_date_sheet(sheet_name)
                or not row_list
                or "etf_code" not in header_list
                or "stock_code" not in header_list
            ):
                return _intraday_original_update_values(self, sheet_name, header_list, row_list)

            spreadsheet = _intraday_get_spreadsheet(self)
            if spreadsheet is None:
                return _intraday_original_update_values(self, sheet_name, header_list, row_list)

            try:
                worksheet = spreadsheet.worksheet(sheet_name)
            except Exception:
                return _intraday_original_update_values(self, sheet_name, header_list, row_list)

            try:
                existing_values = worksheet.get_all_values()
            except Exception:
                return _intraday_original_update_values(self, sheet_name, header_list, row_list)

            existing_rows = _intraday_values_to_rows(existing_values)
            if not existing_rows:
                return _intraday_original_update_values(self, sheet_name, header_list, row_list)

            merged_rows = _intraday_merge_by_etf(header_list, existing_rows, row_list)
            return _intraday_original_update_values(self, sheet_name, header_list, merged_rows)


        GoogleSheetsStore.update_values = _intraday_merge_update_values
        '''
    ).lstrip()
    SHEETS_PATH.write_text(text, encoding="utf-8")

print("Applied intraday ETF merge update patch.")
