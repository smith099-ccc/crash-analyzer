from kivy.app import App
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from crash_analyzer import RollingAnalyzer, TARGET_LOW, TARGET_HIGH

class CrashAnalyzerUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(12), spacing=dp(8), **kwargs)
        self.analyzer = RollingAnalyzer()

        title = Label(text="[b]Crash Analyzer[/b]", markup=True,
                      font_size=dp(24), size_hint_y=None, height=dp(42))
        self.add_widget(title)

        self.status = Label(text="Ready — add multiplier results below.",
                            size_hint_y=None, height=dp(32))
        self.add_widget(self.status)

        self.input = TextInput(
            hint_text="Paste multipliers, e.g. 1.42x 2.15x 1.09x",
            multiline=True, size_hint_y=None, height=dp(90))
        self.add_widget(self.input)

        buttons = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        analyze = Button(text="Analyze")
        analyze.bind(on_press=self.add_values)
        clear = Button(text="Clear")
        clear.bind(on_press=self.clear_values)
        buttons.add_widget(analyze)
        buttons.add_widget(clear)
        self.add_widget(buttons)

        scroll = ScrollView()
        self.output = Label(text="", markup=True, halign="left",
                            valign="top", size_hint_y=None)
        self.output.bind(texture_size=self._resize_output)
        scroll.add_widget(self.output)
        self.add_widget(scroll)
        self.render()

    def _resize_output(self, *_):
        self.output.height = self.output.texture_size[1]
        self.output.text_size = (self.width - dp(24), None)

    def add_values(self, *_):
        from crash_analyzer import parse_multipliers
        values = parse_multipliers(self.input.text)
        if not values:
            self.status.text = "No valid multipliers found."
            return
        self.analyzer.add_values(values)
        self.input.text = ""
        self.status.text = f"Added {len(values)} valid value(s). Latest 40 retained."
        self.render()

    def clear_values(self, *_):
        self.analyzer = RollingAnalyzer()
        self.status.text = "Cleared."
        self.render()

    def render(self):
        a = self.analyzer.analyze()
        if a.sample_size == 0:
            self.output.text = "[b]Dashboard[/b]\n\nSample size: 0\n\nWaiting for valid multiplier data."
            return
        rng = f"{a.estimate_range[0]:.0f}%–{a.estimate_range[1]:.0f}%" if a.estimate_range else "N/A"
        values = "  ".join(f"{x:.2f}x" for x in a.values)
        self.output.text = (
            "[b]Dashboard[/b]\n\n"
            f"Latest valid values: {a.sample_size}/{self.analyzer.window_size}\n"
            f"Target: {TARGET_LOW:.2f}x–{TARGET_HIGH:.2f}x\n\n"
            f"Target hits: {a.target_hits}\n"
            f"Below {TARGET_LOW:.2f}x: {a.below_target}\n"
            f"Above {TARGET_HIGH:.2f}x: {a.above_target}\n"
            f"Median: {a.median:.4f}x\n"
            f"Observed target-range percentage: {a.observed_target_percentage:.2f}%\n\n"
            "[b]Model-generated probability/confidence estimate[/b]\n"
            f"Based on historical statistics: {rng}\n"
            f"Point estimate: {a.next_round_estimate:.4f}x\n\n"
            "[b]Latest 40 valid multipliers[/b]\n"
            f"{values}\n\n"
            "[i]This is a model-generated estimate based on the current historical "
            "window, not a guarantee or measured next-round accuracy.[/i]"
        )

class CrashAnalyzerApp(App):
    title = "Crash Analyzer"
    def build(self):
        return CrashAnalyzerUI()

if __name__ == "__main__":
    CrashAnalyzerApp().run()
