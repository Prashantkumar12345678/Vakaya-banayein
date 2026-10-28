# -*- coding: utf-8 -*-
"""Break things on purpose and check the game never gets stuck.

    python _tools/qa_failures.py

  A  NETWORK  two assets aborted, one 404, one that never answers: Play must appear, and the preload
              must still complete (the stalled one is given up after the 10s stall timeout).
  B  SILENT   every voice line accepted but never heard and never "ended" (Web Audio start() and
              <audio>.play() both swallowed): the teaching slide's Next button and the question's
              voice lock must still release - the watchdogs, not the media events, do it.
  C  BLOBS    once everything is loaded, every blob: URL is revoked: the next pictures, the poem
              video and the voice must fall back to the ordinary files and still show / play.
  D  FILE     opened from file:// (fetch refused): the bar fills at once and Play still comes.
  E  REFUSED  the browser refuses sound until a gesture: the speaker invites the tap, Play stays
              hidden; a real tap starts the greeting, Play follows it, and Play opens the gate.
Exit code 1 on any failure.
"""
import functools, http.server, os, socketserver, sys, threading, time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
PROJ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
GAME = os.path.join(PROJ, "HI02H12_L02_S01")


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass


class Server(socketserver.ThreadingTCPServer):
    request_queue_size = 128; allow_reuse_address = True


srv = Server(("127.0.0.1", 0), functools.partial(Quiet, directory=GAME)); srv.daemon_threads = True
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = "http://127.0.0.1:%d/index.html" % srv.server_address[1]
fails = []


def check(cond, msg):
    print(("  ok    " if cond else "  FAIL  ") + msg)
    if not cond: fails.append(msg)


def errors_of(page, bucket):
    page.on("pageerror", lambda e: bucket.append(str(e)[:160]))
    page.on("console", lambda m: m.type == "error" and "Failed to load resource" not in m.text and bucket.append(m.text[:160]))


def wait_play(page, limit):
    t0 = time.time()
    while time.time() - t0 < limit:
        s = page.evaluate("""() => { const b = document.getElementById('sgBtn'), s = getComputedStyle(b);
            return { pct: +document.getElementById('sgLoad').dataset.pct, play: s.visibility !== 'hidden' && +s.opacity > .5 }; }""")
        if s["play"]: return time.time() - t0, s["pct"]
        time.sleep(0.2)
    return None, page.evaluate("() => +document.getElementById('sgLoad').dataset.pct")


