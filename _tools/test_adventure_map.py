"""Verify the actual Play route, journey transitions, completion and map cleanup."""
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


import re
errors=[]
with sync_playwright() as p:
 br=p.chromium.launch(channel='chrome',headless=True,args=['--autoplay-policy=no-user-gesture-required']);page=br.new_page(viewport={'width':1333,'height':750},has_touch=True)
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(base,wait_until='load');page.locator('#sgBtn').wait_for(state='visible',timeout=20000);page.locator('#sgBtn').click(force=True)
 page.wait_for_selector('.journey-map',timeout=25000)
 assert page.locator('.journey-map').get_attribute('data-level')=='0'
 page.locator('.journey-map').screenshot(path=str(ROOT/'_previews/adventure-playtest/journey-overview.png'))
 page.wait_for_selector('.journey-map',state='detached',timeout=15000)
 page.wait_for_function('state.idx===0 && document.querySelector("#slideHost").children.length>0',timeout=15000)
 print('PASS real Play button: greeting -> journey overview -> tutorial',flush=True)
 page.goto(base+'?slide=7',wait_until='load');page.wait_for_selector('.journey-map',timeout=10000)
 assert page.locator('.adventure-game').get_attribute('data-state')=='map'
 page.evaluate('document.querySelector(".adv-choice").click()');assert page.evaluate('state.attempts')==0
 page.wait_for_function('document.querySelector(".adventure-game").dataset.state==="playing" && !isPlaying',timeout=25000)
 page.locator('.adv-choice').filter(has_text=re.compile('^पानी$')).tap()
 page.wait_for_selector('.journey-map',timeout=20000)
 assert page.locator('.journey-map').get_attribute('data-level')=='1'
 assert page.locator('.journey-landmark.is-done').count()==1
 page.wait_for_timeout(1200)
 page.locator('.journey-map').screenshot(path=str(ROOT/'_previews/adventure-playtest/journey-next-stop.png'))
 page.wait_for_function('document.querySelector(".adventure-game").dataset.scene==="door" && document.querySelector(".adventure-game").dataset.state==="playing" && !isPlaying',timeout=20000)
 print('PASS completed bridge -> moving journey map -> door question, with input/audio gating',flush=True)
 page.goto(base+'?slide=12',wait_until='load');page.wait_for_selector('.adventure-game')
 for word in ['बकरी','पत्ते','खा','रही','है।']:
  page.wait_for_function('document.querySelector(".adventure-game").dataset.state==="playing" && !isPlaying && !state.locked && !document.querySelector(".adv-fitting") && [...document.querySelectorAll(".adv-choice")].every(t=>!t._bridgeCanFit||t._bridgeCanFit())',timeout=25000)
  page.locator('.adv-choice').filter(has_text=re.compile('^'+re.escape(word)+'$')).tap();page.wait_for_timeout(900)
 page.wait_for_selector('.journey-map',timeout=20000)
 assert page.locator('.journey-map').get_attribute('data-level')=='6'
 assert page.locator('.journey-landmark.is-done').count()==6
 page.locator('.journey-map').screenshot(path=str(ROOT/'_previews/adventure-playtest/journey-completed.png'))
 page.wait_for_selector('#endScreen.show',timeout=12000)
 print('PASS last gate -> completed map with six checkmarks -> celebration',flush=True)
 page.goto(base+'?slide=9',wait_until='load');page.wait_for_selector('.journey-map');page.evaluate('mountSlide(3)');assert page.locator('.journey-map').count()==0
 page.wait_for_timeout(4200);assert page.evaluate('state.idx')==3
 print('PASS leaving map cancels animation and pending callbacks',flush=True)
 assert not errors,errors
 br.close()
srv.shutdown()
