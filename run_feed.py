import asyncio
import json
from crash_analyzer import analysis_dict, run_public_feed

URL = "https://trackersino.com/games/stake-crash"
SELECTORS = [
    ".crash-point",
    "[data-testid='crash-point']",
    "[class*='crash']",
]

async def display(analysis):
    print(json.dumps(analysis_dict(analysis), indent=2))

async def main():
    await run_public_feed(URL, SELECTORS, display, poll_seconds=2.0)

if __name__ == "__main__":
    asyncio.run(main())
