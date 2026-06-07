from __future__ import annotations

from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[2]


def write_text(relative_path: str, content: str) -> None:
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(content).strip() + "\n", encoding="utf-8")


write_text(
    "kospi_active/analysis.py",
    r'''
    from __future__ import annotations

    import math
    from collections import defaultdict
    from dataclasses import dataclass
    from typing import Iterable

    from .config import load_stock_metadata


    @dataclass(frozen=True)
    class Signal:
        stock_code: str
        stock_name: str
        signal_type: str
        score: float
        detail: str
        etf_count: int
        latest_weight: float
        latest_weight_delta: float
        latest_share_delta: float


    @dataclass(frozen=True)
    class Candidate:
        stock_code: str
        stock_name: str
        score: float
        etf_count: int
        positive_etf_count: int
        latest_weight: float
        latest_weight_delta: float
        latest_share_delta: float
        max_streak: int
        reason: str
        watch_points: str


    @dataclass(frozen=True)
    class GrowthCandidate:
        stock_code: str
        stock_name: str
        score: float
        etf_count: int
        activity_etf_count: int
        expanded_etf_count: int
        latest_weight: float
        latest_weight_delta: float
        latest_share_delta: float
        max_streak: int
        reason: str
        watch_points: str


    def _num(value: object) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0


    def _is_stock_row(row: dict) -> bool:
        value = row.get("is_stock", 1)
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "y", "yes", "stock", "주식"}
        return value in (1, True)


    def _analysis_rows(rows: Iterable[dict]) -> list[dict]:
        stock_rows = [row for row in rows if _is_stock_row(row)]
        live_rows = [row for row in stock_rows if str(row.get("source", "")).lower() != "sample"]
        return live_rows if live_rows else stock_rows


    def _join(parts: Iterable[str]) -> str:
        return " · ".join(part for part in parts if part)


    def enrich_deltas(rows: list[dict]) -> list[dict]:
        ordered = sorted(rows, key=lambda r: (r["etf_code"], r["stock_code"], r["trade_date"]))
        previous_by_pair: dict[tuple[str, str], dict] = {}
        enriched: list[dict] = []
        for row in ordered:
            pair = (row["etf_code"], row["stock_code"])
            prev = previous_by_pair.get(pair)
            item = dict(row)
            item["weight_delta"] = _num(row.get("weight")) - _num(prev.get("weight")) if prev else 0.0
            item["share_delta"] = _num(row.get("shares")) - _num(prev.get("shares")) if prev else 0.0
            item["market_value_delta"] = _num(row.get("market_value")) - _num(prev.get("market_value")) if prev else 0.0
            previous_by_pair[pair] = row
            enriched.append(item)
        return sorted(enriched, key=lambda r: (r["trade_date"], r["stock_code"], r["etf_code"]))


    def latest_date(rows: list[dict]) -> str | None:
        return max((row["trade_date"] for row in rows), default=None)


    def latest_rows(rows: list[dict]) -> list[dict]:
        current_date = latest_date(rows)
        return [row for row in rows if row["trade_date"] == current_date] if current_date else []


    def _stock_summary(rows: list[dict]) -> dict[str, dict]:
        summary: dict[str, dict] = {}
        for row in rows:
            stock = summary.setdefault(
                row["stock_code"],
                {
                    "stock_code": row["stock_code"],
                    "stock_name": row["stock_name"],
                    "latest_weight": 0.0,
                    "latest_weight_delta": 0.0,
                    "latest_share_delta": 0.0,
                    "etfs": set(),
                },
            )
            stock["latest_weight"] += _num(row.get("weight"))
            stock["latest_weight_delta"] += _num(row.get("weight_delta"))
            stock["latest_share_delta"] += _num(row.get("share_delta"))
            stock["etfs"].add(row["etf_code"])
        return summary


    def _rows_by_stock(rows: list[dict]) -> dict[str, list[dict]]:
        grouped: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            grouped[row["stock_code"]].append(row)
        return grouped


    def _streak_lengths(rows: list[dict]) -> dict[tuple[str, str], int]:
        grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for row in rows:
            grouped[(row["stock_code"], row["etf_code"])].append(row)

        streaks: dict[tuple[str, str], int] = {}
        for key, items in grouped.items():
            streak = 0
            for row in sorted(items, key=lambda r: r["trade_date"], reverse=True):
                if _num(row.get("weight_delta")) > 0 and _num(row.get("share_delta")) > 0:
                    streak += 1
                else:
                    break
            streaks[key] = streak
        return streaks


    def _metadata_reason(stock_code: str, metadata: dict) -> str:
        meta = metadata.get(stock_code, {})
        if not meta:
            return "개별 뉴스와 실적 모멘텀 추가 확인 필요"
        sector = meta.get("sector", "")
        themes = ", ".join(meta.get("themes", [])[:3])
        if sector and themes:
            return f"{sector} 업종 내 {themes} 노출"
        if sector:
            return f"{sector} 업종 노출"
        if themes:
            return f"{themes} 테마 노출"
        return "개별 뉴스와 실적 모멘텀 추가 확인 필요"


    def _watch_points(stock_code: str, metadata: dict) -> str:
        points = metadata.get(stock_code, {}).get("watch_points", [])
        return ", ".join(points[:3]) if points else "실적, 수급, 밸류에이션 변화 추가 확인 필요"


    def _explanation(stock_code: str, *, etf_count: int, expanded_count: int, half_count: int, one_count: int, max_streak: int, metadata: dict) -> str:
        parts = []
        if expanded_count >= 5:
            parts.append("5개 ETF에서 동시에 비중과 보유주식 수가 늘어 공통 편입 확대 신호가 강합니다")
        elif expanded_count >= 3:
            parts.append(f"{expanded_count}개 ETF에서 비중과 보유주식 수가 함께 늘었습니다")
        elif expanded_count > 0:
            parts.append(f"{expanded_count}개 ETF에서 실제 보유 수량 증가가 동반됐습니다")
        if one_count >= 3:
            parts.append(f"{one_count}개 ETF에서 비중이 각각 +1.0%p 이상 늘어 강한 액티브 조정으로 보입니다")
        elif half_count >= 3:
            parts.append(f"{half_count}개 ETF에서 비중이 각각 +0.5%p 이상 늘었습니다")
        if max_streak >= 5:
            parts.append("5개장일 연속 확대 흐름이 확인돼 일회성 리밸런싱 가능성이 낮습니다")
        elif max_streak >= 3:
            parts.append("3개장일 연속 확대 흐름이 확인됩니다")
        if etf_count >= 3:
            parts.append(f"총 {etf_count}개 ETF가 보유 중이라 액티브 운용자 관심도가 높습니다")
        parts.append(_metadata_reason(stock_code, metadata))
        return _join(parts)


    def generate_etf_expansions(rows: list[dict], metadata: dict | None = None) -> list[dict]:
        metadata = metadata if metadata is not None else load_stock_metadata()
        enriched = _analysis_rows(enrich_deltas(rows))
        current = latest_rows(enriched)
        streaks = _streak_lengths(enriched)
        expansions = []
        for row in current:
            if _num(row.get("weight_delta")) <= 0 or _num(row.get("share_delta")) <= 0:
                continue
            streak = streaks.get((row["stock_code"], row["etf_code"]), 0)
            reason = _join(
                [
                    "전 개장일 대비 비중과 보유주식 수 동시 증가",
                    f"{streak}개장일 연속 확대" if streak >= 3 else "",
                    _metadata_reason(row["stock_code"], metadata),
                ]
            )
            expansions.append(
                {
                    "trade_date": row["trade_date"],
                    "etf_code": row["etf_code"],
                    "etf_name": row["etf_name"],
                    "stock_code": row["stock_code"],
                    "stock_name": row["stock_name"],
                    "latest_weight": round(_num(row.get("weight")), 4),
                    "weight_delta": round(_num(row.get("weight_delta")), 4),
                    "share_delta": round(_num(row.get("share_delta")), 4),
                    "streak": streak,
                    "reason": reason,
                }
            )
        return sorted(expansions, key=lambda row: (row["etf_name"], -row["weight_delta"], row["stock_name"]))


    def generate_signals(rows: list[dict]) -> list[dict]:
        enriched = _analysis_rows(enrich_deltas(rows))
        current = latest_rows(enriched)
        if not current:
            return []

        metadata = load_stock_metadata()
        summary = _stock_summary(current)
        current_etfs = {row["etf_code"] for row in current}
        target_etf_count = max(5, len(current_etfs)) if current_etfs else 5
        by_stock = _rows_by_stock(current)
        streaks = _streak_lengths(enriched)
        signals: list[Signal] = []

        for stock_code, stock_rows in by_stock.items():
            item = summary[stock_code]
            expanded = [row for row in stock_rows if _num(row.get("weight_delta")) > 0 and _num(row.get("share_delta")) > 0]
            half = [row for row in stock_rows if _num(row.get("weight_delta")) >= 0.5]
            one = [row for row in stock_rows if _num(row.get("weight_delta")) >= 1.0]
            max_streak = max((streaks.get((stock_code, row["etf_code"]), 0) for row in stock_rows), default=0)
            expanded_count = len({row["etf_code"] for row in expanded})
            half_count = len({row["etf_code"] for row in half})
            one_count = len({row["etf_code"] for row in one})
            etf_names = ", ".join(sorted({row["etf_name"] for row in expanded})[:5])

            if expanded_count >= target_etf_count:
                signals.append(
                    Signal(
                        stock_code=stock_code,
                        stock_name=item["stock_name"],
                        signal_type="5개 ETF 공통 비중·수량 확대",
                        score=120 + item["latest_weight_delta"] * 10 + math.log10(max(item["latest_share_delta"], 0) + 1) * 4,
                        detail=f"5개 ETF 모두에서 전 개장일 대비 비중과 보유주식 수가 증가했습니다. 대상 ETF: {etf_names}",
                        etf_count=expanded_count,
                        latest_weight=item["latest_weight"],
                        latest_weight_delta=item["latest_weight_delta"],
                        latest_share_delta=item["latest_share_delta"],
                    )
                )
            elif expanded_count > 0:
                signals.append(
                    Signal(
                        stock_code=stock_code,
                        stock_name=item["stock_name"],
                        signal_type="비중·수량 동시 확대",
                        score=expanded_count * 12 + max(item["latest_weight_delta"], 0) * 6 + math.log10(max(item["latest_share_delta"], 0) + 1),
                        detail=f"{expanded_count}개 ETF에서 전 개장일 대비 비중과 보유주식 수가 함께 증가했습니다. 대상 ETF: {etf_names}",
                        etf_count=expanded_count,
                        latest_weight=item["latest_weight"],
                        latest_weight_delta=item["latest_weight_delta"],
                        latest_share_delta=item["latest_share_delta"],
                    )
                )

            for threshold, count, label, base in (
                (0.5, half_count, "3개 이상 ETF 비중 +0.5%p", 55),
                (1.0, one_count, "3개 이상 ETF 비중 +1.0%p", 80),
            ):
                if count >= 3:
                    signals.append(
                        Signal(
                            stock_code=stock_code,
                            stock_name=item["stock_name"],
                            signal_type=label,
                            score=base + count * 8 + item["latest_weight_delta"] * 6,
                            detail=f"{count}개 ETF에서 각각 +{threshold:.1f}%p 이상 비중이 증가했습니다.",
                            etf_count=count,
                            latest_weight=item["latest_weight"],
                            latest_weight_delta=item["latest_weight_delta"],
                            latest_share_delta=item["latest_share_delta"],
                        )
                    )

            for days, base in ((3, 35), (5, 65)):
                streak_etfs = [row for row in stock_rows if streaks.get((stock_code, row["etf_code"]), 0) >= days]
                if streak_etfs:
                    names = ", ".join(sorted({row["etf_name"] for row in streak_etfs})[:5])
                    signals.append(
                        Signal(
                            stock_code=stock_code,
                            stock_name=item["stock_name"],
                            signal_type=f"ETF별 {days}개장일 연속 확대",
                            score=base + len(streak_etfs) * 8 + max_streak * 4 + max(item["latest_weight_delta"], 0) * 3,
                            detail=f"{names}에서 최근 {days}개장일 이상 비중과 보유주식 수가 모두 늘었습니다.",
                            etf_count=len(streak_etfs),
                            latest_weight=item["latest_weight"],
                            latest_weight_delta=item["latest_weight_delta"],
                            latest_share_delta=item["latest_share_delta"],
                        )
                    )

        merged: dict[tuple[str, str], Signal] = {}
        for signal in signals:
            key = (signal.stock_code, signal.signal_type)
            if key not in merged or signal.score > merged[key].score:
                merged[key] = signal
        return [signal.__dict__ for signal in sorted(merged.values(), key=lambda item: item.score, reverse=True)]


    def generate_candidate_rankings(rows: list[dict], metadata: dict | None = None, limit: int = 50) -> list[dict]:
        metadata = metadata if metadata is not None else load_stock_metadata()
        enriched = _analysis_rows(enrich_deltas(rows))
        current = latest_rows(enriched)
        if not current:
            return []

        summary = _stock_summary(current)
        by_stock = _rows_by_stock(current)
        streaks = _streak_lengths(enriched)
        candidates: list[Candidate] = []

        for stock_code, item in summary.items():
            stock_rows = by_stock[stock_code]
            etf_count = len(item["etfs"])
            expanded_rows = [row for row in stock_rows if _num(row.get("weight_delta")) > 0 and _num(row.get("share_delta")) > 0]
            half_count = len({row["etf_code"] for row in stock_rows if _num(row.get("weight_delta")) >= 0.5})
            one_count = len({row["etf_code"] for row in stock_rows if _num(row.get("weight_delta")) >= 1.0})
            positive_etf_count = len({row["etf_code"] for row in expanded_rows})
            max_streak = max((streaks.get((stock_code, etf_code), 0) for etf_code in item["etfs"]), default=0)
            latest_weight_delta = item["latest_weight_delta"]
            latest_share_delta = item["latest_share_delta"]
            score = (
                etf_count * 6
                + positive_etf_count * 22
                + half_count * 18
                + one_count * 28
                + max(latest_weight_delta, 0) * 18
                + math.log10(max(latest_share_delta, 0) + 1) * 5
                + max_streak * 9
                + min(item["latest_weight"], 30) * 0.6
                + (40 if positive_etf_count >= 5 else 0)
                + (5 if metadata.get(stock_code) else 0)
            )
            reason = _explanation(
                stock_code,
                etf_count=etf_count,
                expanded_count=positive_etf_count,
                half_count=half_count,
                one_count=one_count,
                max_streak=max_streak,
                metadata=metadata,
            )
            candidates.append(
                Candidate(
                    stock_code=stock_code,
                    stock_name=item["stock_name"],
                    score=round(score, 2),
                    etf_count=etf_count,
                    positive_etf_count=positive_etf_count,
                    latest_weight=round(item["latest_weight"], 4),
                    latest_weight_delta=round(latest_weight_delta, 4),
                    latest_share_delta=round(latest_share_delta, 4),
                    max_streak=max_streak,
                    reason=reason,
                    watch_points=_watch_points(stock_code, metadata),
                )
            )

        ranked = sorted(candidates, key=lambda item: (item.score, item.positive_etf_count, item.latest_weight_delta), reverse=True)
        return [candidate.__dict__ for candidate in ranked[:limit]]


    def generate_growth_rankings(rows: list[dict], metadata: dict | None = None, limit: int = 50) -> list[dict]:
        metadata = metadata if metadata is not None else load_stock_metadata()
        enriched = _analysis_rows(enrich_deltas(rows))
        current = latest_rows(enriched)
        if not current:
            return []

        summary = _stock_summary(current)
        by_stock = _rows_by_stock(current)
        streaks = _streak_lengths(enriched)
        candidates: list[GrowthCandidate] = []

        for stock_code, item in summary.items():
            stock_rows = by_stock[stock_code]
            expanded_rows = [row for row in stock_rows if _num(row.get("weight_delta")) > 0 and _num(row.get("share_delta")) > 0]
            weight_up_rows = [row for row in stock_rows if _num(row.get("weight_delta")) > 0]
            share_up_rows = [row for row in stock_rows if _num(row.get("share_delta")) > 0]
            activity_etf_count = len({row["etf_code"] for row in weight_up_rows + share_up_rows})
            expanded_etf_count = len({row["etf_code"] for row in expanded_rows})
            max_streak = max((streaks.get((stock_code, etf_code), 0) for etf_code in item["etfs"]), default=0)
            latest_weight_delta = item["latest_weight_delta"]
            latest_share_delta = item["latest_share_delta"]
            if not expanded_rows and latest_weight_delta <= 0 and latest_share_delta <= 0 and max_streak < 3:
                continue

            score = (
                expanded_etf_count * 35
                + activity_etf_count * 7
                + max(latest_weight_delta, 0) * 35
                + math.log10(max(latest_share_delta, 0) + 1) * 8
                + max_streak * 11
                + len(item["etfs"]) * 2
                + min(item["latest_weight"], 20) * 0.4
                + (4 if metadata.get(stock_code) else 0)
            )
            half_count = len({row["etf_code"] for row in stock_rows if _num(row.get("weight_delta")) >= 0.5})
            one_count = len({row["etf_code"] for row in stock_rows if _num(row.get("weight_delta")) >= 1.0})
            candidates.append(
                GrowthCandidate(
                    stock_code=stock_code,
                    stock_name=item["stock_name"],
                    score=round(score, 2),
                    etf_count=len(item["etfs"]),
                    activity_etf_count=activity_etf_count,
                    expanded_etf_count=expanded_etf_count,
                    latest_weight=round(item["latest_weight"], 4),
                    latest_weight_delta=round(latest_weight_delta, 4),
                    latest_share_delta=round(latest_share_delta, 4),
                    max_streak=max_streak,
                    reason=_explanation(
                        stock_code,
                        etf_count=len(item["etfs"]),
                        expanded_count=expanded_etf_count,
                        half_count=half_count,
                        one_count=one_count,
                        max_streak=max_streak,
                        metadata=metadata,
                    ),
                    watch_points=_watch_points(stock_code, metadata),
                )
            )

        ranked = sorted(candidates, key=lambda item: (item.score, item.expanded_etf_count, item.latest_weight_delta), reverse=True)
        return [candidate.__dict__ for candidate in ranked[:limit]]


    def stock_reason(signal: dict, metadata: dict | None = None) -> str:
        metadata = metadata if metadata is not None else load_stock_metadata()
        stock_code = signal.get("stock_code", "")
        parts = []
        signal_type = signal.get("signal_type", "")
        if "5개 ETF" in signal_type:
            parts.append("5개 ETF 운용자가 같은 방향으로 편입을 늘린 공통 신호입니다")
        if "+1.0%p" in signal_type:
            parts.append("비중 변화 폭이 커서 단순 가격 변동보다 액티브 편입 조정 가능성이 높습니다")
        elif "+0.5%p" in signal_type:
            parts.append("여러 ETF에서 의미 있는 비중 확대가 동시에 나타났습니다")
        if "연속" in signal_type:
            parts.append("여러 개장일에 걸친 누적 확대라 일회성 리밸런싱보다 지속 매수 흐름에 가깝습니다")
        if _num(signal.get("latest_share_delta")) > 0:
            parts.append("보유주식 수 증가가 동반되어 가격 상승만으로 비중이 커진 경우와 구분됩니다")
        if _num(signal.get("latest_weight_delta")) > 0:
            parts.append(f"합산 비중이 +{_num(signal.get('latest_weight_delta')):.2f}%p 늘었습니다")
        parts.append(_metadata_reason(stock_code, metadata))
        watch = _watch_points(stock_code, metadata)
        if watch:
            parts.append("확인 포인트: " + watch)
        return _join(parts)
    ''',
)

