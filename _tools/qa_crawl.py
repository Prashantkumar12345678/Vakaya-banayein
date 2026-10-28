# -*- coding: utf-8 -*-
"""Drive the game like a user in headless Chrome (Playwright) and report what broke.

    python _tools/qa_crawl.py [--out DIR] [--slow] [--only 0,3,12] [--landing]

Serves HI02H12_L02_S01/ over local HTTP (file:// hides fetch/CORS behaviour the real host has),
then:
  1. LANDING  - loads the page, samples the loading bar and the Play button every 100ms, waits for
                the bar to reach 100% and the button to appear, taps it, confirms the first gate and
                the first slide mount. --slow throttles the network (CDP) so the bar is observable.
  2. SLIDES   - opens every slide on its own (?slide=N), waits for its gated control: the Next button
                on a teaching slide, the end of the voice lock on a question; checks every <img>
                (complete, naturalWidth>0) and <video> (no .error, has data); screenshots it.
  3. LEDGER   - every console error, page error, failed request and 4xx/5xx response, per page.
Exit code 1 if anything failed, so it can gate a deploy.
"""
import functools, http.server, json, os, socketserver, sys, threading, time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
PROJ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
GAME = os.path.join(PROJ, "HI02H12_L02_S01")
ARGS = sys.argv[1:]
OUT = ARGS[ARGS.index("--out") + 1] if "--out" in ARGS else os.path.join(PROJ, "_backup", "qa_shots")
ONLY = [int(x) for x in ARGS[ARGS.index("--only") + 1].split(",")] if "--only" in ARGS else None
SLOW = "--slow" in ARGS
os.makedirs(OUT, exist_ok=True)


SERVED = []   # (path, status) for every request the server actually answered - the real network


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def log_request(self, code="-", size="-"):
        SERVED.append((self.path, int(code) if str(code).isdigit() else 0))
    def end_headers(self):
        self.send_header("Cache-Control", "public, max-age=0, must-revalidate")   # what Vercel sends for static files
        super().end_headers()


class Server(socketserver.ThreadingTCPServer):
    request_queue_size = 128          # the default 5 refuses connections under a 5-wide preload
    allow_reuse_address = True


srv = Server(("127.0.0.1", 0), functools.partial(Quiet, directory=GAME))
srv.daemon_threads = True
PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = "http://127.0.0.1:%d/index.html" % PORT
problems = []


def watch(page, tag):
    page.on("console", lambda m: m.type == "error" and problems.append("%s console: %s" % (tag, m.text[:200])))
    page.on("pageerror", lambda e: problems.append("%s pageerror: %s" % (tag, str(e)[:200])))
    page.on("requestfailed", lambda r: (not r.url.startswith(("blob:", "data:")) and r.failure != "net::ERR_ABORTED")
            and problems.append("%s requestfailed: %s %s" % (tag, r.url.split(str(PORT))[-1], r.failure)))
    page.on("response", lambda r: r.status >= 400 and problems.append("%s HTTP %d %s" % (tag, r.status, r.url.split(str(PORT))[-1])))


HEALTH = """() => {
  const bad = [];
  document.querySelectorAll('img').forEach(i => { const r = i.getBoundingClientRect();
    if(!i.getAttribute('src')) return;
    if(!i.complete || i.naturalWidth === 0) bad.push('img ' + (i.getAttribute('src')||'').slice(0,80) + (r.width ? '' : ' (hidden)')); });
  document.querySelectorAll('video').forEach(v => { if(v.error) bad.push('video error ' + v.error.code + ' ' + (v.currentSrc||'').slice(0,80));
    else if(v.readyState < 1 && v.getBoundingClientRect().width) bad.push('video no data ' + (v.currentSrc||'').slice(0,80)); });
  return bad; }"""

