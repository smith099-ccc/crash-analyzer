import json
import re
import webbrowser
from datetime import datetime
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from sportyjet_stats import analyze, simulate


DATA_FILE = Path("sportyjet_results.json")
SPORTYJET_URL = "https://www.sportybet.com/ng/games/sporty-jet"


def parse_results(text):
    cleaned = text.lower().replace("×", "x")
    matches = re.findall(r"(?<![\w.])(\d+(?:\.\d+)?)\s*x?", cleaned)
    values = []
    for item in matches:
        try:
            value = float(item)
            if 1.0 <= value <= 100000:
                values.append(value)
        except ValueError:
            continue
    return values


class SportyJetUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(10), spacing=dp(7), **kwargs)
        self.results = self.load_results()

        self.add_widget(Label(text="[b]SportyJet Analyzer[/b]", markup=True,
                              font_size=dp(23), size_hint_y=None, height=dp(42)))
        self.status = Label(
            text="Results are stored locally. Add verified results from the official game page.",
            size_hint_y=None, height=dp(42))
        self.add_widget(self.status)

        self.entry = TextInput(
            hint_text="Paste recent results, e.g. 1.24x 2.10x 1.05x",
            multiline=True, size_hint_y=None, height=dp(76))
        self.add_widget(self.entry)

        controls = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
        for label, callback in [
            ("Add results", self.add_results),
            ("Analyze", self.refresh),
            ("Simulate 1,000", self.run_simulation),
            ("Open SportyJet", self.open_game),
        ]:
            btn = Button(text=label, font_size=dp(12))
            btn.bind(on_press=callback)
            controls.add_widget(btn)
        self.add_widget(controls)

        scroll = ScrollView()
        self.output = Label(text="", markup=True, halign="left", valign="top",
                            size_hint_y=None)
        self.output.bind(texture_size=self.resize_output)
        scroll.add_widget(self.output)
        self.add_widget(scroll)
        self.refresh()

    def load_results(self):
        try:
            raw = json.loads(DATA_FILE.read_text())
            return raw if isinstance(raw, list) else []
        except (OSError, ValueError):
            return []

    def save_results(self):
        DATA_FILE.write_text(json.dumps(self.results[-5000:], indent=2))

    def add_results(self, *_):
        values = parse_results(self.entry.text)
        if not values:
            self.status.text = "No valid multipliers found. Include values such as 1.42x."
            return
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        # Pasted results are expected newest-first; store them with timestamps.
        for value in reversed(values):
            self.results.append({"value": value, "captured_at": now, "source": "user-import"})
        self.results = self.results[-5000:]
        self.save_results()
        self.entry.text = ""
        self.status.text = f"Saved {len(values)} results. Source: manual import."
        self.refresh()

    def refresh(self, *_):
        values = [float(item["value"]) for item in self.results if "value" in item]
        stats = analyze(values)
        recent = list(reversed(self.results[-50:]))
        lines = [
            "[b]RESULTS FEED[/b]",
            "Source: manually imported / locally saved",
            f"Stored results: {len(values)}",
            "",
            "[b]MOST RECENT RESULTS (up to 50)[/b]",
        ]
        if recent:
            for i, item in enumerate(recent, 1):
                stamp = item.get("captured_at", "timestamp unavailable")
                lines.append(f"{i:02d}. [b]{float(item['value']):.2f}x[/b]  [size=10sp]{stamp}[/size]")
        else:
            lines.append("No results recorded yet. Open SportyJet and paste its displayed results above.")
        lines += [
            "",
            "[b]STATISTICAL SUMMARY[/b]",
            f"Sample size: {stats['n']}",
            f"Mean: {stats['mean']}",
            f"Median: {stats['median']}",
            f"Minimum / maximum: {stats['minimum']} / {stats['maximum']}",
            f"Below 2.00x: {stats['below_2_pct']}",
            f"2.00x or above: {stats['at_or_above_2_pct']}",
            f"Empirical 1.00x–1.99x frequency: {stats['under_2_count']}/{stats['n']}",
            "",
            "[i]Historical frequencies describe this sample only. They do not establish the next round's outcome.[/i]",
            "",
            "[b]FEED STATUS[/b]",
            "Automatic live extraction: not yet enabled.",
            "The official SportyJet page is linked below; the app will only label results live after a public results feed is verified."
        ]
        self.output.text = "\n".join(lines)
        self.resize_output()

    def run_simulation(self, *_):
        values = [float(item["value"]) for item in self.results if "value" in item]
        result = simulate(values, 1000)
        if result is None:
            self.status.text = "Add at least 5 verified results before running a historical resampling simulation."
        else:
            self.status.text = (
                f"1,000 resampled trials: median {result['median']:.2f}x; "
                f"10th–90th percentile {result['p10']:.2f}x–{result['p90']:.2f}x. "
                "Simulation only, not a next-round prediction."
            )

    def open_game(self, *_):
        webbrowser.open(SPORTYJET_URL)
        self.status.text = "Opened the official SportyJet page. Import only results you can verify there."

    def resize_output(self, *_):
        self.output.text_size = (max(100, self.width - dp(24)), None)
        self.output.height = self.output.texture_size[1] + dp(12)


class SportyJetAnalyzerApp(App):
    title = "SportyJet Analyzer"

    def build(self):
        return SportyJetUI()


if __name__ == "__main__":
    SportyJetAnalyzerApp().run()
