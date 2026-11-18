"""Assemble fixed-body talking poses: complete gesture drawings + five registered beak shapes.
Only mouth pixels differ within a pose. Gesture changes happen between narration lines.
"""
from pathlib import Path
from collections import deque
import hashlib,json,wave,re,shutil,math
import numpy as np
from PIL import Image,ImageChops,ImageFilter,ImageDraw
ROOT=Path(__file__).resolve().parents[1];UI=ROOT/'HI02H12_L02_S01/assets/UI';ART=ROOT/'_masters/art';OUT=ROOT/'_previews/intro-speaking-v2';OUT.mkdir(parents=True,exist_ok=True)
G=Path('/Users/prashantkumar/.codex/generated_images/01a18226-aebf-7240-a921-e0149e214702')
for src,dst in [('exec-066be8c9-42fc-4661-91ce-13338c8da434.png','swifty_intro_gestures_source.png'),('exec-45728d78-eb7e-42f8-ae13-f7fb0c10a5ec.png','swifty_intro_mouths_source.png')]:
 if not (ART/dst).exists():shutil.copy2(G/src,ART/dst)

def biggest(mask):
 ar=np.array(mask)>0;h,w=ar.shape;seen=np.zeros((h,w),bool);best=[]
 for y,x in zip(*np.nonzero(ar)):
  if seen[y,x]:continue
  seen[y,x]=True;q=deque([(int(x),int(y))]);part=[]
  while q:
   x,y=q.popleft();part.append((x,y))
   for nx,ny in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
    if 0<=nx<w and 0<=ny<h and ar[ny,nx] and not seen[ny,nx]:seen[ny,nx]=True;q.append((nx,ny))
  if len(part)>len(best):best=part
 out=np.zeros((h,w),np.uint8)
 for x,y in best:out[y,x]=255
 return Image.fromarray(out)
base=Image.open(UI/'sw_explain_still.webp').convert('RGBA');gest=Image.open(ART/'swifty_intro_gestures_chubby_source.png').convert('RGBA');mouth=Image.open(ART/'swifty_intro_mouths_source.png').convert('RGBA')
beaks=[]
for i in range(5):
 x0=round(i*mouth.width/5);x1=round((i+1)*mouth.width/5);crop=mouth.crop((x0,230,x1,535));a=np.array(crop);r,g,b,al=[a[:,:,k].astype(float) for k in range(4)]
 colored=(r>g*1.08)&(r>b*1.07)&(al>100);colored[:15]=False;colored[:,:75]=False;colored[:,365:]=False
 m=biggest(Image.fromarray((colored*255).astype('uint8'))).filter(ImageFilter.MaxFilter(3));crop.putalpha(ImageChops.multiply(crop.getchannel('A'),m))
 beaks.append(crop)
frames=[];poses=[];W,H=380,410
# Preserve each complete connected drawing: never cut out or paste a separate head.
for pose in range(3):
 art_pose=pose   # body-reference source is already point, chest, open palms
 x0=round(art_pose*gest.width/3);x1=round((art_pose+1)*gest.width/3)
 im=gest.crop((x0+12,12,x1-12,gest.height-12));alpha=im.getchannel('A');m=biggest(alpha.point(lambda v:255 if v>100 else 0)).filter(ImageFilter.MaxFilter(3));im.putalpha(ImageChops.multiply(alpha,m));bb=im.getbbox();im=im.crop(bb)
 scale=400/im.height
 # Anchor by the head and beak, independent of the width of the outstretched arms.
 hb=im.getchannel('A').crop((0,0,im.width,round(im.height*.30))).getbbox();head_x=(hb[0]+hb[2])/2
 region=(round(head_x-im.width*.23),round(im.height*.25),round(head_x+im.width*.23),round(im.height*.43))
 raw=np.array(im.crop(region));rr,gg,bb,aa=[raw[:,:,k].astype(float) for k in range(4)]
 bm=biggest(Image.fromarray((((rr>gg*1.07)&(gg>50)&(bb<180)&(aa>100))*255).astype('uint8')));beak_box=bm.getbbox()
 bx=(beak_box[0]+beak_box[2])/2+region[0];by=beak_box[1]+region[1]
 beak_width=(beak_box[2]-beak_box[0])*scale
 offset_x=round(W/2-bx*scale)
 im=im.resize((round(im.width*scale),400),Image.Resampling.LANCZOS)
 body=Image.new('RGBA',(W,H));body.alpha_composite(im,(offset_x,10))
 hx=W/2;hy=round(10+by*scale)-1
 # Replace only the old beak's opening. The neck, sleeves, hands and hoodie stay intact.
 box=(round(hx-40),hy-5,round(hx+41),hy+66);patch=Image.new('RGBA',(81,71));px=patch.load();bp=body.load()
 L,R=bp[round(hx-40),hy+28],bp[round(hx+40),hy+28]
 for y in range(71):
  for x in range(81):
   t=x/80;px[x,y]=tuple(round(L[k]*(1-t)+R[k]*t) for k in range(4))
 mask=Image.new('L',(81,71))
 pts=[(-33,19),(-20,12),(-10,-3),(8,-3),(19,10),(34,20),(34,31),(23,49),(7,64),(-10,64),(-26,46),(-35,28)]
 ImageDraw.Draw(mask).polygon([(round(hx+x)-box[0],hy+y-box[1]) for x,y in pts],fill=255)
 mask=mask.filter(ImageFilter.GaussianBlur(.7));body.paste(patch,box[:2],mask)
 pose_frames=[]
 for beak in beaks:
  f=body.copy();factor=beak_width/260
  part=beak.resize((round(beak.width*factor),round(beak.height*factor)),Image.Resampling.LANCZOS)
  f.alpha_composite(part,(round(hx-220*factor),round(hy-(265-230)*factor)))
  frames.append(f);pose_frames.append(f)
 poses.append(pose_frames)
