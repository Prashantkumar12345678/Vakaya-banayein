"""Play the tunnel question and verify Swifty crosses under the map's rock roof."""
from pathlib import Path
import functools,http.server,socketserver,threading,re,time,io
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'_previews/adventure-playtest'
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
class Server(socketserver.ThreadingTCPServer):
 allow_reuse_address=True
 daemon_threads=True
srv=Server(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'HI02H12_L02_S01')))
threading.Thread(target=srv.serve_forever,daemon=True).start()
base='http://127.0.0.1:'+str(srv.server_address[1])+'/index.html'
errors=[];frames=[];observed={}
with sync_playwright() as p:
 br=p.chromium.launch(channel='chrome',headless=True,args=['--autoplay-policy=no-user-gesture-required'])
 page=br.new_page(viewport={'width':1333,'height':750},has_touch=True)
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(base+'?slide=10',wait_until='load')
 page.wait_for_function('document.querySelector(".adventure-game")?.dataset.state==="playing" && !isPlaying',timeout=25000)
 page.locator('.adv-choice').filter(has_text=re.compile('^तारे$')).tap()
 page.wait_for_selector('.journey-map[data-level="4"]',timeout=25000)
 end=time.monotonic()+7
 while time.monotonic()<end:
  info=page.evaluate('''()=>{const m=document.querySelector('.journey-map[data-level="4"]'),s=m?.querySelector('.journey-swifty');return m?{phase:m.dataset.tunnelPhase,state:m.dataset.state,opacity:+getComputedStyle(s).opacity,x:parseFloat(getComputedStyle(s).left)+48}:null;}''')
  if not info:break
  frames.append(page.screenshot())
  phase=info.get('phase')
  if phase:
   observed.setdefault(phase,[]).append(info)
   if phase in ['entering','inside','exiting'] and len(observed[phase])==1:(OUT/('tunnel-'+phase+'.png')).write_bytes(frames[-1])
  if info['state']=='ready':break
  page.wait_for_timeout(60)
 assert 'inside' in observed and 'exiting' in observed,observed.keys()
 assert min(i['opacity'] for i in observed['inside'])<.05,observed['inside']
 assert max(i['x'] for i in observed['exiting'])>890
 page.wait_for_function('document.querySelector(".journey-map")?.dataset.state==="ready"',timeout=5000)
 assert page.locator('.journey-swifty').evaluate('(e)=>getComputedStyle(e).opacity')=='1'
 assert not errors,errors
 br.close()
srv.shutdown()
try:
 from PIL import Image
 images=[Image.open(io.BytesIO(f)).convert('RGB').resize((960,540)) for f in frames]
 images[0].save(OUT/'tunnel-crossing.gif',save_all=True,append_images=images[1:],duration=130,loop=0)
except ImportError:pass
print('PASS real tunnel answer -> map: enter left portal, hide under roof, emerge at right, arrive at stairs; no browser errors')