write_text(
    "kospi_active/reporting.py",
    r'''
    from __future__ import annotations

    import re
    from collections import defaultdict
    from datetime import datetime
    from typing import Iterable

    from .analysis import (
        enrich_deltas,
        generate_candidate_rankings,
        generate_etf_expansions,
        generate_growth_rankings,
        generate_signals,
        latest_date,
        latest_rows,
        stock_reason,
    )
    from .config import load_etfs, load_stock_metadata


    DATE_SHEET_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    DATE_HEADERS = [
        "trade_date",
        "etf_code",
        "etf_name",
        "stock_code",
        "stock_name",
        "weight",
        "shares",
        "market_value",
        "weight_delta",
        "share_delta",
        "market_value_delta",
        "source",
        "is_stock",
        "close_price",
        "price_change",
        "source_url",
        "collected_at",
    ]

    STATUS_HEADERS = ["etf_code", "etf_name", "source", "first_date", "latest_date", "date_count", "holding_count"]

    SIGNAL_HEADERS = [
        "stock_code",
        "stock_name",
        "signal_type",
        "score",
        "etf_count",
        "latest_weight",
        "latest_weight_delta",
        "latest_share_delta",
        "reason",
    ]

    ETF_EXPANSION_HEADERS = [
        "trade_date",
        "etf_code",
        "etf_name",
        "stock_code",
        "stock_name",
        "latest_weight",
        "weight_delta",
        "share_delta",
        "streak",
        "reason",
    ]

    LOG_HEADERS = ["run_at", "trade_date", "status", "message"]

    CANDIDATE_HEADERS = [
        "stock_code",
        "stock_name",
        "score",
        "etf_count",
        "positive_etf_count",
        "latest_weight",
        "latest_weight_delta",
        "latest_share_delta",
        "max_streak",
        "reason",
        "watch_points",
    ]

    GROWTH_HEADERS = [
        "stock_code",
        "stock_name",
        "score",
        "etf_count",
        "activity_etf_count",
        "expanded_etf_count",
        "latest_weight",
        "latest_weight_delta",
        "latest_share_delta",
        "max_streak",
        "reason",
        "watch_points",
    ]

    SUMMARY_SHEETS = {"ETF_Status", "ETF_Expansion", "Growth_Ranking", "Signals", "Candidate_Ranking", "Collection_Log"}


    def is_date_sheet(title: str) -> bool:
        return bool(DATE_SHEET_PATTERN.fullmatch(title))


    def _to_float(value: object) -> float:
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip().replace(",", "").replace("%", "")
        if not text or text == "-":
            return 0.0
        try:
            return float(text)
        except ValueError:
            return 0.0


    def _to_int(value: object) -> int:
        return int(round(_to_float(value)))


    def _to_bool_int(value: object) -> int:
        if isinstance(value, bool):
            return 1 if value else 0
        if isinstance(value, (int, float)):
            return 1 if value else 0
        text = str(value or "").strip().lower()
        return 0 if text in {"0", "false", "n", "no", "비주식"} else 1


    def normalize_holding_row(row: dict) -> dict:
        normalized = {
            "trade_date": str(row.get("trade_date") or "").strip(),
            "etf_code": str(row.get("etf_code") or "").strip(),
            "etf_name": str(row.get("etf_name") or "").strip(),
            "stock_code": str(row.get("stock_code") or "").strip(),
            "stock_name": str(row.get("stock_name") or "").strip(),
            "weight": _to_float(row.get("weight")),
            "shares": _to_float(row.get("shares")),
            "market_value": _to_int(row.get("market_value")),
            "source": str(row.get("source") or "unknown").strip(),
            "close_price": row.get("close_price"),
            "price_change": row.get("price_change"),
            "source_url": str(row.get("source_url") or "").strip(),
            "is_stock": _to_bool_int(row.get("is_stock", 1)),
            "collected_at": str(row.get("collected_at") or "").strip(),
        }
        if normalized["close_price"] not in (None, ""):
            normalized["close_price"] = _to_float(normalized["close_price"])
        if normalized["price_change"] not in (None, ""):
            normalized["price_change"] = _to_float(normalized["price_change"])
        return normalized


    def normalize_holding_rows(rows: Iterable[dict]) -> list[dict]:
        normalized = [normalize_holding_row(row) for row in rows]
        return [row for row in normalized if row["trade_date"] and row["etf_code"] and row["stock_code"]]


    def holding_to_row(holding: object, collected_at: str) -> dict:
        return normalize_holding_row(
            {
                "trade_date": getattr(holding, "trade_date"),
                "etf_code": getattr(holding, "etf_code"),
                "etf_name": getattr(holding, "etf_name"),
                "stock_code": getattr(holding, "stock_code"),
                "stock_name": getattr(holding, "stock_name"),
                "weight": getattr(holding, "weight"),
                "shares": getattr(holding, "shares"),
                "market_value": getattr(holding, "market_value"),
                "source": getattr(holding, "source"),
                "close_price": getattr(holding, "close_price"),
                "price_change": getattr(holding, "price_change"),
                "source_url": getattr(holding, "source_url"),
                "is_stock": getattr(holding, "is_stock"),
                "collected_at": collected_at,
            }
        )


    def merge_snapshot_rows(existing_rows: Iterable[dict], new_rows: Iterable[dict]) -> list[dict]:
        existing = normalize_holding_rows(existing_rows)
        new = normalize_holding_rows(new_rows)
        snapshot_keys = {(row["trade_date"], row["etf_code"]) for row in new}
        merged = [row for row in existing if (row["trade_date"], row["etf_code"]) not in snapshot_keys]
        merged.extend(new)
        return sorted(merged, key=lambda row: (row["trade_date"], row["etf_code"], -float(row.get("weight") or 0), row["stock_name"]))


    def has_snapshot(rows: Iterable[dict], etf_code: str, trade_date: str) -> bool:
        return any(row.get("etf_code") == etf_code and row.get("trade_date") == trade_date for row in rows)


    def build_etf_status(rows: Iterable[dict]) -> list[dict]:
        groups: dict[tuple[str, str], dict] = {}
        for row in normalize_holding_rows(rows):
            key = (row["etf_code"], row["etf_name"])
            item = groups.setdefault(
                key,
                {
                    "etf_code": row["etf_code"],
                    "etf_name": row["etf_name"],
                    "source": row["source"],
                    "dates": set(),
                    "holding_count": 0,
                },
            )
            item["source"] = row["source"] or item["source"]
            item["dates"].add(row["trade_date"])
            item["holding_count"] += 1

        status_rows = []
        for item in groups.values():
            dates = sorted(item.pop("dates"))
            status_rows.append(
                {
                    "etf_code": item["etf_code"],
                    "etf_name": item["etf_name"],
                    "source": item["source"],
                    "first_date": dates[0] if dates else "",
                    "latest_date": dates[-1] if dates else "",
                    "date_count": len(dates),
                    "holding_count": item["holding_count"],
                }
            )
        return sorted(status_rows, key=lambda row: row["etf_name"])


    def _common_expanded_stocks(expansions: list[dict], target_count: int, metadata: dict) -> list[dict]:
        grouped: dict[str, list[dict]] = defaultdict(list)
        for row in expansions:
            grouped[row["stock_code"]].append(row)
        common = []
        for stock_code, items in grouped.items():
            etfs = sorted({row["etf_name"] for row in items})
            if len(etfs) < target_count:
                continue
            common.append(
                {
                    "stock_code": stock_code,
                    "stock_name": items[0]["stock_name"],
                    "etf_count": len(etfs),
                    "etfs": ", ".join(etfs),
                    "latest_weight_delta": round(sum(float(row.get("weight_delta") or 0) for row in items), 4),
                    "latest_share_delta": round(sum(float(row.get("share_delta") or 0) for row in items), 4),
                    "reason": stock_reason(
                        {
                            "stock_code": stock_code,
                            "stock_name": items[0]["stock_name"],
                            "signal_type": "5개 ETF 공통 비중·수량 확대",
                            "etf_count": len(etfs),
                            "latest_weight_delta": sum(float(row.get("weight_delta") or 0) for row in items),
                            "latest_share_delta": sum(float(row.get("share_delta") or 0) for row in items),
                        },
                        metadata,
                    ),
                }
            )
        return sorted(common, key=lambda row: (row["latest_weight_delta"], row["latest_share_delta"]), reverse=True)


    def build_report_payload(rows: Iterable[dict], job_runs: Iterable[dict] | None = None, *, data_mode: str = "live") -> dict:
        holdings = normalize_holding_rows(rows)
        enriched = enrich_deltas(holdings)
        metadata = load_stock_metadata()
        etfs = load_etfs()
        signals = generate_signals(holdings)
        for signal in signals:
            signal["reason"] = stock_reason(signal, metadata)
        candidates = generate_candidate_rankings(holdings, metadata)
        growth_candidates = generate_growth_rankings(holdings, metadata)
        etf_expansions = generate_etf_expansions(holdings, metadata)
        current = latest_rows(enriched)
        collected_etfs = {row["etf_code"] for row in current}
        common = _common_expanded_stocks(etf_expansions, len(etfs), metadata)
        threshold_05 = len({row["stock_code"] for row in signals if row["signal_type"] == "3개 이상 ETF 비중 +0.5%p"})
        threshold_10 = len({row["stock_code"] for row in signals if row["signal_type"] == "3개 이상 ETF 비중 +1.0%p"})

        return {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "etfs": [item.to_dict() for item in etfs],
            "dataMode": data_mode,
            "analysisSummary": {
                "latestDate": latest_date(enriched),
                "collectedEtfCount": len(collected_etfs),
                "stockCount": len({row["stock_code"] for row in current}),
                "etfExpansionCount": len(etf_expansions),
                "commonExpansionCount": len(common),
                "threshold05Count": threshold_05,
                "threshold10Count": threshold_10,
            },
            "etfStatus": build_etf_status(holdings),
            "jobRuns": list(job_runs or []),
            "stockMetadata": metadata,
            "dates": sorted({row["trade_date"] for row in holdings}),
            "holdings": enriched,
            "etfExpansions": etf_expansions,
            "commonExpandedStocks": common,
            "signals": signals,
            "candidateRankings": candidates,
            "growthRankings": growth_candidates,
        }


    def rows_for_headers(rows: Iterable[dict], headers: list[str]) -> list[list[object]]:
        return [[row.get(header, "") for header in headers] for row in rows]


    def group_rows_by_date(rows: Iterable[dict]) -> dict[str, list[dict]]:
        grouped: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            grouped[str(row["trade_date"])].append(row)
        return dict(sorted(grouped.items()))
    ''',
)

