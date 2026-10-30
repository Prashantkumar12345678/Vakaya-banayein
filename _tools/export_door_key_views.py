from pathlib import Path
from PIL import Image
import shutil,json
r=Path.cwd();a=r/'HI02H12_L02_S01/assets/Images/adventure';m=r/'_masters/art'
src=m/'door_key_angles_source.png'
im=Image.open(src).convert('RGBA');print(im.size)
frames=[('front',Image.open(a/'key.webp').convert('RGBA'),(0,0,1400,372),(35,160),.3),('approach',im,(0,0,875,724),(65,195),.5),('inserted',im,(875,0,1520,724),(935,225),.5),('turned',im,(1520,0,2172,724),(1605,230),.5)]
for name,image,rect,anchor,factor in frames:
 cut=image.crop(rect);bbox=cut.getchannel('A').point(lambda v:255 if v>100 else 0).getbbox();box=(bbox[0]+rect[0],bbox[1]+rect[1],bbox[2]+rect[0],bbox[3]+rect[1]);cut=image.crop(box)
 cut=cut.resize((round(cut.width*factor),round(cut.height*factor)),Image.Resampling.LANCZOS)
 dst=Image.new('RGBA',(512,320));xy=(round(48-(anchor[0]-box[0])*factor),round(70-(anchor[1]-box[1])*factor));dst.alpha_composite(cut,xy);dst.save(a/('key_'+name+'.webp'),quality=96,method=6)
 print(name,box,xy,cut.size)
