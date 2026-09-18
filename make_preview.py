#!/usr/bin/env python3
"""Generate a self-contained mock of github.com/ritheareach for previewing the design.

Outputs preview/profile-preview.html with hero SVGs and avatar inlined as data URIs,
so it works standalone in any sandboxed preview frame.
"""
import base64
import json
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "preview" / "profile-preview.html"
AVATAR_CACHE = ROOT / ".build" / "avatar.jpg"


def data_uri(path: Path, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def main() -> None:
    readme = (ROOT / "README.md").read_text()

    # markdown -> html (raw HTML blocks pass through)
    body = markdown.markdown(readme, extensions=["tables", "fenced_code", "sane_lists", "md_in_html"])

    dark = data_uri(ROOT / "assets" / "hero-landscape-v2-dark.svg", "image/svg+xml")
    light = data_uri(ROOT / "assets" / "hero-landscape-v2-light.svg", "image/svg+xml")
    avatar = data_uri(AVATAR_CACHE, "image/jpeg") if AVATAR_CACHE.exists() else ""

    # swap repo-relative asset paths for the inlined originals
    body = body.replace("assets/hero-dark.svg", dark).replace("assets/hero-light.svg", light)
    body = re.sub(r'width="100%"', 'width="100%" class="hero-img"', body)

    html = TEMPLATE.replace("__AVATAR__", avatar).replace("__BODY__", body)
    html = html.replace("__DARK__", dark).replace("__LIGHT__", light)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html)
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")


TEMPLATE = r"""<!doctype html>
<html data-theme="dark">
<head>
<meta charset="utf-8">
<title>github.com/ritheareach — preview</title>
<style>
  :root { color-scheme: light dark; }
  html[data-theme="dark"] { --bg:#0d1117; --fg:#e6edf3; --muted:#8b949e; --border:#30363d; --card:#161b22; --link:#4493f8; --btn:#21262d; }
  html[data-theme="light"] { --bg:#ffffff; --fg:#1f2328; --muted:#59636e; --border:#d1d9e0; --card:#ffffff; --link:#0969da; --btn:#f6f8fa; }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--fg);
    font: 14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans",Helvetica,Arial,sans-serif; }
  .topbar { display:flex; align-items:center; gap:12px; padding:12px 16px; border-bottom:1px solid var(--border); }
  .logo { width:26px; height:26px; border-radius:50%; border:1.5px solid var(--muted); }
  .search { flex:0 0 260px; padding:5px 10px; border:1px solid var(--border); border-radius:6px; color:var(--muted); background:var(--bg); font-size:12px; }
  .toggle { margin-left:auto; display:flex; gap:6px; }
  .toggle button { font-size:11px; padding:4px 10px; border-radius:6px; border:1px solid var(--border); background:var(--btn); color:var(--fg); cursor:pointer; }
  .toggle button.on { border-color:var(--link); color:var(--link); }
  .wrap { max-width:1012px; margin:0 auto; padding:24px 16px 40px; }
  .profile { display:flex; gap:20px; align-items:flex-start; padding-bottom:18px; border-bottom:1px solid var(--border); }
  .avatar { width:180px; height:180px; border-radius:50%; border:1px solid var(--border); flex:0 0 auto; }
  h1.name { font-size:26px; margin:6px 0 2px; font-weight:600; }
  .handle { font-size:20px; color:var(--muted); font-weight:300; }
  .bio { margin:10px 0 0; }
  .meta { color:var(--muted); margin-top:8px; display:flex; flex-wrap:wrap; gap:14px; font-size:13px; }
  .readme { margin-top:26px; }
  .readme h3 { font-size:16px; font-weight:600; margin:28px 0 10px; padding-bottom:6px; border-bottom:1px solid var(--border); }
  .readme h3 samp { font-family: ui-monospace,SFMono-Regular,Menlo,monospace; font-weight:600; letter-spacing:0.4px; }
  .readme p { margin:10px 0; }
  .readme ul { padding-left:24px; margin:10px 0; }
  .readme li { margin:6px 0; }
  .readme a { color:var(--link); text-decoration:none; }
  .readme a:hover { text-decoration:underline; }
  .hero-img { display:block; border-radius:8px; width:100%; }
  picture { display:block; margin:4px 0 18px; }
  .tag { color:var(--muted); font-size:12px; margin-top:34px; padding-top:12px; border-top:1px solid var(--border); }
</style>
</head>
<body>
  <div class="topbar">
    <div class="logo"></div>
    <div class="search">Type / to search</div>
    <div class="toggle">
      <button id="bd">Dark</button><button id="bl">Light</button>
    </div>
  </div>
  <div class="wrap">
    <div class="profile">
      <img class="avatar" src="__AVATAR__" alt="avatar">
      <div>
        <h1 class="name">Ritheareach CHAN <span class="handle">ritheareach</span></h1>
        <p class="bio">Senior AI Engineer — AI software &amp; solutions: computer vision, AI agents, LLM-driven automation. AI Farm Robotics.</p>
        <div class="meta">
          <span>📍 Phnom Penh</span><span>🏢 AI Farm Robotics</span><span>🔗 aifarm.dev</span>
          <span><b>10</b> repositories</span>
        </div>
      </div>
    </div>
    <div class="readme">
__BODY__
    </div>
    <div class="tag">Local mock of github.com/ritheareach — hero renders with prefers-color-scheme, same markup as the real README.</div>
  </div>
<script>
  var DARK = "__DARK__", LIGHT = "__LIGHT__";
  function apply(theme) {
    document.documentElement.dataset.theme = theme;
    document.querySelectorAll("picture").forEach(function (p) {
      var img = p.querySelector("img");
      if (!img) return;
      img.src = theme === "dark" ? DARK : LIGHT;
      p.querySelectorAll("source").forEach(function (s) { s.media = "none"; });
    });
    document.getElementById("bd").className = theme === "dark" ? "on" : "";
    document.getElementById("bl").className = theme === "light" ? "on" : "";
  }
  document.getElementById("bd").onclick = function () { apply("dark"); };
  document.getElementById("bl").onclick = function () { apply("light"); };
  var h = location.hash.replace("#", "");
  apply(h === "dark" ? "dark" : h === "light" ? "light" : (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
