"""Build a shareable page + 1200x630 share card for every track on the site.

For each track listed in albums/*.html this writes:
  tracks/<slug>.html          page with cover, Spotify track player, links back to the release
  share/tracks/<slug>.jpg     wide link-preview card (Facebook, LinkedIn, X, iMessage, WhatsApp)

Album pages are read, never modified. Re-run any time a release is added:
    python3 tools/build_track_pages.py          (needs Pillow; macOS system fonts)
Then publish, and refresh Facebook's cache for a new link at
    https://developers.facebook.com/tools/debug/?q=<url>   ->  "Scrape Again"
"""
import collections
import glob
import html
import os
import re
import unicodedata

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://ikonstas70.github.io/music"
ARTIST_URL = "https://open.spotify.com/artist/7gbVmhIUyDkCw47jHlkiTF"

GEORGIA = "/System/Library/Fonts/Supplemental/Georgia.ttf"
AVENIR = "/System/Library/Fonts/Avenir Next.ttc"
GOLD, FG, DIM, BG = (199, 164, 96), (246, 246, 246), (170, 170, 170), (10, 10, 10)
W, H = 1200, 630

GREEK = dict(zip("αβγδεζηθικλμνξοπρσςτυφχψω", ["a", "v", "g", "d", "e", "z", "i", "th", "i", "k", "l", "m", "n", "x", "o", "p", "r", "s", "s", "t", "y", "f", "ch", "ps", "o"]))


def slugify(text):
    text = "".join(c for c in unicodedata.normalize("NFD", text.lower()) if unicodedata.category(c) != "Mn")
    text = "".join(GREEK.get(c, c) for c in text)
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def avenir(index, size):
    return ImageFont.truetype(AVENIR, size, index=index)


def wrap(draw, text, font, max_width):
    lines, cur = [], ""
    for word in text.split():
        test = (cur + " " + word).strip()
        if draw.textlength(test, font=font) <= max_width:
            cur = test
        else:
            lines.append(cur)
            cur = word
    return lines + [cur]


def share_card(title, meta, cover_path, out_path, lead=""):
    cover = Image.open(cover_path).convert("RGB")
    bg = ImageOps.fit(cover, (W, H)).filter(ImageFilter.GaussianBlur(40))
    bg = Image.blend(bg, Image.new("RGB", (W, H), BG), 0.72)
    grad = ImageOps.invert(Image.linear_gradient("L").rotate(90).resize((W, H)))
    img = Image.composite(bg, Image.new("RGB", (W, H), BG), grad.point(lambda v: int(90 + v * 0.65)))

    size, box = 450, (70, 90)
    shadow = Image.new("RGBA", (size + 60, size + 60), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rectangle([30, 34, size + 30, size + 34], fill=(0, 0, 0, 170))
    shadow = shadow.filter(ImageFilter.GaussianBlur(16))
    img.paste(shadow, (box[0] - 30, box[1] - 30), shadow)
    img.paste(ImageOps.fit(cover, (size, size)), box)

    d = ImageDraw.Draw(img)
    d.rectangle([box[0] - 1, box[1] - 1, box[0] + size, box[1] + size], outline=(60, 52, 36), width=1)
    x = 580
    max_width = W - x - 70
    d.text((x, 112), "IOANNIS ALEXANDER KONSTAS", font=avenir(2, 21), fill=GOLD)
    d.rectangle([x, 146, x + 70, 148], fill=GOLD)
    for s in (60, 54, 48, 42, 38, 34):
        font = ImageFont.truetype(GEORGIA, s)
        lines = wrap(d, title, font, max_width)
        if len(lines) * int(s * 1.22) + 126 <= H - 176 - 110:
            break
    y = 176
    for line in lines:
        d.text((x, y), line, font=font, fill=FG)
        y += int(s * 1.22)
    y += 14
    d.text((x, y), meta.upper().replace("·", "  ·  "), font=avenir(5, 20), fill=DIM)
    if lead:                                             # release/track description, italic, under the details line
        max_lines = 5
        for lsize in (23, 21, 19, 18, 17):                # shrink to fit rather than cut the quote off mid-sentence
            lead_font = ImageFont.truetype(GEORGIA.replace("Georgia.ttf", "Georgia Italic.ttf"), lsize)
            lh = int(lsize * 1.42)
            lines = wrap(d, lead, lead_font, max_width - 24)
            if len(lines) <= max_lines:
                break
        else:
            lines = lines[:max_lines]
            joined = " ".join(lines)
            cut = max(joined.rfind(". "), joined.rfind("! "), joined.rfind("? "))   # back off to a full sentence
            lines = wrap(d, joined[:cut + 1] if cut > 0 else joined, lead_font, max_width - 24)
        y += 46
        top = y
        for line in lines:
            d.text((x + 22, y), line, font=lead_font, fill=(222, 212, 192))
            y += lh
        d.rectangle([x, top + 4, x + 1, y - 8], fill=GOLD)   # thin gold rule beside the quote
        y -= 18

    py = max(y + 60, H - 170)
    label, pf = "LISTEN ON SPOTIFY", avenir(2, 20)
    tw = d.textlength(label, font=pf)
    d.rounded_rectangle([x, py, x + tw + 78, py + 52], radius=26, outline=GOLD, width=2)
    d.polygon([(x + 26, py + 17), (x + 26, py + 35), (x + 41, py + 26)], fill=GOLD)
    d.text((x + 54, py + 13), label, font=pf, fill=GOLD)
    d.text((x, H - 72), "ikonstas70.github.io/music", font=avenir(7, 18), fill=(120, 120, 120))
    img.save(out_path, quality=88, optimize=True, progressive=True)


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<link rel="canonical" href="{url}">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title_full}</title>
<meta name="description" content="{desc}">
<meta name="author" content="Ioannis Alexander Konstas">

