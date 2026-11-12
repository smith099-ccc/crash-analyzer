import json
import re

from kivy.clock import Clock
from kivy.utils import platform

TRACKER_URL = "https://trackersino.com/games/stake-crash"
_MULTIPLIER_RE = re.compile(r"(?<![\d.])(\d+(?:\\.\d+)?)\s*[xX×]")


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

            owner = self

            class ValueCallback(PythonJavaClass):
                __javainterfaces__ = ["android/webkit/ValueCallback"]
                __javacontext__ = "app"

                @java_method("(Ljava/lang/String;)V")
                def onReceiveValue(self, value):
                    owner._handle_js_result(value)

            self._callback_class = ValueCallback
            self.webview.loadUrl(TRACKER_URL)
            self.on_status("Opening TrackerSino public Stake Crash page…")
            self.poll_event = Clock.schedule_interval(self._poll, 2.0)
        except Exception as exc:
            self.on_status("Live feed unavailable: " + str(exc))

    def _poll(self, *_):
        if not self.webview:
            return
        try:
            # The current page heading has a suffix ("· last 120"). Find it
            # by prefix and inspect its ancestors, not only its immediate parent.
            script = r"""
            (function () {
                const norm = s => (s || "").replace(/\s+/g, " ").trim();
                const headings = Array.from(document.querySelectorAll("h1,h2,h3,h4"));
                const heading = headings.find(el =>
                    norm(el.innerText).toLowerCase().startsWith("recent crash points")
                );
                if (!heading) {
                    return JSON.stringify({
                        section: "",
                        page: norm(document.body ? document.body.innerText : "")
                    });
                }
                let node = heading;
                let best = node.innerText || "";
                for (let i = 0; i < 5 && node; i++, node = node.parentElement) {
                    const text = node.innerText || "";
                    if (text.length > best.length) best = text;
                    if ((text.match(/\d+(?:\\.\d+)?\s*[xX×]/g) || []).length >= 1) {
                        best = text;
                        break;
                    }
                }
                return JSON.stringify({
                    section: best,
                    page: norm(document.body ? document.body.innerText : "")
                });
            })();
            """
            self.callback = self._callback_class()
            self.webview.evaluateJavascript(script, self.callback)
        except Exception as exc:
            self.on_status("Feed check failed: " + str(exc))

    def _handle_js_result(self, raw):
        try:
            decoded = json.loads(str(raw)) if raw is not None else ""
            payload = json.loads(decoded) if isinstance(decoded, str) else decoded
        except Exception:
            payload = {"section": str(raw or ""), "page": str(raw or "")}

        if isinstance(payload, dict):
            section = payload.get("section", "")
            page = payload.get("page", "")
        else:
            section = str(payload or "")
            page = section

        values = parse_rendered_multipliers(section)
        if not values:
            page_lower = (page or "").lower()
            if "connecting" in page_lower or "loading…" in page_lower or "loading..." in page_lower:
                self.on_status("TrackerSino page opened, but its public Stake Crash feed is still connecting/loading.")
            elif "stale" in page_lower or "offline" in page_lower:
                self.on_status("TrackerSino reports its Stake Crash feed is stale or offline. Waiting for source recovery.")
            elif "recent crash points" not in (section or "").lower():
                self.on_status("TrackerSino page opened; recent crash-points section was not found.")
            else:
                self.on_status("TrackerSino results section found, but it currently contains no readable multipliers.")
            return

        snapshot = tuple(values[:120])
        if snapshot == self.previous_snapshot:
            return
        self.previous_snapshot = snapshot
        self.on_status(f"Live feed connected — {len(snapshot)} rendered round(s) found.")
        self.on_values(list(snapshot))

    def reset_snapshot(self):
        self.previous_snapshot = ()

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