sheet=Image.new('RGBA',(W*5,H*3));strip=Image.new('RGBA',(W*15,H))
for i,f in enumerate(frames):sheet.paste(f,((i%5)*W,(i//5)*H));strip.paste(f,(i*W,0))
sheet.save(UI/'swifty_intro_speech_v2_sheet.png');strip.save(UI/'swifty_intro_speech_v2_strip.webp',lossless=True,exact=True,method=6)
# Within each gesture all non-mouth pixels must be byte-identical: no body or head bobbing.
for pose in poses:
 ref=np.array(pose[0]);outside=np.ones((H,W),bool);outside[105:210,145:240]=False
 for f in pose[1:]:assert np.array_equal(np.array(f)[outside],ref[outside]),'Non-mouth pixels moved'
cues={};analysis={}
for n in range(1,4):
 p=ROOT/f'HI02H12_L02_S01/assets/VO/vo_map_intro{n}.wav'
 with wave.open(str(p),'rb') as wav:
  rate=wav.getframerate();samples=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2').reshape(-1,wav.getnchannels()).mean(axis=1)/32768
 step=round(rate*.05);env=np.array([np.sqrt(np.mean(samples[i:i+step]**2)) for i in range(0,len(samples),step)]);env=np.convolve(np.pad(env,(1,1),mode='edge'),[.15,.7,.15],mode='valid')
 threshold=max(.010,float(env.max())*.045);active=np.flatnonzero(env>threshold);ref=float(np.percentile(env[active],80));cue=[]
 for i,v in enumerate(env):
  if v<=threshold:shape=0
  elif v/ref<.30:shape=1
  elif v/ref<.72:shape=2
  elif i%7 in [2,3] and v/ref<1.15:shape=4
  else:shape=3
  cue.append((n-1)*5+shape)
 cue[-1]=(n-1)*5;cues[str(n)]=cue
 analysis[str(n)]={'duration_ms':round(len(samples)/rate*1000),'gesture':['point to map','hand to chest','both palms explaining'][n-1],'rest_frame':(n-1)*5,'audio_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 seq=[frames[f] for f in cue];seq[0].save(OUT/f'line-{n}.webp',save_all=True,append_images=seq[1:],duration=50,loop=0,lossless=True,method=4)
 seq[0].save(OUT/f'line-{n}.gif',save_all=True,append_images=seq[1:],duration=50,loop=0,disposal=2)
p=ROOT/'HI02H12_L02_S01/index.html';s=p.read_text();s=re.sub(r'const JOURNEY_SPEECH_CUES=.*?;',lambda _:'const JOURNEY_SPEECH_CUES='+json.dumps(cues,separators=(',',':'))+';',s);p.write_text(s)
meta={'method':'Complete connected character drawings with independently registered 5 beak shapes and 3 stable hand gestures; no head/body cutout or neck seam. All pixels outside the mouth are identical within each gesture. Gesture changes only between lines.','frame_size':[W,H],'frame_count':15,'sheet_grid':[5,3],'step_ms':50,'rest_frames':[0,5,10],'audio_analysis':analysis,'cues':cues,'original_still_sha256':hashlib.sha256((UI/'sw_explain_still.webp').read_bytes()).hexdigest(),'source_gestures':'_masters/art/swifty_intro_gestures_chubby_source.png','body_reference':'HI02H12_L02_S01/assets/Images/last_swifty_end.webp','source_mouths':'_masters/art/swifty_intro_mouths_source.png'}
meta.update({'tool': 'Built-in image_gen for gesture and mouth source art; registered sprite assembly', 'body_reference_prompt': '_masters/art/SWIFTY_INTRO_BODY_REFERENCE_PROMPT.txt', 'prompts': '_masters/art/SWIFTY_INTRO_V2_PROMPTS.json', 'sheet': 'HI02H12_L02_S01/assets/UI/swifty_intro_speech_v2_sheet.png', 'strip': 'HI02H12_L02_S01/assets/UI/swifty_intro_speech_v2_strip.webp', 'preview_with_audio': '_previews/intro-speaking-v2/three-lines-with-audio.mp4'})
(ART/'SWIFTY_INTRO_SPEECH_V2.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
print('Built 3 stable gestures x 5 mouth shapes. All non-mouth pixels verified fixed per gesture.')
