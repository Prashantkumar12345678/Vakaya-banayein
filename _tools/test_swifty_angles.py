"""Verify direction selection, alpha sheets, real map turns and railway walking."""
from pathlib import Path
import functools,http.server,socketserver,threading,re
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
class Server(socketserver.ThreadingTCPServer):
 allow_reuse_address=True
 daemon_threads=True
srv=Server(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'HI02H12_L02_S01')))
threading.Thread(target=srv.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(srv.server_address[1])+'/index.html'
errors=[]
with sync_playwright() as p:
 br=p.chromium.launch(channel='chrome',headless=True,args=['--autoplay-policy=no-user-gesture-required'])
 page=br.new_page(viewport={'width':1333,'height':750},has_touch=True)
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(base+'?slide=9',wait_until='load')
 page.wait_for_selector('.journey-swifty.is-walking')
 page.wait_for_function('document.querySelector(".journey-swifty")?.dataset.facing==="back"')
 assert 'swifty_walk_back_strip.webp' in page.locator('.journey-walk').evaluate('(e)=>getComputedStyle(e).backgroundImage')
 page.locator('.journey-map').screenshot(path=str(ROOT/'_previews/adventure-playtest/ui-swifty-map-back.png'))
 results=page.evaluate('''()=>{const host=document.querySelector('.adventure-game'),e=document.createElement('div');host.appendChild(e);const result=[];for(const [p,want] of [[[10,0],'right'],[[-10,0],'left'],[[0,-10],'back'],[[0,10],'front']]){swiftyFaceStep(e,[0,0],p);result.push(e.dataset.facing===want);}e.remove();return result;}''')
 assert all(results),results
 page.goto(base+'?slide=11',wait_until='load')
 page.wait_for_function('document.querySelector(".adventure-game").dataset.state==="playing" && !isPlaying',timeout=25000)
 # The gate opens only after all five taps; then Swifty turns away over the rails.
 for word in ['लड़की','गाना','गा','रही','है।']:
  page.wait_for_function('document.querySelector(".adventure-game")?.dataset.state==="playing" && !isPlaying && !state.locked && !document.querySelector(".adv-fitting")',timeout=25000)
  page.locator('.adv-choice').filter(has_text=re.compile('^'+re.escape(word)+'$')).tap()
 page.wait_for_function('document.querySelector(".adv-railway .adv-walker.is-walking")?.dataset.facing==="back"',timeout=25000)
 assert 'swifty_walk_back_strip.webp' in page.locator('.adv-gait').evaluate('(e)=>getComputedStyle(e).backgroundImage')
 page.locator('.adventure-game').screenshot(path=str(ROOT/'_previews/adventure-playtest/ui-swifty-railway-back.png'))
 assert not errors,errors
 br.close()
srv.shutdown()
print('PASS four directions; actual map uses rear walk; completed railway sentence uses rear walk; no browser errors')
