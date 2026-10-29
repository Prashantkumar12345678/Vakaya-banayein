"""Check map routes join at all six asset pads and inspect actual animated stop positions."""
from pathlib import Path
import functools,http.server,socketserver,threading,json,shutil
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
errors=[]
with sync_playwright() as p:
 br=p.chromium.launch(channel='chrome',headless=True,args=['--autoplay-policy=no-user-gesture-required'])
 page=br.new_page(viewport={'width':1333,'height':750})
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(base+'?slide=3',wait_until='load');page.wait_for_selector('#slideHost')
 nodes,routes=page.evaluate('[ADVENTURE_MAP_NODES,ADVENTURE_MAP_ROUTES]')
 assert len(nodes)==len(routes)==6
 for i,route in enumerate(routes):
  assert route[-1]==nodes[i]
  if i:assert route[0]==nodes[i-1]
  assert all(0<x<1333 and 141<y<750 for x,y in route)
  page.evaluate('(i)=>showAdventureMap(i,()=>{})',i)
  page.wait_for_function('document.querySelector(".journey-map")?.dataset.state==="ready"',timeout=10000)
  actual=page.locator('.journey-swifty').evaluate('(e)=>[parseFloat(e.style.left)+48,parseFloat(e.style.top)+141]')
  assert actual==nodes[i],(i,actual,nodes[i])
  marker=page.locator('.journey-landmark.is-current').evaluate('(e)=>[parseFloat(e.style.left)+e.offsetWidth/2,parseFloat(e.style.top)+e.offsetHeight/2]')
  assert marker==nodes[i],(i,marker,nodes[i])
  page.locator('.journey-map').screenshot(path=str(OUT/('map-stop-'+str(i+1)+'.png')))
  print('PASS map stop',i+1,'sprite feet and marker aligned',flush=True)
 shutil.copy2(OUT/'map-stop-6.png',OUT/'map-placement-updated.png')
 assert not errors,errors
 br.close()
srv.shutdown()
print('PASS all route endpoints joined; all six real map arrivals and marker positions; no browser errors')