write_text(
    "kospi_active/sheets_store.py",
    r'''
    from __future__ import annotations

    import base64
    import json
    import os
    from dataclasses import dataclass
    from typing import Iterable

    from .reporting import (
        CANDIDATE_HEADERS,
        DATE_HEADERS,
        ETF_EXPANSION_HEADERS,
        GROWTH_HEADERS,
        LOG_HEADERS,
        SIGNAL_HEADERS,
        STATUS_HEADERS,
        group_rows_by_date,
        is_date_sheet,
        normalize_holding_rows,
        rows_for_headers,
    )


    class GoogleSheetsConfigError(RuntimeError):
        pass


    @dataclass(frozen=True)
    class GoogleSheetsStore:
        spreadsheet: object

        @classmethod
        def from_env(cls) -> "GoogleSheetsStore":
            spreadsheet_id = os.environ.get("GOOGLE_SPREADSHEET_ID")
            if not spreadsheet_id:
                raise GoogleSheetsConfigError("GOOGLE_SPREADSHEET_ID is not set.")

            try:
                import gspread
            except ImportError as exc:
                raise GoogleSheetsConfigError("gspread is not installed. Install requirements.txt first.") from exc

            service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
            service_account_b64 = os.environ.get("GOOGLE_SERVICE_ACCOUNT_B64")
            service_account_file = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE")

            if service_account_json:
                credentials = json.loads(service_account_json)
                client = gspread.service_account_from_dict(credentials)
            elif service_account_b64:
                credentials = json.loads(base64.b64decode(service_account_b64).decode("utf-8"))
                client = gspread.service_account_from_dict(credentials)
            elif service_account_file:
                client = gspread.service_account(filename=service_account_file)
            else:
                raise GoogleSheetsConfigError("Set GOOGLE_SERVICE_ACCOUNT_JSON, GOOGLE_SERVICE_ACCOUNT_B64, or GOOGLE_SERVICE_ACCOUNT_FILE.")

            return cls(client.open_by_key(spreadsheet_id))

        def _worksheet_by_title(self, title: str):
            try:
                return self.spreadsheet.worksheet(title)
            except Exception as exc:
                if exc.__class__.__name__ != "WorksheetNotFound":
                    raise
                return None

        def read_holdings(self) -> list[dict]:
            rows: list[dict] = []
            for worksheet in self.spreadsheet.worksheets():
                if not is_date_sheet(worksheet.title):
                    continue
                rows.extend(worksheet.get_all_records(default_blank=""))
            return normalize_holding_rows(rows)

        def read_collection_log(self, limit: int = 200) -> list[dict]:
            worksheet = self._worksheet_by_title("Collection_Log")
            if worksheet is None:
                return []
            rows = worksheet.get_all_records(default_blank="")
            return rows[:limit]

        def update_values(self, title: str, headers: list[str], rows: Iterable[dict]) -> None:
            items = list(rows)
            values = [headers] + rows_for_headers(items, headers)
            worksheet = self._worksheet_by_title(title)
            if worksheet is None:
                worksheet = self.spreadsheet.add_worksheet(title=title, rows=max(100, len(values) + 5), cols=max(1, len(headers)))
            else:
                worksheet.clear()
                worksheet.resize(rows=max(100, len(values) + 5), cols=max(1, len(headers)))
            worksheet.update(values, value_input_option="USER_ENTERED")

        def write_report(self, payload: dict, date_filter: Iterable[str] | None = None) -> None:
            self.update_values("ETF_Status", STATUS_HEADERS, payload["etfStatus"])
            self.update_values("ETF_Expansion", ETF_EXPANSION_HEADERS, payload.get("etfExpansions", []))
            self.update_values("Growth_Ranking", GROWTH_HEADERS, payload["growthRankings"])
            self.update_values("Signals", SIGNAL_HEADERS, payload["signals"])
            self.update_values("Candidate_Ranking", CANDIDATE_HEADERS, payload["candidateRankings"])
            self.update_values("Collection_Log", LOG_HEADERS, payload["jobRuns"])

            allowed_dates = None if date_filter is None else set(date_filter)
            for trade_date, rows in group_rows_by_date(payload["holdings"]).items():
                if allowed_dates is not None and trade_date not in allowed_dates:
                    continue
                self.update_values(trade_date, DATE_HEADERS, rows)
    ''',
)