<meta property="og:type" content="music.song">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{title_full}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{img}">
<meta property="og:image:secure_url" content="{img}">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{title} — {album} cover art">
<meta property="og:site_name" content="Ioannis Alexander Konstas — Music">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title_full}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{img}">

<link rel="stylesheet" href="/music/style.css">
</head>
<body>
<div class="wrap">
  <header class="site">
    <a class="brand" href="/music/">Ioannis Alexander Konstas<em>.</em></a>
    <div class="tagline">Original Music</div>
    <div class="rule"></div>
    <nav class="top">
      <a href="/music/">Discography</a>
      <a href="{artist}">Spotify Profile</a>
    </nav>
  </header>

  <main>
    <img class="album-cover" src="../covers/{cover_file}" alt="{cover_alt}">
    <h1 style="text-align:center">{title}</h1>
    <p class="meta" style="text-align:center">{meta_html}</p>
{notes_html}
    <div class="spotify-embed">
      <iframe src="https://open.spotify.com/embed/track/{track_id}?utm_source=oembed" width="100%" height="352" frameborder="0" allowfullscreen="" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" loading="lazy" title="Spotify Embed: {title}"></iframe>
    </div>

    <p style="text-align:center;"><a href="https://open.spotify.com/track/{track_id}">Listen on Spotify &rarr;</a></p>
    <a class="artist-link" href="{artist}">Follow on Spotify &middot; Ioannis Alexander Konstas</a>

    <p style="margin-top:32px;">{back_html} &nbsp;&middot;&nbsp; <a href="/music/">Discography</a></p>
  </main>

  <footer class="site">
    <p>&copy; 2026 Ioannis Konstas &middot; <a href="https://github.com/ikonstas70">github.com/ikonstas70</a></p>
  </footer>