with sync_playwright() as p:
    br = p.chromium.launch(channel="chrome", headless=True, args=["--autoplay-policy=no-user-gesture-required"])
    ctx = br.new_context(viewport={"width": 1920, "height": 1080})

    # ---------------------------------------------------------------- 1. landing
    if ONLY is None:
        page = ctx.new_page(); watch(page, "landing")
        if SLOW:
            cdp = ctx.new_cdp_session(page)
            cdp.send("Network.enable")
            cdp.send("Network.emulateNetworkConditions", {"offline": False, "latency": 150,
                     "downloadThroughput": 4 * 1024 * 1024 / 8, "uploadThroughput": 1024 * 1024 / 8})   # 4 Mbps
        SERVED.clear()
        t0 = time.time(); page.goto(BASE, wait_until="commit"); shot_mid = False
        samples, seen_btn, last = [], None, -1
        while time.time() - t0 < (400 if SLOW else 90):
            s = page.evaluate("""() => { const b = document.getElementById('sgBtn'), bar = document.getElementById('sgLoad');
                const bs = b ? getComputedStyle(b) : null;
                const vs = bar ? getComputedStyle(bar) : null;
                return { pct: bar ? +(bar.dataset.pct || 0) : -1,
                         barShown: !!(bar && !bar.hidden && vs.visibility !== 'hidden' && +vs.opacity > 0.5),
                         btn: !!(bs && bs.visibility !== 'hidden' && +bs.opacity > 0.5), cls: b ? b.className : '' }; }""")
            if SLOW and not shot_mid and 30 <= s["pct"] <= 70:
                page.screenshot(path=os.path.join(OUT, "landing_loading.png")); shot_mid = True
            if s["pct"] != last:
                samples.append((round(time.time() - t0, 1), s["pct"], s["barShown"], s["btn"])); last = s["pct"]
            if s["btn"] and s["barShown"]: problems.append("landing: Play button and loading bar visible together")
            # [H11-202] Play no longer waits for 100% - the bar is gone, the preload runs behind
            if s["btn"]: seen_btn = round(time.time() - t0, 1); break
            time.sleep(0.1)
        pcts = [x[1] for x in samples]
        if any(b < a for a, b in zip(pcts, pcts[1:])): problems.append("landing: bar went backwards %s" % pcts)
        print("landing: bar samples (t, pct, barShown, btn):", samples[:6], "...", samples[-3:])
        print("landing: Play appeared at", seen_btn, "s")
        st = page.evaluate("() => window.AssetLoader ? AssetLoader.stats() : null")
        print("landing: loader stats", st)
        bodies, order = {}, []
        for path, code in SERVED:                       # a 304 sends no body: only 200s are downloads
            if code == 200 and "/assets/" in path:
                k = path.split("?")[0]; bodies[k] = bodies.get(k, 0) + 1
                if k not in order: order.append(k)
        dup = {u: n for u, n in bodies.items() if n > 1}
        print("landing: %d asset files downloaded, %d more than once %s" % (len(bodies), len(dup), dup if dup else ""))
        for u, n in dup.items(): problems.append("landing: %s downloaded %d times" % (u, n))
        print("landing: first 8 downloads:", [o.split("/")[-1] for o in order[:8]])
        if SLOW:   # under a slow link, the pictures must all be in before the first video / big clip
            big = [i for i, o in enumerate(order) if o.endswith((".webm",))]
            pics = [i for i, o in enumerate(order) if o.endswith((".webp", ".svg")) and "anim" not in o and "peeking" not in o and "last_swifty_end" not in o]
            print("landing: last still picture finished #%d, first video #%d of %d" % (max(pics), min(big), len(order)))
            if max(pics) > min(big): problems.append("landing: a still picture finished after a video")
            print("landing: bar timeline:", [(t, p) for t, p, _, _ in samples][::max(1, len(samples) // 12)])
        if seen_btn is None: problems.append("landing: Play button never appeared")
        else:
            page.screenshot(path=os.path.join(OUT, "landing_ready.png"))
            page.click("#sgBtn", force=True); t1 = time.time()
            page.wait_for_selector("#phaseGate.show", timeout=5000)
            print("landing: gate open %.2fs after tap" % (time.time() - t1))
            page.wait_for_timeout(4500); page.screenshot(path=os.path.join(OUT, "gate_tutorial.png"))
            page.wait_for_function("() => document.getElementById('startGate').classList.contains('hidden') && !document.body.classList.contains('gating')", timeout=30000)
            print("landing: first slide mounted %.1fs after tap" % (time.time() - t1))
            # walk the whole tutorial the way a child does: wait for Next, press it, check the media
            for step in range(12):
                cur = page.evaluate("() => CARD.slides[state.idx].id")
                if not cur.startswith("T"): break
                try:
                    page.wait_for_function("() => { const b = document.getElementById('navBtn'); return b && !b.disabled && b.offsetParent && !document.body.classList.contains('gating'); }", timeout=40000)
                except Exception:
                    problems.append("walk: %s Next never enabled" % cur); break
                bad = page.evaluate(HEALTH)
                vid = page.evaluate("() => { const v = document.querySelector('.slide-host video'); return v ? [v.readyState, v.currentSrc.slice(0, 5)] : null; }")
                print("walk: %-3s ready, media-bad=%d video=%s" % (cur, len(bad), vid))
                for b in bad: problems.append("walk %s: %s" % (cur, b))
                page.click("#navBtn", force=True)
                page.wait_for_function("(c) => CARD.slides[state.idx].id !== c || document.body.classList.contains('gating')", arg=cur, timeout=15000)
                page.wait_for_function("() => !document.body.classList.contains('gating')", timeout=30000)
            print("walk: reached", page.evaluate("() => CARD.slides[state.idx].id"))
            page.screenshot(path=os.path.join(OUT, "walk_end.png"))
        page.close()

    # ---------------------------------------------------------------- 2. every slide
    n = ctx.new_page(); n.goto(BASE + "?slide=0"); n.wait_for_timeout(1500)
    slides = n.evaluate("() => CARD.slides.map(s => [s.id, s.type, s.phase])"); n.close()
    for i, (sid, typ, ph) in enumerate(slides):
        if (ONLY is not None and i not in ONLY) or "--landing" in ARGS: continue
        page = ctx.new_page(); tag = "%02d %s" % (i, sid); watch(page, tag)
        page.goto(BASE + "?slide=%d" % i); t0 = time.time()
        gate = "nav" if typ == "STORY_SCENE" else ("end" if typ == "CELEBRATION" else "unlock")
        try:
            if gate == "nav":
                page.wait_for_function("() => { const b = document.getElementById('navBtn'); return b && !b.disabled && b.offsetParent; }", timeout=40000)
            elif gate == "unlock":
                page.wait_for_function("() => document.querySelector('.slide-host') && !document.body.classList.contains('vo-lock') && !document.body.classList.contains('gating')", timeout=40000)
                page.wait_for_timeout(400)
            else:
                page.wait_for_timeout(6000)
            took = time.time() - t0
        except Exception:
            took = None; problems.append("%s: gated control never appeared (%s)" % (tag, gate))
        bad = page.evaluate(HEALTH)
        for b in bad: problems.append("%s: %s" % (tag, b))
        page.screenshot(path=os.path.join(OUT, "slide_%02d_%s.png" % (i, sid)))
        print("%-8s %-18s %-9s %s ready in %s  media-bad=%d" % (tag, typ, ph, gate, "%.1fs" % took if took else "NEVER", len(bad)))
        page.close()
    br.close()
srv.shutdown()
print("\n%d problem(s)" % len(problems))
for x in problems: print("  -", x)
sys.exit(1 if problems else 0)
