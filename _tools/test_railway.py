"""Play P5 with real taps and verify closed -> solved -> open -> cross -> updated journey map."""
from pathlib import Path
import functools,http.server,socketserver,threading,re,io,json,hashlib
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'_previews/railway-crossing/live';OUT.mkdir(parents=True,exist_ok=True)
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
class Server(socketserver.ThreadingTCPServer):
 allow_reuse_address=True
 daemon_threads=True
srv=Server(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'HI02H12_L02_S01')))
threading.Thread(target=srv.serve_forever,daemon=True).start()
errors=[];frames=[]
with sync_playwright() as p:
 browser=p.chromium.launch(channel='chrome',headless=True,args=['--autoplay-policy=no-user-gesture-required'])
 page=browser.new_page(viewport={'width':1333,'height':750},has_touch=True)
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('response',lambda r:errors.append(str(r.status)+' '+r.url) if r.status>=400 else None)
 page.goto('http://127.0.0.1:'+str(srv.server_address[1])+'/index.html?slide=11',wait_until='load')
 page.wait_for_selector('.journey-map[data-level="4"]')
 page.locator('.journey-map').screenshot(path=str(OUT/'map-closed.png'))
 def ready():
  page.wait_for_function('document.querySelector(".adventure-game")?.dataset.state==="playing" && !isPlaying && !state.locked && !state.hintActive && !document.querySelector(".adv-fitting")',timeout=30000)
 ready()
 assert page.locator('.adv-railway').count()==1
 assert page.locator('.adv-deck .bridge-gap').count()==5
 assert page.locator('.adv-rail-arm').evaluate('(e)=>getComputedStyle(e).transform')=='none'
 assert page.locator('.adv-choice').count()==8
 assert all('railway_tile.webp' in bg for bg in page.locator('.adv-choice').evaluate_all('(els)=>els.map(e=>getComputedStyle(e).backgroundImage)'))
 assert page.locator('.adv-walker .adv-idle').get_attribute('src').split('?')[0]=='assets/UI/sw_explain_still.webp'
 page.locator('.adventure-game').screenshot(path=str(OUT/'01-closed.png'))
 print('PASS closed crossing and metal word options loaded; original UI Swifty',flush=True)
 page.locator('.adv-choice').filter(has_text=re.compile('^किताब$')).tap();ready()
 assert page.locator('.adv-deck .wb-word').count()==0
 assert page.locator('.adv-railway').get_attribute('data-crossing-phase')=='closed'
 for i,word in enumerate(['लड़की','गाना','गा','रही','है।']):
  ready();page.locator('.adv-choice').filter(has_text=re.compile('^'+re.escape(word)+'$')).tap()
  page.wait_for_function('(n)=>Number(document.querySelector(".adventure-game").dataset.filled)===n',arg=i+1)
  if i==0:
   page.locator('.adventure-game').screenshot(path=str(OUT/'02-tap-flight.png'))
  if i<4:
   page.wait_for_timeout(850)
   assert page.locator('.adv-railway').get_attribute('data-crossing-phase')=='closed'
 print('PASS wrong word leaves gate closed; five single taps complete original sentence',flush=True)
 page.wait_for_selector('.adv-rail-success',timeout=25000)
 page.locator('.adventure-game').screenshot(path=str(OUT/'03-solved.png'))
 page.wait_for_function('document.querySelector(".adv-railway")?.dataset.crossingPhase==="crossing"',timeout=10000)
 assert page.locator('.adv-rail-lamp').evaluate('(e)=>getComputedStyle(e).opacity')=='1'
 assert page.locator('.adv-rail-arm').evaluate('(e)=>getComputedStyle(e).transform')!='none'
 assert page.locator('.adv-deck .wb-word').all_text_contents()==['लड़की','गाना','गा','रही','है।']
 observed_back=False
 for i in range(30):
  if page.locator('.adv-railway').count()==0:break
  info=page.locator('.adv-walker').evaluate('(e)=>({facing:e.dataset.facing,moving:e.classList.contains("is-walking")})')
  if info['facing']=='back' and info['moving']:
   if not observed_back:page.locator('.adventure-game').screenshot(path=str(OUT/'04-open-crossing.png'))
   observed_back=True
   assert 'swifty_walk_back_strip.webp' in page.locator('.adv-gait').evaluate('(e)=>getComputedStyle(e).backgroundImage')
  frames.append(page.screenshot());page.wait_for_timeout(80)
  if page.locator('.adv-railway').get_attribute('data-crossing-phase')=='crossed':break
 assert observed_back, 'Swifty must turn away while crossing the rails'
 page.wait_for_function('state.idx===12',timeout=15000)
 page.wait_for_selector('.journey-map[data-level="5"]')
 # Preloaded assets may be represented by blob URLs; verify actual image bytes.
 actual_map_hash=page.locator('.journey-map-art').evaluate("async e=>{const bytes=await (await fetch(e.src)).arrayBuffer();const hash=await crypto.subtle.digest('SHA-256',bytes);return [...new Uint8Array(hash)].map(b=>b.toString(16).padStart(2,'0')).join('');}")
 expected_map_hash=hashlib.sha256((ROOT/'HI02H12_L02_S01/assets/Images/adventure/journey_map_railway_open.webp').read_bytes()).hexdigest()
 assert actual_map_hash==expected_map_hash, 'Next journey map must use the open crossing asset' 
 page.wait_for_function('document.querySelector(".journey-map")?.dataset.state==="ready"',timeout=10000)
 page.locator('.journey-map').screenshot(path=str(OUT/'05-map-open.png'))
 assert not errors,errors
 browser.close()
srv.shutdown()
from PIL import Image
imgs=[Image.open(io.BytesIO(b)).convert('RGB').resize((960,540)) for b in frames]
imgs[0].save(OUT/'railway-crossing.gif',save_all=True,append_images=imgs[1:],duration=180,loop=0)
print('PASS green light, raised boom, rear-view walk over rails, next map shows open railway crossing; no errors')