write_text(
    "scripts/cloud_daily.py",
    r'''
    from __future__ import annotations

    import argparse
    import json
    import sys
    import time
    from datetime import date, datetime
    from pathlib import Path
    from zoneinfo import ZoneInfo

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

    from kospi_active.config import DASHBOARD_DIR, ensure_dirs, load_etfs
    from kospi_active.providers import ProviderError, create_provider, recent_business_dates
    from kospi_active.reporting import build_report_payload, has_snapshot, holding_to_row, merge_snapshot_rows
    from kospi_active.sheets_store import GoogleSheetsConfigError, GoogleSheetsStore


    KST = ZoneInfo("Asia/Seoul")


    def now_kst() -> datetime:
        return datetime.now(KST)


    def log_row(trade_date: str, status: str, message: str) -> dict:
        return {"run_at": now_kst().isoformat(timespec="seconds"), "trade_date": trade_date, "status": status, "message": message}


    def write_dashboard_data(payload: dict) -> None:
        ensure_dirs()
        output = DASHBOARD_DIR / "data.js"
        output.write_text("window.KOSPI_ACTIVE_DATA = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")


    def collect_rows(requested_date: str, existing_rows: list[dict], *, backfill_days: int, force: bool, latest_only: bool, sleep_seconds: float) -> tuple[list[dict], list[dict]]:
        collected_at = now_kst().isoformat(timespec="seconds")
        new_rows: list[dict] = []
        logs: list[dict] = []

        for etf in load_etfs():
            provider = create_provider(etf)
            if latest_only or not etf.supports_history:
                dates = [requested_date]
            else:
                dates = recent_business_dates(backfill_days, date.fromisoformat(requested_date))

            seen_actual_snapshots: set[tuple[str, str]] = set()
            for target_date in dates:
                if not force and has_snapshot(existing_rows, etf.market_code, target_date):
                    continue
                try:
                    holdings = provider.fetch_holdings(target_date)
                    rows = [holding_to_row(holding, collected_at) for holding in holdings]
                    actual_dates = sorted({row["trade_date"] for row in rows})
                    actual_label = ",".join(actual_dates) or target_date
                    duplicate = False
                    for actual_date in actual_dates:
                        key = (actual_date, etf.market_code)
                        if key in seen_actual_snapshots:
                            duplicate = True
                        seen_actual_snapshots.add(key)
                    if duplicate:
                        continue
                    if not force:
                        rows = [row for row in rows if not has_snapshot(existing_rows, row["etf_code"], row["trade_date"])]
                    if rows:
                        new_rows.extend(rows)
                        logs.append(log_row(actual_label, "success", f"{etf.name}: {len(rows)} rows collected from {target_date}"))
                        print(f"{etf.name} {target_date} -> {actual_label}: {len(rows)} rows")
                except ProviderError as exc:
                    message = f"{etf.name} {target_date}: {exc}"
                    logs.append(log_row(target_date, "failed", message))
                    print(f"Failed - {message}")
                finally:
                    if etf.supports_history:
                        time.sleep(max(0.0, sleep_seconds))

        return new_rows, logs


    def affected_dates(new_rows: list[dict], merged_rows: list[dict], requested_date: str, manual_date: bool) -> list[str]:
        affected = {row["trade_date"] for row in new_rows}
        if manual_date:
            affected.add(requested_date)
            all_dates = sorted({row["trade_date"] for row in merged_rows})
            next_dates = [item for item in all_dates if item > requested_date]
            if next_dates:
                affected.add(next_dates[0])
        return sorted(affected)


    def main() -> None:
        parser = argparse.ArgumentParser(description="Cloud daily collector that uses Google Sheets as the source of truth.")
        parser.add_argument("--date", help="Requested date in YYYY-MM-DD. Defaults to today's KST date.")
        parser.add_argument("--backfill-days", type=int, default=92)
        parser.add_argument("--sleep-seconds", type=float, default=1.0)
        parser.add_argument("--latest-only", action="store_true", help="Skip KoAct/KODEX history backfill.")
        parser.add_argument("--force", action="store_true", help="Replace existing snapshots.")
        parser.add_argument("--dry-run", action="store_true", help="Collect and build payload without writing Sheets.")
        parser.add_argument("--run-weekend", action="store_true", help="Allow default weekend runs.")
        args = parser.parse_args()

        requested_date = args.date or now_kst().date().isoformat()
        if not args.date and not args.run_weekend and date.fromisoformat(requested_date).weekday() >= 5:
            print("Weekend run skipped.")
            return

        try:
            store = GoogleSheetsStore.from_env()
        except GoogleSheetsConfigError as exc:
            raise SystemExit(str(exc)) from exc

        existing_rows = store.read_holdings()
        existing_logs = store.read_collection_log()
        print(f"Loaded {len(existing_rows)} existing holding rows from Google Sheets.")

        new_rows, new_logs = collect_rows(
            requested_date,
            existing_rows,
            backfill_days=args.backfill_days,
            force=args.force,
            latest_only=args.latest_only,
            sleep_seconds=args.sleep_seconds,
        )

        if not new_rows and any(row["status"] == "failed" for row in new_logs):
            payload = build_report_payload(existing_rows, [*new_logs, *existing_logs][:200])
            write_dashboard_data(payload)
            dates_to_write = affected_dates([], existing_rows, requested_date, bool(args.date))
            if not args.dry_run:
                store.write_report(payload, date_filter=dates_to_write)
            raise SystemExit("All attempted ETF collections failed; existing Sheets data was left unchanged.")

        merged_rows = merge_snapshot_rows(existing_rows, new_rows)
        payload = build_report_payload(merged_rows, [*new_logs, *existing_logs][:200])
        write_dashboard_data(payload)
        dates_to_write = affected_dates(new_rows, merged_rows, requested_date, bool(args.date))

        if args.dry_run:
            print(f"Dry run completed. New rows: {len(new_rows)}. Sheets were not updated.")
            return

        store.write_report(payload, date_filter=dates_to_write if dates_to_write else [])
        if new_rows or new_logs:
            print(f"Google Sheets updated. New rows: {len(new_rows)}. Date sheets refreshed: {', '.join(dates_to_write) or 'summary only'}.")
        else:
            print("No new snapshots found. Summary sheets and dashboard data refreshed.")


    if __name__ == "__main__":
        main()
    ''',
)