</div>
</body>
</html>
"""

TRACK_RE = re.compile(r'<li><span class="tn">(\d+)</span><button type="button" class="tt" data-track-id="([^"]+)">(.*?)</button><span class="td">([^<]*)</span>')


def releases():
    for path in sorted(glob.glob(os.path.join(ROOT, "albums", "*.html"))):
        page = open(path, encoding="utf-8").read()
        album_slug = os.path.basename(path)[:-5]
        album = html.unescape(re.search(r'<h1[^>]*>(.*?)</h1>', page, re.S).group(1).strip())
        meta = html.unescape(re.sub(r"<[^>]+>", "", re.search(r'<p class="meta"[^>]*>(.*?)</p>', page, re.S).group(1)))
        kind = meta.split("·")[0].strip()                       # Album / EP / Single
        year = re.search(r"(20\d\d)", meta).group(1)
        cover_file = re.search(r'src="\.\./covers/([^"]+)"', page)
        cover_file = cover_file.group(1) if cover_file else None
        tracks = [(int(n), tid, html.unescape(t), dur) for n, tid, t, dur in TRACK_RE.findall(page)]
        # optional "About the Release" / "About the Track" sections. Untagged -> applies to every
        # track on the release. Tagged with data-track-id="<spotify id>" -> that one track only
        # (used for a compilation where the note is about a single song, not the whole release).
        release_notes, release_lead, notes_by_track = "", "", {}
        for m in re.finditer(r'<section class="release-notes"([^>]*)>.*?</section>', page, re.S):
            attrs, block = m.group(1), m.group(0)
            lead_m = re.search(r'<p[^>]*>(.*?)</p>', block, re.S)
            block_lead = html.unescape(re.sub(r"<[^>]+>", "", lead_m.group(1))).strip() if lead_m else ""
            tid_m = re.search(r'data-track-id="([^"]+)"', attrs)
            if tid_m:
                notes_by_track[tid_m.group(1)] = (re.sub(r'\s*data-track-id="[^"]+"', "", block), block_lead)
            else:
                release_notes, release_lead = block, block_lead
        yield dict(slug=album_slug, title=album, kind=kind, year=year, cover_file=cover_file, tracks=tracks,
                   notes=release_notes, lead=release_lead, notes_by_track=notes_by_track)


def main():
    os.makedirs(os.path.join(ROOT, "tracks"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "share", "tracks"), exist_ok=True)
    rels = list(releases())
    title_count = collections.Counter(slugify(t[2]) for r in rels for t in r["tracks"])
    built = []
    for r in rels:
        cover_file = r["cover_file"] or "../cover-simeio-midev.jpg"
        cover_path = os.path.normpath(os.path.join(ROOT, "covers", cover_file))
        for num, track_id, title, dur in r["tracks"]:
            base = slugify(title)
            slug = base if title_count[base] == 1 else f"{base}--{r['slug']}"   # same song on two releases
            if r["kind"] == "Single":
                card_meta = " · ".join(x for x in ("Single", dur, r["year"]) if x)
                meta_html = " &middot; ".join(x for x in (f'Single <a href="/music/albums/{r["slug"]}.html">{html.escape(r["title"])}</a>' if r["title"] != title else "Single", dur, r["year"]) if x)
                back_html = f'<a href="/music/albums/{r["slug"]}.html">&larr; Single page</a>'
                desc = f"{title} — single by Ioannis Alexander Konstas. Stream on Spotify."
            else:
                card_meta = " · ".join(x for x in (f"Track {num}", f"{r['kind']} “{r['title']}”", dur) if x)
                meta_html = " &middot; ".join(x for x in (f'Track {num} from the {r["kind"]} <a href="/music/albums/{r["slug"]}.html">{html.escape(r["title"])}</a>', dur, r["year"]) if x)
                back_html = f'<a href="/music/albums/{r["slug"]}.html">&larr; The full {r["kind"]}: {html.escape(r["title"])}</a>'
                desc = f"{title} — track {num} from the {r['kind']} “{r['title']}” by Ioannis Alexander Konstas. Stream on Spotify."
            notes_html, lead = r["notes_by_track"].get(track_id, (r["notes"], r["lead"]))
            if lead:
                desc = f"{lead} {title} by Ioannis Alexander Konstas — stream on Spotify."
            # a track can have its own cover art (covers/tracks/<slug>.jpg) instead of the release cover
            track_cover_path = os.path.join(ROOT, "covers", "tracks", slug + ".jpg")
            if os.path.exists(track_cover_path):
                use_cover_path, use_cover_file, cover_alt = track_cover_path, f"tracks/{slug}.jpg", f"{title} cover art"
            else:
                use_cover_path, use_cover_file, cover_alt = cover_path, cover_file, f"{r['title']} cover art"
            share_card(title, card_meta, use_cover_path, os.path.join(ROOT, "share", "tracks", slug + ".jpg"), lead)
            e = html.escape
            page = PAGE.format(
                url=f"{SITE}/tracks/{slug}.html", img=f"{SITE}/share/tracks/{slug}.jpg" + ("?v=3" if lead else ""), artist=ARTIST_URL,
                title=e(title), title_full=e(f"{title} — Ioannis Alexander Konstas"), desc=e(desc), album=e(r["title"]),
                cover_file=use_cover_file, cover_alt=e(cover_alt), meta_html=meta_html, track_id=track_id, back_html=back_html, notes_html=notes_html)
            with open(os.path.join(ROOT, "tracks", slug + ".html"), "w", encoding="utf-8") as f:
                f.write(page)
            built.append((slug, title, r["title"]))
    with open(os.path.join(ROOT, "tracks", "LINKS.txt"), "w", encoding="utf-8") as f:
        for slug, title, album in built:
            f.write(f"{title} ({album})\n  {SITE}/tracks/{slug}.html\n")
    print(f"{len(built)} track pages built")


if __name__ == "__main__":
    main()
