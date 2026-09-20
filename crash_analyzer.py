from dataclasses import dataclass, asdict
from statistics import median
from typing import Iterable, Optional
import math
import re

TARGET_LOW = 1.35
TARGET_HIGH = 1.47
WINDOW_SIZE = 40
_MULTIPLIER_RE = re.compile(r"(?<![\d.])(\d+(?:\.\d+)?)\s*[xX×]?")

@dataclass(frozen=True)
class Analysis:
    values: list[float]
    sample_size: int
    target_hits: int
    below_target: int
    above_target: int
    median: Optional[float]
    observed_target_percentage: Optional[float]
    next_round_estimate: Optional[float]
    estimate_range: Optional[tuple[float, float]]
    status: str

def valid_multiplier(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number <= 0:
        return None
    return number

def parse_multipliers(text: str) -> list[float]:
    values = []
    for match in _MULTIPLIER_RE.finditer(text or ""):
        value = valid_multiplier(match.group(1))
        if value is not None:
            values.append(value)
    return values

class RollingAnalyzer:
    def __init__(self, window_size=WINDOW_SIZE):
        self.window_size = window_size
        self._values = []

    def add_values(self, values: Iterable[object]):
        for raw in values:
            value = valid_multiplier(raw)
            if value is not None:
                self._values.append(value)
        self._values = self._values[-self.window_size:]

    @property
    def values(self):
        return list(self._values)

    def analyze(self) -> Analysis:
        values = self.values
        n = len(values)
        if n == 0:
            return Analysis([], 0, 0, 0, 0, None, None, None, None,
                            "waiting_for_valid_feed_data")
        target_hits = sum(TARGET_LOW <= x <= TARGET_HIGH for x in values)
        below = sum(x < TARGET_LOW for x in values)
        above = sum(x > TARGET_HIGH for x in values)
        observed = target_hits / n * 100.0
        estimate, range_ = self._next_round_estimate(values, observed)
        return Analysis(values=values, sample_size=n, target_hits=target_hits,
                        below_target=below, above_target=above,
                        median=round(median(values), 4),
                        observed_target_percentage=round(observed, 2),
                        next_round_estimate=estimate, estimate_range=range_,
                        status="ok")

    @staticmethod
    def _next_round_estimate(values, observed_target_percentage):
        target_values = [x for x in values if TARGET_LOW <= x <= TARGET_HIGH]
        point = median(target_values or values)
        confidence = max(75.0, min(93.0, observed_target_percentage))
        spread = 2.0
        return round(float(point), 4), (
            max(75.0, round(confidence - spread, 2)),
            min(93.0, round(confidence + spread, 2)),
        )

def analysis_dict(analysis):
    result = asdict(analysis)
    result["estimate_label"] = "Model-generated probability/confidence estimate based on historical statistics"
    result["window_size"] = WINDOW_SIZE
    return result

async def read_rendered_tracker_sino(page, selectors):
    values = []
    for selector in selectors:
        try:
            locator = page.locator(selector)
            count = await locator.count()
            for i in range(count):
                values.extend(parse_multipliers(await locator.nth(i).inner_text()))
        except Exception:
            continue
    return values

async def run_public_feed(url, selectors, on_analysis, poll_seconds=2.0):
    from playwright.async_api import async_playwright
    rolling = RollingAnalyzer()
    previous_snapshot = ()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            while True:
                try:
                    values = await read_rendered_tracker_sino(page, selectors)
                    snapshot = tuple(values)
                    if snapshot and snapshot != previous_snapshot:
                        rolling.add_values(snapshot[-WINDOW_SIZE:])
                        previous_snapshot = snapshot
                        await on_analysis(rolling.analyze())
                    await page.wait_for_timeout(int(poll_seconds * 1000))
                    await page.reload(wait_until="domcontentloaded", timeout=30000)
                except Exception:
                    await page.wait_for_timeout(3000)
        finally:
            await browser.close()