write_text(
    "dashboard/index.html",
    r'''
    <!doctype html>
    <html lang="ko">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>KOSPI Active ETF Dashboard</title>
        <link rel="stylesheet" href="styles.css" />
      </head>
      <body>
        <header class="topbar">
          <div>
            <p class="eyebrow">KOSPI Active ETF</p>
            <h1>국내 종목 확대 신호 대시보드</h1>
          </div>
          <div class="status">
            <span id="latestDate">-</span>
            <span id="holdingCount">-</span>
          </div>
        </header>

        <main>
          <section class="toolbar">
            <label>
              기준일
              <select id="dateSelect"></select>
            </label>
            <label>
              신호
              <select id="signalSelect">
                <option value="all">전체</option>
                <option value="common">5개 ETF 공통 확대</option>
                <option value="0.5">3개 이상 ETF +0.5%p</option>
                <option value="1.0">3개 이상 ETF +1.0%p</option>
                <option value="streak">3/5개장일 연속 확대</option>
              </select>
            </label>
          </section>

          <section class="metrics" id="metrics"></section>

          <section class="panel source-panel">
            <div class="panel-title">
              <h2>5개 ETF 공통 확대 종목</h2>
              <p>전 개장일 대비 5개 ETF 모두에서 비중과 보유주식 수가 늘어난 종목</p>
            </div>
            <div class="table-wrap compact">
              <table>
                <thead>
                  <tr>
                    <th>종목</th>
                    <th>ETF</th>
                    <th>합산 비중 증감</th>
                    <th>합산 수량 증감</th>
                    <th>확대 해석</th>
                  </tr>
                </thead>
                <tbody id="commonBody"></tbody>
              </table>
            </div>
          </section>

          <section class="panel source-panel">
            <div class="panel-title">
              <h2>ETF별 전일 대비 확대 종목</h2>
              <p>각 ETF에서 비중과 보유주식 수가 모두 증가한 종목</p>
            </div>
            <div class="table-wrap compact">
              <table>
                <thead>
                  <tr>
                    <th>ETF</th>
                    <th>종목</th>
                    <th>비중</th>
                    <th>비중 증감</th>
                    <th>수량 증감</th>
                    <th>연속 확대</th>
                    <th>확대 해석</th>
                  </tr>
                </thead>
                <tbody id="expansionBody"></tbody>
              </table>
            </div>
          </section>

          <section class="panel source-panel">
            <div class="panel-title">
              <h2>확대 강도 랭킹</h2>
              <p>ETF 공통성, 비중 변화 폭, 수량 변화, 연속성을 합산한 후보 순위</p>
            </div>
            <div class="table-wrap compact">
              <table>
                <thead>
                  <tr>
                    <th>순위</th>
                    <th>종목</th>
                    <th>점수</th>
                    <th>변화 ETF</th>
                    <th>동시 확대 ETF</th>
                    <th>비중 증감</th>
                    <th>수량 증감</th>
                    <th>판단 근거</th>
                  </tr>
                </thead>
                <tbody id="growthBody"></tbody>
              </table>
            </div>
          </section>

          <section class="panel source-panel">
            <div class="panel-title">
              <h2>투자 후보 랭킹</h2>
              <p>공통 보유, 편입 확대, 테마 노출, 확인 포인트를 함께 본 리서치 후보</p>
            </div>
            <div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>순위</th>
                    <th>종목</th>
                    <th>점수</th>
                    <th>보유 ETF</th>
                    <th>합산 비중</th>
                    <th>비중 증감</th>
                    <th>판단 근거</th>
                    <th>확인 포인트</th>
                  </tr>
                </thead>
                <tbody id="candidateBody"></tbody>
              </table>
            </div>
          </section>

          <section class="layout">
            <article class="panel">
              <div class="panel-title">
                <h2>핵심 신호</h2>
                <p>공통 확대, +0.5%p/+1.0%p, 3/5개장일 연속 확대</p>
              </div>
              <div class="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>종목</th>
                      <th>신호</th>
                      <th>ETF</th>
                      <th>합산 비중</th>
                      <th>비중 증감</th>
                      <th>확대 이유 추정</th>
                    </tr>
                  </thead>
                  <tbody id="signalsBody"></tbody>
                </table>
              </div>
            </article>

            <aside class="panel">
              <div class="panel-title">
                <h2>ETF별 비중 증가 상위</h2>
                <p>선택 기준일의 전 개장일 대비 변화</p>
              </div>
              <div id="etfLeaders" class="leader-list"></div>
            </aside>
          </section>

          <section class="panel source-panel">
            <div class="panel-title">
              <h2>수집 상태</h2>
              <p id="dataModeLabel">-</p>
            </div>
            <div class="table-wrap compact">
              <table>
                <thead>
                  <tr>
                    <th>ETF</th>
                    <th>제공처</th>
                    <th>수집 시작일</th>
                    <th>최신 기준일</th>
                    <th>기준일 수</th>
                    <th>누적 행 수</th>
                  </tr>
                </thead>
                <tbody id="sourceStatusBody"></tbody>
              </table>
            </div>
          </section>

          <section class="panel source-panel">
            <div class="panel-title">
              <h2>최근 수집 로그</h2>
              <p>특정 ETF 실패가 있어도 성공한 데이터와 기존 대시보드는 유지됩니다</p>
            </div>
            <div class="table-wrap compact">
              <table>
                <thead>
                  <tr>
                    <th>실행 시각</th>
                    <th>기준일</th>
                    <th>상태</th>
                    <th>메시지</th>
                  </tr>
                </thead>
                <tbody id="jobRunsBody"></tbody>
              </table>
            </div>
          </section>

          <section class="panel">
            <div class="panel-title">
              <h2>종목별 합산 비중 추이</h2>
              <p>상위 후보의 5개 ETF 합산 비중</p>
            </div>
            <canvas id="trendCanvas" width="1100" height="360"></canvas>
          </section>
        </main>

        <script src="data.js"></script>
        <script src="app.js"></script>
      </body>
    </html>
    ''',
)

