"""Export the original-UI Swifty walking sheet, strip, GIF and alpha WebP.
Creative source: _masters/art/swifty_ui_walk_source.png, generated from UI/sw_explain_still.webp.
Run with Pillow available; this only normalizes frames and exports production formats.
"""
import argparse
from pathlib import Path
from collections import deque
from PIL import Image, ImageFilter, ImageChops
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'HI02H12_L02_S01/assets/UI'
parser=argparse.ArgumentParser()
parser.add_argument('--direction',choices=['right','front','back'],default='right')
args=parser.parse_args()
name='swifty_walk' if args.direction=='right' else 'swifty_walk_'+args.direction
source=Image.open(ROOT/('_masters/art/swifty_ui_walk_source.png' if args.direction=='right' else '_masters/art/swifty_ui_walk_angles_source.png')).convert('RGBA')
rows=2 if args.direction=='right' else 4
row_start=2 if args.direction=='back' else 0
raw=[]
for row in range(row_start,row_start+2):
 for col in range(4):
  x0,x1=round(col*source.width/4),round((col+1)*source.width/4)
  # Generated rows have slightly unequal spacing: cut at their actual transparent seams.
  cuts=[0,source.height]
  if rows==4:
   a=source.getchannel('A')
   cuts=[0]+[min(range(round(center)-30,round(center)+31),key=lambda y:sum(v>48 for v in a.crop((x0,y,x1,y+1)).getdata())) for center in [source.height/4,source.height/2,source.height*3/4]]+[source.height]
  else:cuts=[0,round(source.height/2),source.height]
  frame=source.crop((x0,cuts[row],x1,cuts[row+1]))
  w,h=frame.size;alpha=frame.getchannel('A');pixels=alpha.point(lambda a:255 if a>48 else 0).tobytes();seen=bytearray(w*h);best=[]
  for start in range(w*h):
   if seen[start] or not pixels[start]:continue
   q=deque([start]);seen[start]=1;component=[]
   while q:
    n=q.popleft();component.append(n);x=n%w
    for v in ([n-1] if x else [])+([n+1] if x<w-1 else [])+([n-w] if n>=w else [])+([n+w] if n<w*(h-1) else []):
     if not seen[v] and pixels[v]:seen[v]=1;q.append(v)
   if len(component)>len(best):best=component
  keep=bytearray(w*h)
  for n in best:keep[n]=255
  keep=Image.frombytes('L',(w,h),bytes(keep)).filter(ImageFilter.MaxFilter(3));frame.putalpha(ImageChops.multiply(alpha,keep))
  bbox=frame.getchannel('A').point(lambda a:255 if a>48 else 0).getbbox()
  head=frame.getchannel('A').crop((0,bbox[1],w,bbox[1]+int((bbox[3]-bbox[1])*.42))).point(lambda a:255 if a>48 else 0).getbbox()
  raw.append((frame,bbox,(head[0]+head[2])/2))
scale=min(246/(2*max(max(hx-b[0],b[2]-hx) for _,b,hx in raw)),372/max(b[3]-b[1] for _,b,_ in raw))
frames=[]
for original,bbox,head_x in raw:
 crop=original.crop(bbox);crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS)
 canvas=Image.new('RGBA',(256,384));x=round(128-(head_x-bbox[0])*scale);canvas.alpha_composite(crop,(x,378-crop.height));frames.append(canvas)
sheet=Image.new('RGBA',(1024,768));strip=Image.new('RGBA',(2048,384))
for i,f in enumerate(frames):sheet.alpha_composite(f,((i%4)*256,(i//4)*384));strip.alpha_composite(f,(i*256,0))
sheet.save(OUT/(name+'_sheet.png'));strip.save(OUT/(name+'_strip.webp'),quality=94,method=6)
frames[0].save(OUT/(name+'.webp'),save_all=True,append_images=frames[1:],duration=100,loop=0,quality=94,method=6)
contact=Image.new('RGB',(2048,384),'white')
for i,f in enumerate(frames):contact.paste(f,(i*256,0),f)
palette=contact.quantize(colors=255);gifs=[]
for f in frames:
 rgb=Image.new('RGB',f.size,'white');rgb.paste(f,mask=f.getchannel('A'));q=rgb.quantize(palette=palette,dither=Image.Dither.NONE);q.paste(255,mask=f.getchannel('A').point(lambda a:255 if a<100 else 0));gifs.append(q)
gifs[0].save(OUT/(name+'.gif'),save_all=True,append_images=gifs[1:],duration=100,loop=0,transparency=255,disposal=2)
print('Exported 8 matching UI frames: 4x2 PNG sheet, runtime strip, animated WebP and GIF.')
