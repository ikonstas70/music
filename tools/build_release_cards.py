import os,re,html
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageOps
M=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=f"{M}/share"; os.makedirs(OUT,exist_ok=True)
G="/System/Library/Fonts/Supplemental/"
F=lambda n,s:ImageFont.truetype(G+n,s)
AV=lambda i,s:ImageFont.truetype("/System/Library/Fonts/Avenir Next.ttc",s,index=i)
GOLD=(199,164,96); FG=(246,246,246); DIM=(170,170,170); BG=(10,10,10)
W,H=1200,630

t=open(f"{M}/index.html").read()
rel=[]
for slug,inner in re.findall(r'<a[^>]*href="(?:/music/)?albums/([^"]+)\.html"[^>]*>(.*?)</a>',t,re.S):
    txt=[html.unescape(x.strip()) for x in re.sub(r'<[^>]+>','\n',inner).split('\n') if x.strip()]
    cover=f"{M}/covers/{slug}.jpg"
    if not os.path.exists(cover): cover=f"{M}/cover-simeio-midev.jpg"
    rel.append((slug,txt[0],txt[1],cover))

def wrap(d,text,font,maxw):
    words=text.split(); lines=[]; cur=""
    for w in words:
        test=(cur+" "+w).strip()
        if d.textlength(test,font=font)<=maxw: cur=test
        else: lines.append(cur); cur=w
    lines.append(cur); return lines

def backdrop(cover):
    bg=ImageOps.fit(Image.open(cover).convert("RGB"),(W,H)).filter(ImageFilter.GaussianBlur(40))
    shade=Image.new("RGB",(W,H),BG); bg=Image.blend(bg,shade,0.72)
    # soft left-to-right vignette so the text side stays deep
    grad=Image.linear_gradient("L").rotate(90).resize((W,H)); grad=ImageOps.invert(grad)
    return Image.composite(bg,Image.new("RGB",(W,H),BG),grad.point(lambda v:int(90+v*.65)))

def frame_cover(img,cover,box,size):
    c=ImageOps.fit(Image.open(cover).convert("RGB"),(size,size))
    sh=Image.new("RGBA",(size+60,size+60),(0,0,0,0)); ImageDraw.Draw(sh).rectangle([30,34,size+30,size+34],fill=(0,0,0,170))
    sh=sh.filter(ImageFilter.GaussianBlur(16)); img.paste(sh,(box[0]-30,box[1]-30),sh)
    img.paste(c,box); ImageDraw.Draw(img).rectangle([box[0]-1,box[1]-1,box[0]+size,box[1]+size],outline=(60,52,36),width=1)

def release_lead(slug):
    p=f"{M}/albums/{slug}.html"
    if not os.path.exists(p): return ""
    m=re.search(r'<section class="release-notes".*?<p[^>]*>(.*?)</p>',open(p).read(),re.S)
    return html.unescape(re.sub(r"<[^>]+>","",m.group(1))).strip() if m else ""

def pill(d,x,y):
    pf=AV(2,20); label="LISTEN ON SPOTIFY"; tw=d.textlength(label,font=pf)
    d.rounded_rectangle([x,y,x+tw+78,y+52],radius=26,outline=GOLD,width=2)
    d.polygon([(x+26,y+17),(x+26,y+35),(x+41,y+26)],fill=GOLD)
    d.text((x+54,y+13),label,font=pf,fill=GOLD)

def card(slug,title,meta,cover):
    lead=release_lead(slug)
    img=backdrop(cover); d=ImageDraw.Draw(img)
    size=450; frame_cover(img,cover,(70,90),size)
    x=580; maxw=W-x-70
    d.text((x,112),"IOANNIS ALEXANDER KONSTAS",font=AV(2,21),fill=GOLD)
    d.rectangle([x,146,x+70,148],fill=GOLD)
    for s in (60,54,48,42,38,34):
        f=F("Georgia.ttf",s); lines=wrap(d,title,f,maxw)
        block=len(lines)*int(s*1.22)+14+26+34+52
        if block<=H-176-110: break
    y=176
    for ln in lines: d.text((x,y),ln,font=f,fill=FG); y+=int(s*1.22)
    y+=14; d.text((x,y),meta.upper().replace("·","  ·  "),font=AV(5,20),fill=DIM)
    if lead:
        lf=ImageFont.truetype(G+"Georgia Italic.ttf",23); y+=46; top=y
        for ln in wrap(d,lead,lf,maxw-24)[:4]: d.text((x+22,y),ln,font=lf,fill=(222,212,192)); y+=34
        d.rectangle([x,top+4,x+1,y-8],fill=GOLD)
        y-=18
    pill(d,x,max(y+60,H-170))
    d.text((x,H-72),"ikonstas70.github.io/music",font=AV(7,18),fill=(120,120,120))
    img.save(f"{OUT}/{slug}.jpg",quality=88,optimize=True,progressive=True)

def index_card():
    import hashlib
    img=Image.new("RGB",(W,H),BG); seen=set(); covs=[]
    thumbs=[]
    for r in rel:
        th=list(Image.open(r[3]).convert("L").resize((16,16)).getdata())
        if all(sum(abs(a-b) for a,b in zip(th,o))/256>28 for o in thumbs):
            thumbs.append(th); covs.append(r[3])
    covs=covs[:9]; tile=172; gap=8; ox=W-3*tile-2*gap-50; oy=(H-3*tile-2*gap)//2
    for i,c in enumerate(covs):
        img.paste(ImageOps.fit(Image.open(c).convert("RGB"),(tile,tile)),(ox+(i%3)*(tile+gap),oy+(i//3)*(tile+gap)))
    fade=Image.linear_gradient("L").rotate(90).resize((W,H))
    img=Image.composite(img,Image.new("RGB",(W,H),BG),fade.point(lambda v:int(min(255,max(0,(v-95)*2.2)))))
    d=ImageDraw.Draw(img); x=70
    d.text((x,140),"ORIGINAL MUSIC",font=AV(2,22),fill=GOLD); d.rectangle([x,176,x+70,178],fill=GOLD)
    d.text((x,202),"Ioannis Alexander",font=F("Georgia.ttf",50),fill=FG)
    d.text((x,264),"Konstas",font=F("Georgia.ttf",50),fill=FG)
    d.text((x,346),"30 RELEASES  ·  159 TRACKS",font=AV(5,21),fill=DIM)
    pill(d,x,400)
    d.text((x,H-72),"ikonstas70.github.io/music",font=AV(7,18),fill=(120,120,120))
    img.save(f"{OUT}/discography.jpg",quality=88,optimize=True,progressive=True)

for r in rel: card(*r)
index_card(); print(len(rel)+1,"cards")
