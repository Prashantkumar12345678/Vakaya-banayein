"""Play the three map-intro recordings; check audio-clock sprites, pauses, mute and disposal."""
from pathlib import Path
import functools,http.server,socketserver,threading,time,io,json,hashlib
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'_previews/intro-speaking-v2';OUT.mkdir(parents=True,exist_ok=True)
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
class Server(socketserver.ThreadingTCPServer):
 allow_reuse_address=True
 daemon_threads=True
srv=Server(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'HI02H02_L02_S01')))
threading.Thread(target=srv.serve_forever,daemon=True).start();base='http://127.0.0.1:'+str(srv.server_address[1])+'/index.html'
meta=json.loads((ROOT/'_masters/art/SWIFTY_INTRO_SPEECH_V2.json').read_text());errors=[];seen={};frames=[];matched=0;samples=0;muted=False
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome',headless=True,args=['--autoplay-policy=no-user-gesture-required'])
 page=b.new_page(viewport={'width':1333,'height':750},has_touch=True)
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.on('response',lambda r:errors.append(str(r.status)+' '+r.url) if r.status>=400 else None)
 page.goto(base+'?slide=7',wait_until='load')
 page.wait_for_selector('.journey-map.is-intro .journey-guide-sprite',timeout=30000)
 assert page.locator('.journey-guide-sprite').evaluate('(e)=>[e.offsetWidth,Math.round(e.offsetHeight)]')==[204,220]
 deadline=time.monotonic()+24
 while time.monotonic()<deadline:
  info=page.evaluate('''()=>{const g=document.querySelector('.journey-guide'),s=g?.querySelector('.journey-guide-sprite'),v=currentVoiceSource;return g?{line:g.dataset.line,speaking:g.dataset.speaking,frame:+s.dataset.frame,vo:isPlaying,ms:v?.context.state==='running'?(v.context.currentTime-v._speechStartedAt)*1000:null,gone:g.classList.contains('is-gone')}:null;}''')
  if not info or info['gone']:break
  line=info['line'];assert info['frame']//5==int(line)-1,info;seen.setdefault(line,{'open':set(),'closed':0})
  if info['frame']%5==0:seen[line]['closed']+=1
  else:
   seen[line]['open'].add(info['frame'])
   if len(seen[line]['open'])==1:page.locator('.journey-map').screenshot(path=str(OUT/f'actual-line-{line}.png'))
  if info['ms'] is not None and info['speaking']=='true':
   cue=meta['cues'][line];i=min(len(cue)-1,max(0,int(info['ms']//50)));expected={cue[j] for j in range(max(0,i-2),min(len(cue),i+2))};samples+=1;matched+=info['frame'] in expected
  if line=='1' and len(frames)<24:frames.append(page.screenshot())
  if line=='2' and not muted:
   page.evaluate('isMuted=true');page.wait_for_timeout(70)
   assert page.locator('.journey-guide-sprite').get_attribute('data-frame')==str((int(page.locator('.journey-guide').get_attribute('data-line'))-1)*5)
   page.evaluate('isMuted=false');muted=True
  page.wait_for_timeout(70)
 assert set(seen)=={'1','2','3'},seen
 for line,values in seen.items():
  assert len(values['open'])>=2 and values['closed']>0,(line,values)
 assert matched/max(samples,1)>.90,(matched,samples)
 page.wait_for_selector('.adv-bridge[data-state="playing"]',timeout=18000)
 assert page.locator('.journey-guide').count()==0
 print('PASS all three real intro clips: multiple mouth/gesture frames, closed-mouth pauses, mute and audio-clock cues',matched,'/',samples,flush=True)
 # An active narration must stop immediately and the next screen must have no orphan sprite.
 page.evaluate('state.journeyIntroDone=false;mountSlide(7)')
 page.wait_for_selector('.journey-guide[data-speaking="true"]',timeout=15000)
 page.evaluate('stopAudio()');page.wait_for_timeout(80)
 assert page.locator('.journey-guide').get_attribute('data-speaking')=='false'
 assert page.locator('.journey-guide-sprite').get_attribute('data-frame')==str((int(page.locator('.journey-guide').get_attribute('data-line'))-1)*5)
 page.evaluate('mountSlide(3)');page.wait_for_timeout(500)
 assert page.locator('.journey-guide-sprite').count()==0
 assert not errors,errors
 b.close()
srv.shutdown()
assert hashlib.sha256((ROOT/'HI02H02_L02_S01/assets/UI/sw_explain_still.webp').read_bytes()).hexdigest()==meta['original_still_sha256']
from PIL import Image
images=[Image.open(io.BytesIO(x)).convert('RGB').resize((960,540)) for x in frames]
images[0].save(OUT/'actual-intro-speaking.gif',save_all=True,append_images=images[1:],duration=150,loop=0)
print('PASS audio stop and navigation clean speech; original Swifty still unchanged; no browser errors')