with sync_playwright() as p:
    br = p.chromium.launch(channel="chrome", headless=True, args=["--autoplay-policy=no-user-gesture-required"])

    print("A  network failures")
    ctx = br.new_context(viewport={"width": 1920, "height": 1080}); page = ctx.new_page(); errs = []; errors_of(page, errs)
    page.route("**/pic_mor.webp*", lambda r: r.abort())
    page.route("**/vo_name_gaay.wav*", lambda r: r.abort())
    page.route("**/sfx_tap.wav*", lambda r: r.fulfill(status=404, body="no"))
    page.route("**/pic_bail.webp*", lambda r: None)            # never answered: a stalled transfer
    page.goto(BASE, wait_until="commit")
    took, pct = wait_play(page, 40)
    # [H11-202] Play no longer waits for the (hidden) bar - it follows the greeting; the preload
    # finishes behind it, the stalled file after its 10s stall timeout
    check(took is not None, "Play appeared %s with failing files in the preload" % ("after %.1fs" % took if took else "NEVER"))
    page.wait_for_function("() => AssetLoader.isReady", timeout=30000)
    st = page.evaluate("() => AssetLoader.stats()")
    check(st["shown"] == 100, "the preload still completed (100%%) despite the failures")
    check(st["finished"] == st["files"] and st["local"] == st["files"] - 4, "all %d files settled, %d local, 4 left on their ordinary URL" % (st["finished"], st["local"]))
    check(page.evaluate("() => AssetLoader.resolve('assets/Images/pic_mor.webp') === null"), "an aborted file keeps its ordinary URL")
    check(not errs, "no JS errors %s" % errs[:3]); ctx.close()

    print("B  media that never ends")
    for slide, what, js in [(0, "T1 Next button", "() => { const b = document.getElementById('navBtn'); return b && !b.disabled; }"),
                            (9, "G1 voice lock released", "() => !document.body.classList.contains('vo-lock')")]:
        ctx = br.new_context(viewport={"width": 1920, "height": 1080}); page = ctx.new_page(); errs = []; errors_of(page, errs)
        page.add_init_script("""
          AudioBufferSourceNode.prototype.start = function(){};                 // accepted, never sounds, never ends
          HTMLMediaElement.prototype.play = function(){ return Promise.resolve(); };""")
        page.goto(BASE + "?slide=%d" % slide); t0 = time.time()
        try:
            page.wait_for_function(js, timeout=45000); took = time.time() - t0
        except Exception:
            took = None
        check(took is not None, "%s appeared with silent media %s" % (what, "after %.1fs" % took if took else "NEVER"))
        check(not errs, "no JS errors %s" % errs[:3]); ctx.close()

    print("C  revoked blob: URLs fall back to the files")
    ctx = br.new_context(viewport={"width": 1920, "height": 1080}); page = ctx.new_page(); errs = []; errors_of(page, errs)
    page.goto(BASE + "?slide=0"); page.wait_for_function("() => AssetLoader.isReady", timeout=60000)
    n = page.evaluate("() => { let n = 0; AssetLoader.list().forEach(p => { const u = AssetLoader.resolve(p); if(u && u.startsWith('blob:')){ URL.revokeObjectURL(u); n++; } }); return n; }")
    print("  revoked %d blob URLs" % n)
    page.evaluate("() => mountSlide(1)"); page.wait_for_timeout(4000)      # T2: the poem video + pictures
    v = page.evaluate("""() => { const v = document.querySelector('video'); return v ? { src: v.currentSrc.slice(0, 60), rs: v.readyState, err: !!v.error, t: v.currentTime } : null; }""")
    check(bool(v) and v["rs"] >= 2 and not v["err"] and not v["src"].startswith("blob:"), "poem video fell back and plays: %s" % v)
    page.evaluate("() => mountSlide(9)"); page.wait_for_timeout(3000)      # G1: question pictures
    bad = page.evaluate("() => [...document.querySelectorAll('.slide-host img')].filter(i => !i.complete || !i.naturalWidth).map(i => i.src.slice(0, 60))")
    check(not bad, "question pictures all drawn after the revoke %s" % bad)
    check(not errs, "no JS errors %s" % errs[:3]); ctx.close()

    print("E  sound refused until a real tap")
    b2 = p.chromium.launch(channel="chrome", headless=True, args=["--autoplay-policy=document-user-activation-required"])
    page = b2.new_page(viewport={"width": 1920, "height": 1080}); errs = []; errors_of(page, errs)
    page.goto(BASE); page.wait_for_timeout(4000)
    s = page.evaluate("() => ({ spk: document.getElementById('sgVo').className, play: getComputedStyle(document.getElementById('sgBtn')).visibility })")
    check("sg-blocked" in s["spk"] and s["play"] == "hidden", "refused: speaker invites the tap, Play hidden (%s)" % s)
    page.mouse.click(960, 500)                       # a trusted tap anywhere
    took, pct = wait_play(page, 40)
    check(took is not None, "after the tap the greeting played and Play appeared %s" % ("after %.1fs" % took if took else "NEVER"))
    if took:
        page.click("#sgBtn", force=True)
        try: page.wait_for_selector("#phaseGate.show", timeout=4000); check(True, "Play opens the transition")
        except Exception: check(False, "Play opens the transition")
    check(not errs, "no JS errors %s" % errs[:3]); b2.close()

    print("D  file://")
    ctx = br.new_context(viewport={"width": 1920, "height": 1080}); page = ctx.new_page(); errs = []; errors_of(page, errs)
    page.goto("file:///" + os.path.join(GAME, "index.html").replace("\\", "/"))
    took, pct = wait_play(page, 40)
    check(took is not None and pct == 100, "file:// - bar %s%%, Play %s" % (pct, "after %.1fs" % took if took else "NEVER"))
    check(not errs, "no JS errors %s" % errs[:3]); ctx.close()
    br.close()
srv.shutdown()
print("\n%d failure(s)" % len(fails))
sys.exit(1 if fails else 0)
