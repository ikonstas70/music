"""Build a searchable A–Z + by-date catalog of every released track, from albums/*.html."""
import glob, html, os, re, unicodedata, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GREEK = dict(zip("αβγδεζηθικλμνξοπρσςτυφχψω",["a","v","g","d","e","z","i","th","i","k","l","m","n","x","o","p","r","s","s","t","y","f","ch","ps","o"]))
def slugify(t):
    t="".join(c for c in unicodedata.normalize("NFD",t.lower()) if unicodedata.category(c)!="Mn")
    t="".join(GREEK.get(c,c) for c in t)
    return re.sub(r"[^a-z0-9]+","-",t).strip("-")

MONTHS={m:i for i,m in enumerate(["January","February","March","April","May","June","July","August","September","October","November","December"],1)}
def parse_date(meta):
    m=re.search(r'Released\s+([A-Z][a-z]+)\s+(\d{1,2}),\s*(\d{4})',meta)
    if m: return datetime.date(int(m.group(3)),MONTHS[m.group(1)],int(m.group(2)))
    y=re.search(r'\b(20\d{2})\b',meta)
    return datetime.date(int(y.group(1)),1,1) if y else None

tracks=[]  # {title, album, date, url}
for ap in sorted(glob.glob(os.path.join(ROOT,"albums","*.html"))):
    s=open(ap,encoding="utf-8").read()
    h1=re.search(r'<h1[^>]*>(.*?)</h1>',s,re.S)
    album=html.unescape(re.sub(r'<[^>]+>','',h1.group(1)).strip()) if h1 else os.path.basename(ap)[:-5]
    meta=re.search(r'<p class="meta"[^>]*>(.*?)</p>',s,re.S)
    metatxt=html.unescape(re.sub(r'<[^>]+>','',meta.group(1))) if meta else ""
    d=parse_date(metatxt)
    for b in re.findall(r'<button[^>]*class="tt"[^>]*>(.*?)</button>',s,re.S):
        title=html.unescape(re.sub(r'<[^>]+>','',b).strip())
        if not title: continue
        slug=slugify(title)
        tp=os.path.join(ROOT,"tracks",slug+".html")
        url=f"/music/tracks/{slug}.html" if os.path.exists(tp) else f"/music/albums/{os.path.basename(ap)}"
        tracks.append({"title":title,"album":album,"date":d,"url":url})

# dedupe by (title,album)
seen=set(); uniq=[]
for t in tracks:
    k=(t["title"].lower(),t["album"].lower())
    if k in seen: continue
    seen.add(k); uniq.append(t)
tracks=uniq
print(f"{len(tracks)} tracks across {len(set(t['album'] for t in tracks))} releases")

def esc(x): return html.escape(x or "")
def datestr(d): return d.strftime("%b %-d, %Y") if d else "—"

# A–Z grouping
azrows=[]
for t in sorted(tracks,key=lambda x:slugify(x["title"]) or "~"):
    first=(slugify(t["title"])[:1] or "#").upper()
    if not first.isalpha(): first="#"
    azrows.append((first,t))
# by date (newest first)
bydate=sorted(tracks,key=lambda x:(x["date"] or datetime.date(1900,1,1)),reverse=True)

def row(t):
    return (f'<li class="cat-row" data-title="{esc(t["title"].lower())}" data-album="{esc(t["album"].lower())}">'
            f'<a href="{t["url"]}"><span class="cat-t">{esc(t["title"])}</span>'
            f'<span class="cat-a">{esc(t["album"])}</span>'
            f'<span class="cat-d">{datestr(t["date"])}</span></a></li>')

az_html=""; cur=None
for first,t in azrows:
    if first!=cur:
        if cur is not None: az_html+="</ul>"
        az_html+=f'<h3 class="cat-letter" id="ltr-{first}">{first}</h3><ul class="cat-list">'
        cur=first
    az_html+=row(t)
az_html+="</ul>"
date_html='<ul class="cat-list">'+''.join(row(t) for t in bydate)+'</ul>'