write_text(
    "dashboard/app.js",
    r'''
    (function () {
      const data = window.KOSPI_ACTIVE_DATA || { etfs: [], dates: [], holdings: [], signals: [] };
      data.etfs = data.etfs || [];
      data.dates = data.dates || [];
      data.holdings = data.holdings || [];
      data.signals = data.signals || [];
      data.growthRankings = data.growthRankings || [];
      data.candidateRankings = data.candidateRankings || [];
      data.etfExpansions = data.etfExpansions || [];
      data.commonExpandedStocks = data.commonExpandedStocks || [];

      const dateSelect = document.getElementById("dateSelect");
      const signalSelect = document.getElementById("signalSelect");
      const commonBody = document.getElementById("commonBody");
      const expansionBody = document.getElementById("expansionBody");
      const growthBody = document.getElementById("growthBody");
      const candidateBody = document.getElementById("candidateBody");
      const signalsBody = document.getElementById("signalsBody");
      const metrics = document.getElementById("metrics");
      const etfLeaders = document.getElementById("etfLeaders");
      const sourceStatusBody = document.getElementById("sourceStatusBody");
      const jobRunsBody = document.getElementById("jobRunsBody");
      const dataModeLabel = document.getElementById("dataModeLabel");
      const latestDate = document.getElementById("latestDate");
      const holdingCount = document.getElementById("holdingCount");
      const canvas = document.getElementById("trendCanvas");
      const ctx = canvas.getContext("2d");
      const colors = ["#0f766e", "#2563eb", "#b45309", "#7c3aed", "#dc2626", "#0891b2"];

      function esc(value) {
        return String(value ?? "")
          .replaceAll("&", "&amp;")
          .replaceAll("<", "&lt;")
          .replaceAll(">", "&gt;")
          .replaceAll('"', "&quot;")
          .replaceAll("'", "&#039;");
      }

      function formatPct(value) {
        const number = Number(value || 0);
        const sign = number > 0 ? "+" : "";
        return `${sign}${number.toFixed(2)}%p`;
      }

      function formatNumber(value) {
        return new Intl.NumberFormat("ko-KR").format(Math.round(Number(value || 0)));
      }

      function rowsForDate(date) {
        return data.holdings.filter((row) => row.trade_date === date);
      }

      function filteredSignals() {
        const mode = signalSelect.value;
        return data.signals.filter((signal) => {
          if (mode === "all") return true;
          if (mode === "common") return signal.signal_type.includes("5개 ETF");
          if (mode === "0.5") return signal.signal_type.includes("0.5");
          if (mode === "1.0") return signal.signal_type.includes("1.0");
          if (mode === "streak") return signal.signal_type.includes("연속");
          return true;
        });
      }

      function latestExpansionMap() {
        const map = new Map();
        data.etfExpansions.forEach((row) => map.set(`${row.trade_date}|${row.etf_code}|${row.stock_code}`, row));
        return map;
      }

      function renderMetrics(dateRows, signals) {
        const summary = data.analysisSummary || {};
        const stockCount = new Set(dateRows.map((row) => row.stock_code)).size || summary.stockCount || 0;
        const expandedRows = dateRows.filter((row) => Number(row.weight_delta || 0) > 0 && Number(row.share_delta || 0) > 0).length;
        const collectedEtfs = new Set(dateRows.map((row) => row.etf_code)).size || summary.collectedEtfCount || 0;
        const topCandidate = data.growthRankings[0]?.stock_name || data.candidateRankings[0]?.stock_name || signals[0]?.stock_name || "-";
        metrics.innerHTML = [
          ["수집 ETF", `${collectedEtfs}/${data.etfs.length}개`],
          ["보유 종목", `${stockCount}개`],
          ["ETF별 동시 확대", `${summary.etfExpansionCount ?? expandedRows}건`],
          ["최우선 후보", topCandidate],
        ]
          .map(([label, value]) => `<div class="metric"><span>${esc(label)}</span><strong>${esc(value)}</strong></div>`)
          .join("");
        holdingCount.textContent = `공통 확대 ${summary.commonExpansionCount || 0}개 · +0.5%p ${summary.threshold05Count || 0}개 · +1.0%p ${summary.threshold10Count || 0}개`;
      }

      function renderCommon() {
        const rows = data.commonExpandedStocks.slice(0, 20);
        commonBody.innerHTML = rows.length
          ? rows
              .map(
                (row) => `
            <tr>
              <td><span class="stock">${esc(row.stock_name)}</span><span class="code">${esc(row.stock_code)}</span></td>
              <td>${esc(row.etfs)}</td>
              <td class="positive">${formatPct(row.latest_weight_delta)}</td>
              <td>${formatNumber(row.latest_share_delta)}</td>
              <td>${esc(row.reason)}</td>
            </tr>`
              )
              .join("")
          : `<tr><td colspan="5">현재 최신 기준일에는 5개 ETF 모두에서 동시에 비중과 보유주식 수가 늘어난 종목이 없습니다.</td></tr>`;
      }

      function renderExpansions(dateRows) {
        const map = latestExpansionMap();
        const rows = dateRows
          .filter((row) => Number(row.weight_delta || 0) > 0 && Number(row.share_delta || 0) > 0)
          .sort((a, b) => String(a.etf_name).localeCompare(String(b.etf_name), "ko") || Number(b.weight_delta || 0) - Number(a.weight_delta || 0));
        expansionBody.innerHTML = rows.length
          ? rows
              .map((row) => {
                const info = map.get(`${row.trade_date}|${row.etf_code}|${row.stock_code}`) || {};
                return `
            <tr>
              <td><span class="stock">${esc(row.etf_name)}</span><span class="code">${esc(row.etf_code)}</span></td>
              <td><span class="stock">${esc(row.stock_name)}</span><span class="code">${esc(row.stock_code)}</span></td>
              <td>${Number(row.weight || 0).toFixed(2)}%</td>
              <td class="positive">${formatPct(row.weight_delta)}</td>
              <td>${formatNumber(row.share_delta)}</td>
              <td>${info.streak ? `${esc(info.streak)}일` : "-"}</td>
              <td>${esc(info.reason || "전 개장일 대비 비중과 보유주식 수가 함께 증가했습니다")}</td>
            </tr>`;
              })
              .join("")
          : `<tr><td colspan="7">선택 기준일에 비중과 보유주식 수가 동시에 늘어난 종목이 아직 없습니다.</td></tr>`;
      }

      function renderGrowthCandidates() {
        const rows = data.growthRankings.slice(0, 20);
        growthBody.innerHTML = rows.length
          ? rows
              .map(
                (candidate, index) => `
            <tr>
              <td>${index + 1}</td>
              <td><span class="stock">${esc(candidate.stock_name)}</span><span class="code">${esc(candidate.stock_code)}</span></td>
              <td>${Number(candidate.score || 0).toFixed(1)}</td>
              <td>${candidate.activity_etf_count || 0}개</td>
              <td>${candidate.expanded_etf_count || 0}개</td>
              <td class="${Number(candidate.latest_weight_delta || 0) >= 0 ? "positive" : "negative"}">${formatPct(candidate.latest_weight_delta)}</td>
              <td>${formatNumber(candidate.latest_share_delta || 0)}</td>
              <td>${esc(candidate.reason || "-")}</td>
            </tr>`
              )
              .join("")
          : `<tr><td colspan="8">최근 확대 강도가 확인된 국내 종목이 아직 없습니다.</td></tr>`;
      }

      function renderCandidates() {
        const rows = data.candidateRankings.slice(0, 30);
        candidateBody.innerHTML = rows.length
          ? rows
              .map(
                (candidate, index) => `
            <tr>
              <td>${index + 1}</td>
              <td><span class="stock">${esc(candidate.stock_name)}</span><span class="code">${esc(candidate.stock_code)}</span></td>
              <td>${Number(candidate.score || 0).toFixed(1)}</td>
              <td>${candidate.etf_count || 0}개</td>
              <td>${Number(candidate.latest_weight || 0).toFixed(2)}%</td>
              <td class="${Number(candidate.latest_weight_delta || 0) >= 0 ? "positive" : "negative"}">${formatPct(candidate.latest_weight_delta)}</td>
              <td>${esc(candidate.reason || "-")}</td>
              <td>${esc(candidate.watch_points || "-")}</td>
            </tr>`
              )
              .join("")
          : `<tr><td colspan="8">투자 후보 랭킹을 계산할 실제 국내 주식 데이터가 아직 없습니다.</td></tr>`;
      }

      function renderSourceStatus() {
        const statusByCode = new Map((data.etfStatus || []).map((item) => [item.etf_code, item]));
        dataModeLabel.textContent = data.dataMode === "sample" ? "샘플 데이터 표시 중" : "실제 수집 데이터 표시 중";
        sourceStatusBody.innerHTML = data.etfs
          .map((etf) => {
            const status = statusByCode.get(etf.code) || {};
            return `
            <tr>
              <td><span class="stock">${esc(etf.name)}</span><span class="code">${esc(etf.code)}</span></td>
              <td>${esc(etf.provider || "-")}</td>
              <td>${esc(status.first_date || "-")}</td>
              <td>${esc(status.latest_date || "-")}</td>
              <td>${formatNumber(status.date_count || 0)}</td>
              <td>${formatNumber(status.holding_count || 0)}</td>
            </tr>`;
          })
          .join("");
      }

      function renderJobRuns() {
        const rows = (data.jobRuns || []).slice(0, 12);
        jobRunsBody.innerHTML = rows.length
          ? rows
              .map(
                (run) => `
            <tr>
              <td>${esc(run.run_at || "-")}</td>
              <td>${esc(run.trade_date || "-")}</td>
              <td><span class="status-pill ${run.status === "failed" ? "failed" : "ok"}">${esc(run.status || "-")}</span></td>
              <td>${esc(run.message || "-")}</td>
            </tr>`
              )
              .join("")
          : `<tr><td colspan="4">수집 로그가 아직 없습니다.</td></tr>`;
      }

      function renderSignals(signals) {
        signalsBody.innerHTML = signals.length
          ? signals
              .slice(0, 40)
              .map(
                (signal) => `
            <tr>
              <td><span class="stock">${esc(signal.stock_name)}</span><span class="code">${esc(signal.stock_code)}</span></td>
              <td><span class="tag">${esc(signal.signal_type)}</span></td>
              <td>${signal.etf_count || 0}개</td>
              <td>${Number(signal.latest_weight || 0).toFixed(2)}%</td>
              <td class="${Number(signal.latest_weight_delta || 0) >= 0 ? "positive" : "negative"}">${formatPct(signal.latest_weight_delta)}</td>
              <td>${esc(signal.reason || signal.detail || "-")}</td>
            </tr>`
              )
              .join("")
          : `<tr><td colspan="6">선택한 조건에 해당하는 신호가 아직 없습니다.</td></tr>`;
      }

      function renderLeaders(dateRows) {
        etfLeaders.innerHTML = data.etfs
          .map((etf) => {
            const leaders = dateRows
              .filter((row) => row.etf_code === etf.code)
              .sort((a, b) => Number(b.weight_delta || 0) - Number(a.weight_delta || 0))
              .slice(0, 5);
            return `
            <div class="leader">
              <h3>${esc(etf.name)}</h3>
              <ol>
                ${leaders
                  .map(
                    (row) => `<li>${esc(row.stock_name)} <span class="${Number(row.weight_delta || 0) >= 0 ? "positive" : "negative"}">${formatPct(row.weight_delta)}</span></li>`
                  )
                  .join("") || "<li>데이터 없음</li>"}
              </ol>
            </div>`;
          })
          .join("");
      }

      function aggregateTrend(stockCode) {
        return data.dates.map((date) => {
          const total = data.holdings
            .filter((row) => row.trade_date === date && row.stock_code === stockCode)
            .reduce((sum, row) => sum + Number(row.weight || 0), 0);
          return { date, total };
        });
      }

      function renderTrend(signals) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        const padding = { left: 56, right: 24, top: 24, bottom: 48 };
        const source = data.commonExpandedStocks.length ? data.commonExpandedStocks : data.growthRankings.length ? data.growthRankings : signals;
        const series = source.slice(0, 5).map((item) => ({ name: item.stock_name, points: aggregateTrend(item.stock_code) }));
        if (!series.length || !data.dates.length) {
          ctx.fillStyle = "#687385";
          ctx.font = "14px Segoe UI";
          ctx.fillText("표시할 추이 데이터가 없습니다.", 24, 40);
          return;
        }
        const maxValue = Math.max(1, ...series.flatMap((item) => item.points.map((point) => point.total)));
        const xStep = (canvas.width - padding.left - padding.right) / Math.max(1, data.dates.length - 1);
        const y = (value) => canvas.height - padding.bottom - (value / maxValue) * (canvas.height - padding.top - padding.bottom);

        ctx.strokeStyle = "#dce1e7";
        ctx.lineWidth = 1;
        for (let i = 0; i <= 4; i += 1) {
          const yy = padding.top + ((canvas.height - padding.top - padding.bottom) * i) / 4;
          ctx.beginPath();
          ctx.moveTo(padding.left, yy);
          ctx.lineTo(canvas.width - padding.right, yy);
          ctx.stroke();
        }

        ctx.fillStyle = "#687385";
        ctx.font = "12px Segoe UI";
        data.dates.forEach((date, index) => {
          if (index % Math.ceil(data.dates.length / 5) === 0 || index === data.dates.length - 1) {
            ctx.fillText(date.slice(5), padding.left + index * xStep - 14, canvas.height - 18);
          }
        });

        series.forEach((item, index) => {
          ctx.strokeStyle = colors[index % colors.length];
          ctx.lineWidth = 3;
          ctx.beginPath();
          item.points.forEach((point, pointIndex) => {
            const x = padding.left + pointIndex * xStep;
            const yy = y(point.total);
            if (pointIndex === 0) ctx.moveTo(x, yy);
            else ctx.lineTo(x, yy);
          });
          ctx.stroke();
          const last = item.points[item.points.length - 1];
          ctx.fillStyle = colors[index % colors.length];
          ctx.fillText(`${item.name} ${last.total.toFixed(1)}%`, canvas.width - 190, 28 + index * 20);
        });
      }

      function render() {
        const date = dateSelect.value || data.dates[data.dates.length - 1];
        const dateRows = rowsForDate(date);
        const signals = filteredSignals();
        latestDate.textContent = `기준일 ${date || "-"}`;
        renderMetrics(dateRows, signals);
        renderCommon();
        renderExpansions(dateRows);
        renderGrowthCandidates();
        renderCandidates();
        renderSourceStatus();
        renderJobRuns();
        renderSignals(signals);
        renderLeaders(dateRows);
        renderTrend(signals.length ? signals : data.signals);
      }

      data.dates.forEach((date) => {
        const option = document.createElement("option");
        option.value = date;
        option.textContent = date;
        dateSelect.appendChild(option);
      });
      if (data.dates.length) dateSelect.value = data.analysisSummary?.latestDate || data.dates[data.dates.length - 1];
      dateSelect.addEventListener("change", render);
      signalSelect.addEventListener("change", render);
      render();
    })();
    ''',
)

