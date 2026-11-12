from statistics import mean, median
import random


def analyze(values):
    values = [float(v) for v in values if v is not None and float(v) >= 1.0]
    n = len(values)
    if not n:
        return {
            "n": 0, "mean": "N/A", "median": "N/A",
            "minimum": "N/A", "maximum": "N/A",
            "below_2_pct": "N/A", "at_or_above_2_pct": "N/A",
            "under_2_count": 0,
        }
    under = sum(v < 2.0 for v in values)
    return {
        "n": n,
        "mean": f"{mean(values):.2f}x",
        "median": f"{median(values):.2f}x",
        "minimum": f"{min(values):.2f}x",
        "maximum": f"{max(values):.2f}x",
        "below_2_pct": f"{under / n * 100:.1f}%",
        "at_or_above_2_pct": f"{(n - under) / n * 100:.1f}%",
        "under_2_count": under,
    }


def simulate(values, trials=1000, seed=None):
    values = [float(v) for v in values if v is not None and float(v) >= 1.0]
    if len(values) < 5:
        return None
    rng = random.Random(seed)
    draws = sorted(rng.choice(values) for _ in range(max(1, trials)))
    def percentile(p):
        index = round((len(draws) - 1) * p)
        return draws[index]
    return {
        "median": percentile(0.50),
        "p10": percentile(0.10),
        "p90": percentile(0.90),
    }
