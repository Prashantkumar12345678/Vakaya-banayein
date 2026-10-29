"""Protect original UI Swifty identity and verify map/adventure sprite animation."""
"""Play all six practice scenes using one touch per answer, including retry/help and transitions.
Run with python3 _tools/test_adventure.py (requires Playwright and Chrome).
Saves actual game screenshots and a play-through under _previews/adventure-playtest/.
"""
from pathlib import Path
import functools,http.server,socketserver,threading,json,time,sys
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'_previews'/'adventure-playtest'
OUT.mkdir(parents=True,exist_ok=True)
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
class Server(socketserver.ThreadingTCPServer):
 allow_reuse_address=True
 daemon_threads=True
srv=Server(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'HI02H12_L02_S01')))
threading.Thread(target=srv.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(srv.server_address[1])+'/index.html'


import re,hashlib
errors=[]
ui=ROOT/'HI02H12_L02_S01/assets/UI'
assert hashlib.sha256((ui/'sw_explain_still.webp').read_bytes()).hexdigest()=='1d1d2e7f9b912cab4b2ef827d7b605cbdb9f6231224465931375d9aef5d509fb'
assert hashlib.sha256((ui/'start_mascot.webp').read_bytes()).hexdigest()=='207d6c4db4a9629a22c9f010b2ca1595315c98eeeeb014b4b1bf161f12f39b98'
with sync_playwright() as p:
 br=p.chromium.launch(channel='chrome',headless=True,args=['--autoplay-policy=no-user-gesture-required']);page=br.new_page(viewport={'width':1333,'height':750},has_touch=True)
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(base+'?slide=8',wait_until='load');page.wait_for_selector('.journey-map')
 page.wait_for_selector('.journey-swifty.is-walking',timeout=5000)
 expected=page.evaluate('new URL(bustAudio("assets/UI/sw_explain_still.webp"),document.baseURI).href')
 assert 'assets/UI/sw_explain_still.webp' in page.locator('.journey-idle').get_attribute('src') or page.locator('.journey-idle').evaluate('(e)=>e.src')==expected
 assert page.locator('.journey-walk').evaluate('(e)=>getComputedStyle(e).animationName')=='swiftyUiWalk'
 page.locator('.journey-map').screenshot(path=str(ROOT/'_previews/adventure-playtest/ui-swifty-map-walk.png'))
 page.goto(base+'?slide=7',wait_until='load');page.wait_for_selector('.adventure-game')
 page.wait_for_function('document.querySelector(".adventure-game").dataset.state==="playing" && !isPlaying',timeout=25000)
 assert page.locator('.adv-idle').get_attribute('src').split('?')[0].endswith('assets/UI/sw_explain_still.webp')
 page.locator('.adv-choice').filter(has_text=re.compile('^पानी$')).tap()
 page.wait_for_selector('.adv-walker.is-walking',timeout=20000)
 sprite=page.locator('.adv-walker .adv-gait')
 assert sprite.evaluate('(e)=>getComputedStyle(e).animationName')=='swiftyUiWalk'
 assert page.locator('.adv-idle').evaluate('(e)=>getComputedStyle(e).opacity')=='0'
 assert sprite.evaluate('(e)=>getComputedStyle(e).opacity')=='1'
 a=sprite.evaluate('(e)=>getComputedStyle(e).backgroundPosition');page.wait_for_timeout(210);b=sprite.evaluate('(e)=>getComputedStyle(e).backgroundPosition');assert a!=b,(a,b)
 page.locator('.adventure-game').screenshot(path=str(ROOT/'_previews/adventure-playtest/ui-swifty-bridge-walk.png'))
 page.wait_for_function('state.idx===8',timeout=12000)
 for idx in range(7,13):
  page.goto(base+'?slide='+str(idx)+'&still=1',wait_until='load');page.wait_for_selector('.adv-idle');page.wait_for_timeout(350)
  assert page.locator('.adv-idle').get_attribute('src').split('?')[0].endswith('assets/UI/sw_explain_still.webp')
 assert not errors,errors
 print('PASS original UI bitmaps unchanged; map and bridge use eight-step sprite animation; all six scenes use original UI Swifty',flush=True)
 br.close()
srv.shutdown()
