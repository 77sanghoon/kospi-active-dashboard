from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

index_path = ROOT / "dashboard" / "index.html"
index = index_path.read_text(encoding="utf-8")

cache_marker = "kospi-cache-runtime-fix"
cache_script = r'''
    <!-- kospi-cache-runtime-fix -->
    <meta http-equiv="Cache-Control" content="no-store, no-cache, must-revalidate, max-age=0" />
    <meta http-equiv="Pragma" content="no-cache" />
    <meta http-equiv="Expires" content="0" />
    <script>
      (function () {
        var refreshParam = "_refresh";
        var guardKey = "kospi-active-refresh-token";
        var url = new URL(window.location.href);
        var params = url.searchParams;
        var token = params.get(refreshParam);
        window.__KOSPI_ASSET_VERSION__ = token || String(Date.now());

        function cleanVisibleUrl() {
          if (!token || !window.history || !window.history.replaceState) return;
          var cleanUrl = new URL(window.location.href);
          cleanUrl.searchParams.delete(refreshParam);
          window.history.replaceState(null, "", cleanUrl.pathname + cleanUrl.search + cleanUrl.hash);
        }

        function clearCaches() {
          var tasks = [];
          if (window.caches && caches.keys) {
            tasks.push(
              caches.keys().then(function (keys) {
                return Promise.all(keys.map(function (key) { return caches.delete(key); }));
              }).catch(function () {})
            );
          }
          if (navigator.serviceWorker && navigator.serviceWorker.getRegistrations) {
            tasks.push(
              navigator.serviceWorker.getRegistrations().then(function (registrations) {
                return Promise.all(registrations.map(function (registration) { return registration.unregister(); }));
              }).catch(function () {})
            );
          }
          return Promise.all(tasks);
        }

        function hardReload() {
          var nextToken = String(Date.now());
          try { sessionStorage.setItem(guardKey, nextToken); } catch (error) {}
          var nextUrl = new URL(window.location.href);
          nextUrl.searchParams.set(refreshParam, nextToken);
          return clearCaches().finally(function () {
            window.location.replace(nextUrl.toString());
          });
        }

        window.KOSPI_ACTIVE_FORCE_RELOAD = hardReload;

        var navigation = performance.getEntriesByType ? performance.getEntriesByType("navigation")[0] : null;
        var isReload = navigation ? navigation.type === "reload" : Boolean(performance.navigation && performance.navigation.type === 1);

        if (token) {
          try {
            if (sessionStorage.getItem(guardKey) === token) sessionStorage.removeItem(guardKey);
          } catch (error) {}
          cleanVisibleUrl();
          return;
        }

        if (isReload) hardReload();

        document.addEventListener("DOMContentLoaded", function () {
          var button = document.getElementById("hardRefreshButton");
          if (button) {
            button.addEventListener("click", function () {
              button.disabled = true;
              button.textContent = "새로 불러오는 중";
              hardReload();
            });
          }
        });
      })();
    </script>
    <script>
      document.write('<link rel="stylesheet" href="styles.css?v=' + encodeURIComponent(window.__KOSPI_ASSET_VERSION__ || Date.now()) + '" />');
    </script>
'''.rstrip()

if cache_marker not in index:
    index = index.replace('    <link rel="stylesheet" href="styles.css" />', cache_script)

if 'id="hardRefreshButton"' not in index:
    index = index.replace(
        '        <span id="holdingCount">-</span>\n      </div>',
        '        <span id="holdingCount">-</span>\n        <button id="hardRefreshButton" class="refresh-button" type="button">최신 데이터 새로고침</button>\n      </div>',
    )

static_scripts = '    <script src="data.js"></script>\n    <script src="app.js"></script>'
dynamic_scripts = r'''    <script>
      (function () {
        var version = encodeURIComponent(window.__KOSPI_ASSET_VERSION__ || Date.now());
        document.write('<script src="data.js?v=' + version + '"><\/script>');
        document.write('<script src="app.js?v=' + version + '"><\/script>');
      })();
    </script>'''
if static_scripts in index:
    index = index.replace(static_scripts, dynamic_scripts)

index_path.write_text(index, encoding="utf-8")

styles_path = ROOT / "dashboard" / "styles.css"
styles = styles_path.read_text(encoding="utf-8")
style_marker = "/* cache-refresh-button-runtime-fix */"
style_patch = r'''
/* cache-refresh-button-runtime-fix */
.refresh-button {
  min-height: 34px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #111827;
  color: #ffffff;
  padding: 0 12px;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
}

.refresh-button:disabled {
  cursor: progress;
  opacity: 0.72;
}

.refresh-button:hover:not(:disabled) {
  background: #0f766e;
}

@media (max-width: 720px) {
  .refresh-button {
    width: 100%;
    min-height: 38px;
    font-size: 13px;
  }
}
'''.strip()
if style_marker not in styles:
    styles = styles.rstrip() + "\n\n" + style_patch + "\n"
styles_path.write_text(styles, encoding="utf-8")

print("Applied cache reload and asset cache-busting fixes.")