write_text(
    "config/stocks.json",
    r'''
    {
      "005930": {"name": "삼성전자", "sector": "반도체/IT", "themes": ["메모리 반도체", "파운드리", "온디바이스 AI"], "watch_points": ["메모리 가격 사이클", "AI 서버 수요", "파운드리 수익성"]},
      "000660": {"name": "SK하이닉스", "sector": "반도체", "themes": ["HBM", "AI 메모리", "데이터센터"], "watch_points": ["HBM 점유율", "DRAM/NAND 가격", "CAPEX 부담"]},
      "402340": {"name": "SK스퀘어", "sector": "투자회사/반도체 지주", "themes": ["SK하이닉스 지분가치", "주주환원", "포트폴리오 재평가"], "watch_points": ["자회사 지분가치", "할인율 축소", "현금흐름"]},
      "009150": {"name": "삼성전기", "sector": "IT 부품", "themes": ["AI 서버 부품", "MLCC", "패키지기판"], "watch_points": ["MLCC 수요", "서버용 기판 매출", "스마트폰 출하"]},
      "005380": {"name": "현대차", "sector": "자동차", "themes": ["하이브리드", "전기차", "주주환원"], "watch_points": ["미국 판매", "환율", "전기차 수익성"]},
      "000270": {"name": "기아", "sector": "자동차", "themes": ["SUV", "하이브리드", "주주환원"], "watch_points": ["미국 판매", "인센티브", "전기차 수익성"]},
      "012330": {"name": "현대모비스", "sector": "자동차 부품", "themes": ["전동화 부품", "AS 부품", "자율주행"], "watch_points": ["전동화 부문 수익성", "완성차 생산량", "지배구조 변화"]},
      "028260": {"name": "삼성물산", "sector": "지주/상사/건설", "themes": ["삼성그룹 지분가치", "주주환원", "바이오/상사 포트폴리오"], "watch_points": ["NAV 할인율", "배당/자사주 정책", "건설 부문 리스크"]},
      "373220": {"name": "LG에너지솔루션", "sector": "2차전지", "themes": ["전기차 배터리", "ESS", "북미 생산"], "watch_points": ["전기차 수요", "AMPC/IRA 효과", "가동률"]},
      "006400": {"name": "삼성SDI", "sector": "2차전지", "themes": ["프리미엄 배터리", "ESS", "전고체 배터리"], "watch_points": ["전기차 수요", "고객 믹스", "신규 공장 일정"]},
      "003670": {"name": "포스코퓨처엠", "sector": "2차전지 소재", "themes": ["양극재", "음극재", "배터리 소재 내재화"], "watch_points": ["양극재 판가", "고객사 수요", "증설 부담"]},
      "329180": {"name": "HD현대중공업", "sector": "조선", "themes": ["LNG선", "방산", "선가 상승"], "watch_points": ["신조선가", "수주잔고", "원가/환율"]},
      "042660": {"name": "한화오션", "sector": "조선", "themes": ["LNG선", "방산/특수선", "해양플랜트"], "watch_points": ["수주 마진", "흑자 전환 지속성", "방산 수주"]},
      "010140": {"name": "삼성중공업", "sector": "조선", "themes": ["LNG선", "해양플랜트", "선가 상승"], "watch_points": ["수주 마진", "공정 안정성", "환율"]},
      "298040": {"name": "효성중공업", "sector": "전력기기", "themes": ["전력망 투자", "AI 데이터센터", "변압기"], "watch_points": ["북미 전력망 투자", "수주잔고", "증설 일정"]},
      "267260": {"name": "HD현대일렉트릭", "sector": "전력기기", "themes": ["변압기", "전력망 투자", "데이터센터"], "watch_points": ["북미 수주", "마진 지속성", "증설 일정"]},
      "062040": {"name": "산일전기", "sector": "전력기기", "themes": ["변압기", "전력망 투자", "데이터센터"], "watch_points": ["수주잔고", "증설 효과", "원재료 가격"]},
      "006260": {"name": "LS", "sector": "전력/전선 지주", "themes": ["전력 인프라", "전선", "구리 가격"], "watch_points": ["전력망 투자", "구리 가격", "자회사 수주"]},
      "000150": {"name": "두산", "sector": "지주/기계", "themes": ["전력기기", "로보틱스", "원전/에너지"], "watch_points": ["자회사 가치", "수주 지속성", "재무구조"]},
      "034020": {"name": "두산에너빌리티", "sector": "에너지/기계", "themes": ["원전", "가스터빈", "전력 인프라"], "watch_points": ["원전 수주", "수익성 개선", "부채 부담"]},
      "012450": {"name": "한화에어로스페이스", "sector": "방산/항공", "themes": ["방산 수출", "항공엔진", "우주"], "watch_points": ["수출 계약", "납품 일정", "마진율"]},
      "064350": {"name": "현대로템", "sector": "방산/철도", "themes": ["방산 수출", "철도", "K2 전차"], "watch_points": ["방산 계약", "철도 수익성", "수주잔고"]},
      "034730": {"name": "SK", "sector": "지주", "themes": ["반도체 지분가치", "바이오/에너지 포트폴리오", "주주환원"], "watch_points": ["자회사 실적", "재무구조", "지주사 할인율"]},
      "003550": {"name": "LG", "sector": "지주", "themes": ["자회사 지분가치", "배당", "포트폴리오 재편"], "watch_points": ["자회사 실적", "NAV 할인율", "주주환원"]},
      "011070": {"name": "LG이노텍", "sector": "IT 부품", "themes": ["스마트폰 카메라", "전장부품", "AI 디바이스"], "watch_points": ["주요 고객사 출하", "카메라 모듈 믹스", "전장 수익성"]},
      "066570": {"name": "LG전자", "sector": "가전/전장", "themes": ["전장부품", "프리미엄 가전", "로봇/플랫폼"], "watch_points": ["전장 수주잔고", "가전 마진", "수요 회복"]},
      "005490": {"name": "POSCO홀딩스", "sector": "철강/소재", "themes": ["철강", "리튬", "2차전지 소재"], "watch_points": ["철강 스프레드", "리튬 가격", "소재 투자 회수"]},
      "010130": {"name": "고려아연", "sector": "비철금속", "themes": ["아연/귀금속", "신재생", "주주가치"], "watch_points": ["금속 가격", "지배구조 이슈", "신사업 투자"]},
      "017670": {"name": "SK텔레콤", "sector": "통신", "themes": ["AI 데이터센터", "통신 배당", "엔터프라이즈 AI"], "watch_points": ["배당 지속성", "AI 투자 성과", "규제 환경"]},
      "105560": {"name": "KB금융", "sector": "금융지주", "themes": ["주주환원", "대출 이익", "밸류업"], "watch_points": ["순이자마진", "자사주/배당", "대손비용"]},
      "055550": {"name": "신한지주", "sector": "금융지주", "themes": ["주주환원", "밸류업", "은행/비은행 포트폴리오"], "watch_points": ["순이자마진", "대손비용", "자본정책"]},
      "086790": {"name": "하나금융지주", "sector": "금융지주", "themes": ["주주환원", "환율 민감도", "밸류업"], "watch_points": ["순이자마진", "외환 민감도", "자본정책"]},
      "032830": {"name": "삼성생명", "sector": "보험", "themes": ["금리 민감주", "주주환원", "삼성그룹 지분가치"], "watch_points": ["금리 변화", "회계 이익 변동성", "배당정책"]},
      "000810": {"name": "삼성화재", "sector": "보험", "themes": ["손해보험", "주주환원", "밸류업"], "watch_points": ["자동차/장기보험 손해율", "금리", "자본정책"]},
      "001450": {"name": "현대해상", "sector": "보험", "themes": ["손해보험", "배당/자사주", "밸류업"], "watch_points": ["보험 손해율", "금리와 투자이익", "주주환원 정책"]},
      "035420": {"name": "NAVER", "sector": "인터넷 플랫폼", "themes": ["검색 광고", "커머스", "AI"], "watch_points": ["광고 경기", "커머스 성장", "AI 투자비"]},
      "207940": {"name": "삼성바이오로직스", "sector": "바이오", "themes": ["CDMO", "바이오 의약품", "증설"], "watch_points": ["수주잔고", "가동률", "환율"]},
      "259960": {"name": "크래프톤", "sector": "게임", "themes": ["글로벌 게임", "신작", "AI 제작 효율"], "watch_points": ["PUBG 매출", "신작 성과", "마케팅비"]},
      "096770": {"name": "SK이노베이션", "sector": "에너지/배터리", "themes": ["정유", "배터리", "석유화학"], "watch_points": ["정제마진", "배터리 손익", "재무 부담"]}
    }
    ''',
)

print("Applied KOSPI Active dashboard runtime fixes.")
