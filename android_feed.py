import json
import re

from kivy.clock import Clock
from kivy.utils import platform

TRACKER_URL = "https://trackersino.com/games/stake-crash"
_MULTIPLIER_RE = re.compile(r"(?<![\d.])(\d+(?:\.\d+)?)\s*[xX×]")


def parse_rendered_multipliers(text):
    values = []
    for match in _MULTIPLIER_RE.finditer(text or ""):
        try:
            value = float(match.group(1))
            if value > 0:
                values.append(value)
        except (TypeError, ValueError):
            pass
    return values


class AndroidPublicFeed:
    def __init__(self, on_values, on_status):
        self.on_values = on_values
        self.on_status = on_status
        self.webview = None
        self.callback = None
        self.poll_event = None
        self.previous_snapshot = ()

    def start(self):
        if platform != "android":
            self.on_status("Live feed is available in the Android APK.")
            return
        try:
            from jnius import autoclass, PythonJavaClass, java_method
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            WebView = autoclass("android.webkit.WebView")
            WebViewClient = autoclass("android.webkit.WebViewClient")
            LayoutParams = autoclass("android.view.ViewGroup$LayoutParams")

            activity = PythonActivity.mActivity
            self.webview = WebView(activity)
            settings = self.webview.getSettings()
            settings.setJavaScriptEnabled(True)
            settings.setDomStorageEnabled(True)
            settings.setDatabaseEnabled(True)
            settings.setLoadsImagesAutomatically(False)
            settings.setBlockNetworkImage(True)
            self.webview.setWebViewClient(WebViewClient())
            activity.addContentView(self.webview, LayoutParams(1, 1))
            self.webview.loadUrl(TRACKER_URL)

            self.on_status("Connecting to public TrackerSino page…")
            self.poll_event = Clock.schedule_interval(self._poll, 2.0)

            owner = self

            class ValueCallback(PythonJavaClass):
                __javainterfaces__ = ["android/webkit/ValueCallback"]
                __javacontext__ = "app"

                @java_method("(Ljava/lang/String;)V")
                def onReceiveValue(self, value):
                    owner._handle_js_result(value)

            self._callback_class = ValueCallback
        except Exception as exc:
            self.on_status("Live feed unavailable: " + str(exc))

    def _poll(self, *_):
        if not self.webview:
            return
        try:
            script = r"""
            (function () {
                const els = Array.from(document.querySelectorAll("h2,h3,h4,div,section"));
                const heading = els.find(el =>
                    (el.innerText || "").trim().startsWith("Recent crash points")
                );
                if (!heading || !heading.parentElement) return "";
                return heading.parentElement.innerText || "";
            })();
            """
            self.callback = self._callback_class()
            self.webview.evaluateJavascript(script, self.callback)
        except Exception:
            self.on_status("Waiting for rendered feed…")

    def _handle_js_result(self, raw):
        try:
            text = json.loads(str(raw)) if raw is not None else ""
        except Exception:
            text = str(raw or "")
        values = parse_rendered_multipliers(text)
        if not values:
            self.on_status("Waiting for new public Stake Crash rounds…")
            return
        snapshot = tuple(values[:120])
        if snapshot == self.previous_snapshot:
            return
        self.previous_snapshot = snapshot
        self.on_status(f"Live feed connected — {len(snapshot)} rendered round(s) found.")
        self.on_values(list(snapshot))

    def stop(self):
        if self.poll_event:
            self.poll_event.cancel()
            self.poll_event = None
        if self.webview:
            try:
                self.webview.stopLoading()
                self.webview.destroy()
            except Exception:
                pass
            self.webview = None
