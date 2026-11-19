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
record_frames=[]
card=json.loads((ROOT/'HI02H12_L02_S01/card.json').read_text())
expected=['मीरा पौधों को पानी दे रही है।','बिल्ली टोकरी में सो रही है।','बच्चा प्यासा है, उसे पानी चाहिए।','रात के समय आसमान में तारे चमकते हैं।','लड़की गाना गा रही है।','बकरी पत्ते खा रही है।']
B=next(i for i,s in enumerate(card['slides']) if s['id']=='P1')   # first game slide (G1 was removed 2026-11-19)
for n,slide in enumerate(card['slides'][B:B+6]):
 answer=next((o['label'] for o in slide['data'].get('options',[]) if o.get('correct')),'')
 assert slide['data']['sentence'].replace('___',answer)==expected[n]
with sync_playwright() as p:
 br=p.chromium.launch(channel='chrome',headless=True,args=['--autoplay-policy=no-user-gesture-required'])
 context=br.new_context(viewport={'width':1333,'height':750},has_touch=True)
 page=context.new_page()
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('response',lambda r:errors.append('HTTP '+str(r.status)+' '+r.url) if r.status>=400 else None)
 page.goto(base+'?slide=%d'%(B+1),wait_until='load');page.wait_for_selector('.adventure-game')   # Game 2 first: Game 1 is now a ghost-hand demo
 def ready():
  page.wait_for_function('''document.querySelector('.adventure-game')?.dataset.state==='playing' && document.querySelector('.adventure-game.adv-opts-done') && !isPlaying && !state.locked && !state.hintActive && !document.querySelector('.adv-fitting') && [...document.querySelectorAll('.adv-choice')].every(t=>!t._bridgeCanFit||t._bridgeCanFit())''',timeout=60000)   # the map intro before Game 1 runs ~25s
  page.wait_for_timeout(80)
 def tap(word):
  ready();tile=page.locator('.adv-choice').filter(has_text=re.compile('^'+re.escape(word)+'$'));tile.tap(force=True);page.wait_for_timeout(100)
 def placed(n):page.wait_for_function('(n)=>Number(document.querySelector(".adventure-game").dataset.filled)===n',arg=n,timeout=5000)
 ready()
 wrong=[o['label'] for o in card['slides'][B+1]['data']['options'] if not o.get('correct')]
 for word in [wrong[0],wrong[1],wrong[0]]:
  tap(word);ready()
 assert page.evaluate('state.attempts')==3
 assert page.locator('.adventure-game .reveal-hold').count()==1
 print('PASS P2 wrong attempts, feedback and terminal reveal',flush=True)
 # Game 1: the ghost hand plays it by itself - nobody taps
 page.goto(base+'?slide=%d'%B,wait_until='load');page.wait_for_selector('.adventure-game')
 page.wait_for_selector('.adv-ghost-hand',timeout=90000)
 for _ in range(10):record_frames.append(page.screenshot());page.wait_for_timeout(150)   # the hand carrying the plank
 page.wait_for_function('!document.querySelector(".adv-ghost-hand") && !document.querySelector(".adventure-game.adv-ghosting") && !state.locked && !isPlaying',timeout=30000)
 assert page.evaluate('Number(document.querySelector(".adventure-game").dataset.filled||0)')==0, 'the demo must leave the gap for the child'
 pick=page.locator('.adv-choice').filter(has_text=re.compile('^पानी$'))
 pick.click(force=True);page.wait_for_timeout(600)          # a plain tap does not answer - it shows the drag again
 assert page.evaluate('Number(document.querySelector(".adventure-game").dataset.filled||0)')==0
 page.wait_for_function('!document.querySelector(".adv-ghost-hand")',timeout=15000);page.wait_for_timeout(300)
 a=pick.bounding_box();g=page.locator('.adv-deck .sent-blank').bounding_box()
 page.mouse.move(a['x']+a['width']/2,a['y']+a['height']/2);page.mouse.down()
 for t in range(1,13):
  page.mouse.move(a['x']+a['width']/2+(g['x']+g['width']/2-a['x']-a['width']/2)*t/12,a['y']+a['height']/2+(g['y']+g['height']/2-a['y']-a['height']/2)*t/12);page.wait_for_timeout(30)
  if t==8:record_frames.append(page.screenshot())
 page.mouse.up();placed(1)
 page.wait_for_function('document.querySelector(".adventure-game").dataset.state==="resolving"',timeout=30000)
 for _ in range(8):record_frames.append(page.screenshot());page.wait_for_timeout(150)    # the walk across
 print('PASS P1 ghost hand shows the drag, the child drags पानी in',flush=True)
 for idx in range(B+1,B+6):
  page.wait_for_function('(i)=>state.idx===i',arg=idx,timeout=30000);ready()
  assert page.locator('.bridge-progress,.bridge-title,.bridge-instruction,.adv-drag-ghost').count()==0
  assert page.locator('.audio-chip').is_visible()==False
  if idx!=B:page.locator('.adventure-game').screenshot(path=str(OUT/('actual-P'+str(idx-B+1)+'.png')))
  s=card['slides'][idx]
  if s['type']=='SENTENCE_CLOZE':
   answer=next(o['label'] for o in s['data']['options'] if o.get('correct'))
   tap(answer);placed(1)
   assert page.locator('.adv-key-insertion' if idx==B+1 else '.adv-piece-flight').count()==1
   if idx==B:
    for _ in range(4):record_frames.append(page.screenshot());page.wait_for_timeout(120)
   page.wait_for_timeout(900)
   assert page.locator('.adv-deck').inner_text().split()==s['data']['sentence'].replace('___',answer).split()
  else:
   if idx==B+4:
    for n in range(3):tap('खेल');ready()
    assert page.locator('.reveal-hold').count()==1
   for n,word in enumerate(s['data']['sentence'].split()):
    tap(word);placed(n+1)
   page.wait_for_timeout(1000)
   assert page.locator('.adv-deck .wb-word').all_text_contents()==s['data']['sentence'].split()
  page.wait_for_function('document.querySelector(".adventure-game").dataset.state==="resolving"',timeout=20000)
  if idx==B:
   bridge_walk_positions=[]
   for k in range(48):   # the whole crossing (5.6s): it first goes up the sand on the left, then across the deck
    if page.locator('.adv-walker.is-walking').count():bridge_walk_positions.append(page.locator('.adv-walker').evaluate('(e)=>parseFloat(getComputedStyle(e).left)'))
    if k%6==0:record_frames.append(page.screenshot())
    page.wait_for_timeout(120)
  else:page.wait_for_timeout(2000)
  if idx in [B+1,B+3,B+5]:assert page.locator('.adv-open').count()==1
  if idx==B:
   assert bridge_walk_positions and max(bridge_walk_positions)>100, bridge_walk_positions
  page.locator('.adventure-game').screenshot(path=str(OUT/('action-P'+str(idx-B+1)+'.png')))
  page.wait_for_function('(i)=>state.idx===i+1',arg=idx,timeout=22000)
  print('PASS',s['id'],'single touch, correct words, animation and automatic progression',flush=True)
 page.wait_for_selector('#endScreen.show',timeout=12000)
 page.evaluate('mountSlide(3)')   # a guided screen
 assert page.locator('.adventure-game').count()==0
 assert not page.locator('.stage').evaluate('(e)=>e.classList.contains("bridge-mode")')
 assert not errors,errors
 print('PASS original questions preserved, celebration reached, guided restored, no browser errors',flush=True)
 context.close()
 try:
  from PIL import Image
  from io import BytesIO
  frames=[Image.open(BytesIO(b)).convert('RGB').resize((800,450)) for b in record_frames]
  frames[0].save(OUT/'bridge-play-through.gif',save_all=True,append_images=frames[1:],duration=150,loop=0)
  print('Saved actual tap/bridge-walk GIF',flush=True)
 except ImportError:print('Pillow unavailable; screenshot evidence saved instead of GIF',flush=True)
 br.close()
srv.shutdown()