page=f'''<!DOCTYPE html>
<html lang="en">
<head>
<link rel="canonical" href="https://ikonstas70.github.io/music/catalog.html">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Catalog — Ioannis Alexander Konstas Music</title>
<meta name="description" content="Full searchable catalog of {len(tracks)} tracks by Ioannis Alexander Konstas — browse alphabetically or by release date.">
<meta name="author" content="Ioannis Alexander Konstas">
<meta property="og:type" content="website">
<meta property="og:url" content="https://ikonstas70.github.io/music/catalog.html">
<meta property="og:title" content="Catalog — Ioannis Alexander Konstas Music">
<meta property="og:description" content="Full searchable catalog of {len(tracks)} tracks — alphabetical and by date.">
<meta property="og:image" content="https://ikonstas70.github.io/music/share/discography.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://ikonstas70.github.io/music/share/discography.jpg">
<link rel="stylesheet" href="/music/style.css">
<style>
.cat-tools{{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin:18px 0 10px}}
.cat-search{{flex:1 1 260px;min-width:220px;padding:12px 14px;border:1px solid var(--border);border-radius:10px;background:var(--card);color:var(--fg);font-size:1rem}}
.cat-search:focus{{outline:none;border-color:var(--accent)}}
.cat-toggle{{display:flex;border:1px solid var(--border);border-radius:10px;overflow:hidden}}
.cat-toggle button{{background:var(--card);color:var(--fg-dim);border:0;padding:12px 16px;font-size:.85rem;letter-spacing:.06em;text-transform:uppercase;cursor:pointer}}
.cat-toggle button.on{{background:var(--accent);color:#0a0a0a}}
.cat-count{{color:var(--fg-dim);font-size:.85rem;margin:4px 0 14px}}
.cat-letter{{color:var(--accent);font-family:var(--serif);margin:22px 0 6px;border-bottom:1px solid var(--border);padding-bottom:4px}}
.cat-list{{list-style:none;margin:0 0 6px;padding:0}}
.cat-row a{{display:grid;grid-template-columns:1fr auto auto;gap:14px;align-items:baseline;
  padding:10px 12px;border-radius:8px;text-decoration:none;color:var(--fg);border-bottom:1px solid hsl(0 0% 100% / .04)}}
.cat-row a:hover{{background:var(--card)}}
.cat-t{{font-weight:600}}
.cat-a{{color:var(--fg-dim);font-size:.85rem;text-align:right}}
.cat-d{{color:var(--accent-dim);font-size:.8rem;white-space:nowrap;min-width:92px;text-align:right}}
.cat-empty{{color:var(--fg-dim);padding:20px 0}}
@media(max-width:560px){{.cat-row a{{grid-template-columns:1fr auto}}.cat-a{{display:none}}}}
</style>
</head>
<body>
<div class="wrap">
  <header class="site">
    <a class="brand" href="/music/">Ioannis Alexander Konstas<em>.</em></a>
    <div class="tagline">Original Music</div>
    <div class="rule"></div>
    <nav class="top">
      <a href="/music/">Discography</a>
      <a href="/music/catalog.html" class="active">Catalog</a>
      <a href="https://open.spotify.com/artist/7gbVmhIUyDkCw47jHlkiTF">Spotify Profile</a>
    </nav>
  </header>
  <main>
    <h1 style="text-align:center">Catalog</h1>
    <p class="section-intro">Every released track &mdash; search by name, or browse A&ndash;Z and by date. Tap any title to play.</p>
    <div class="cat-tools">
      <input class="cat-search" id="q" type="search" placeholder="Search {len(tracks)} tracks&hellip;" autocomplete="off">
      <div class="cat-toggle">
        <button id="t-az" class="on" type="button">A&ndash;Z</button>
        <button id="t-date" type="button">By date</button>
      </div>
    </div>
    <p class="cat-count" id="count"></p>
    <div id="view-az">{az_html}</div>
    <div id="view-date" hidden>{date_html}</div>
    <p class="cat-empty" id="empty" hidden>No tracks match your search.</p>
  </main>
  <footer class="site">
    <p>&copy; 2026 Ioannis Konstas &middot; <a href="https://github.com/ikonstas70">github.com/ikonstas70</a></p>
    <a class="artist-link" href="https://pulseintimetunes.agency/player.html" style="margin-top:14px;">&#9654;&nbsp; Pulse In Time Tunes &mdash; Player</a>
  </footer>
</div>
<script>
(function(){{
  var q=document.getElementById("q"),az=document.getElementById("view-az"),dt=document.getElementById("view-date"),
      taz=document.getElementById("t-az"),tdt=document.getElementById("t-date"),
      count=document.getElementById("count"),empty=document.getElementById("empty");
  var rows=[].slice.call(document.querySelectorAll(".cat-row"));
  var total={len(tracks)};
  function cur(){{return dt.hidden?az:dt;}}
  function filter(){{
    var s=q.value.trim().toLowerCase(),shown=0;
    rows.forEach(function(r){{
      var m=!s||r.getAttribute("data-title").indexOf(s)>-1||r.getAttribute("data-album").indexOf(s)>-1;
      r.style.display=m?"":"none";
    }});
    // hide empty letter headers in az view
    cur().querySelectorAll(".cat-letter").forEach(function(h){{
      var ul=h.nextElementSibling,any=false,n=ul&&ul.firstElementChild;
      while(n){{if(n.style.display!=="none"){{any=true;break;}}n=n.nextElementSibling;}}
      h.style.display=any?"":"none";
    }});
    shown=cur().querySelectorAll('.cat-row:not([style*="display: none"])').length;
    count.textContent=s?(shown+" of "+total+" tracks"):(total+" tracks");
    empty.hidden=shown>0;
  }}
  function show(which){{
    var d=which==="date";dt.hidden=!d;az.hidden=d;
    tdt.classList.toggle("on",d);taz.classList.toggle("on",!d);filter();
  }}
  q.addEventListener("input",filter);
  taz.addEventListener("click",function(){{show("az");}});
  tdt.addEventListener("click",function(){{show("date");}});
  filter();
}})();
</script>
</body>
</html>'''
open(os.path.join(ROOT,"catalog.html"),"w",encoding="utf-8").write(page)
print("wrote catalog.html")
