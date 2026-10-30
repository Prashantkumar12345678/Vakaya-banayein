"""Real tap: oblique key approach -> insertion -> quarter-turn -> unlock -> door opens."""
from pathlib import Path
import functools,http.server,socketserver,threading,re,time,io
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'_previews/door-key-animation';OUT.mkdir(parents=True,exist_ok=True)
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
class Server(socketserver.ThreadingTCPServer):
 allow_reuse_address=True
 daemon_threads=True
srv=Server(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'HI02H12_L02_S01')))
threading.Thread(target=srv.serve_forever,daemon=True).start();errors=[];frames=[];phases={}
with sync_playwright() as p:
 browser=p.chromium.launch(channel='chrome',headless=True,args=['--autoplay-policy=no-user-gesture-required'])
 page=browser.new_page(viewport={'width':1333,'height':750},has_touch=True)
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('response',lambda r:errors.append(str(r.status)+' '+r.url) if r.status>=400 else None)
 page.goto('http://127.0.0.1:'+str(srv.server_address[1])+'/index.html?slide=8',wait_until='load')
 page.wait_for_function('document.querySelector(".adv-door")?.dataset.state==="playing" && !isPlaying && !state.locked',timeout=30000)
 page.locator('.adventure-game').screenshot(path=str(OUT/'00-before.png'))
 page.locator('.adv-choice').filter(has_text=re.compile('^सो रही$')).tap()
 page.wait_for_selector('.adv-key-insertion')
 deadline=time.monotonic()+5
 while time.monotonic()<deadline:
  phase=page.locator('.adv-door').get_attribute('data-key-phase')
  if phase not in phases:
   phases[phase]=time.monotonic()
   page.locator('.adventure-game').screenshot(path=str(OUT/(phase+'.png')))
  if phase=='done':break
  assert page.locator('.adv-open').count()==0,'Door cannot open before key is inserted and turned'
  frames.append(page.screenshot());page.wait_for_timeout(60)
 assert all(phase in phases for phase in ['aligning','inserting','turning','unlocked','done']),phases.keys()
 assert phases['inserting']<phases['turning']<phases['unlocked']<phases['done']
 assert page.locator('.adv-key-insertion').count()==0
 assert 'सो रही' in page.locator('.adv-deck').inner_text()
 page.wait_for_selector('.adv-open',timeout=15000)
 page.locator('.adventure-game').screenshot(path=str(OUT/'door-open.png'))
 assert not errors,errors
 # Navigation while the key is moving must remove its overlays, animations and pending unlock.
 page.goto('http://127.0.0.1:'+str(srv.server_address[1])+'/index.html?slide=8',wait_until='load')
 page.wait_for_function('document.querySelector(".adv-door")?.dataset.state==="playing" && !isPlaying && !state.locked',timeout=30000)
 page.locator('.adv-choice').filter(has_text=re.compile('^सो रही$')).tap();page.wait_for_selector('.adv-key-insertion')
 page.evaluate('mountSlide(3)');page.wait_for_timeout(3300)
 assert page.locator('.adv-key-insertion,.adv-door,.adv-open').count()==0
 assert not errors,errors
 browser.close()
srv.shutdown()
from PIL import Image
images=[Image.open(io.BytesIO(b)).convert('RGB').resize((960,540)) for b in frames]
images[0].save(OUT/'key-insertion.gif',save_all=True,append_images=images[1:],duration=180,loop=0)
print('PASS real tap: align, insert with depth, turn, unlock, reveal answer, open gate; navigation cleans animation; no errors')
