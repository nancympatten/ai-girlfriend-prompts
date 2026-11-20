#!/usr/bin/env python3
"""
AI Girlfriend Prompts — Static Website Generator
Usage: python3 build.py

Reads data.csv and generates a complete static website in dist/.
Uses only the Python standard library.
"""

import os
BASE_URL = "https://ai-girlfriend-prompts.velvetgrid.workers.dev"
SITE_NAME = "AI Girlfriend Prompts"
NICHE_TOPIC = "AI Companion & Voice Roleplay Prompts"
CONTACT_EMAIL = "nancympatten@gmail.com"
AFFILIATE_URL = "#affiliate-link"
AFFILIATE_CTA_TEXT = "Test This Prompt Live with an AI Voice Girlfriend (Free Trial)"

import csv
import html
import json
import math
import re
import shutil
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data.csv"
DIST = ROOT / "dist"

ITEMS_PER_PAGE = 24
RELATED_ITEMS = 8
RATING_META = "RTA-5042-1996-1400-1577-RTA"

REQUIRED_COLUMNS = [
    "slug", "title", "category", "subcategory", "target_keyword",
    "prompt_or_script", "description", "tags", "faq_q1", "faq_a1",
    "faq_q2", "faq_a2", "upload_date"
]


def esc(value):
    return html.escape(str(value or ""), quote=True)


def clean(value):
    return str(value or "").strip()


def slugify(value):
    value = clean(value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "item"


def unique_slug(value, used):
    base = slugify(value)
    candidate = base
    number = 2
    while candidate in used:
        candidate = f"{base}-{number}"
        number += 1
    used.add(candidate)
    return candidate


def split_tags(value):
    if isinstance(value, (list, tuple)):
        values = value
    else:
        values = re.split(r"[,|]", clean(value))
    result = []
    seen = set()
    for item in values:
        tag = clean(item)
        key = tag.casefold()
        if tag and key not in seen:
            result.append(tag)
            seen.add(key)
    return result


def parse_date(value):
    value = clean(value)
    if not value:
        return date.today()
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        for fmt in ("%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                pass
    return date.today()


def read_csv():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Missing CSV file: {DATA_FILE}")

    items = []
    used_slugs = set()

    with DATA_FILE.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames or []
        missing = [column for column in REQUIRED_COLUMNS if column not in headers]

        if missing:
            raise ValueError(
                "data.csv is missing required columns: " + ", ".join(missing)
            )

        for row_number, row in enumerate(reader, start=2):
            if not row or not any(clean(value) for value in row.values()):
                continue

            item = {key: clean(row.get(key, "")) for key in REQUIRED_COLUMNS}
            if not item["title"] or not item["prompt_or_script"]:
                print(f"Skipping row {row_number}: missing title or prompt.")
                continue

            item["slug"] = unique_slug(item["slug"] or item["title"], used_slugs)
            item["tags_list"] = split_tags(item["tags"])
            item["date_obj"] = parse_date(item["upload_date"])
            item["category"] = item["category"] or "General"
            item["subcategory"] = item["subcategory"] or "General"
            item["target_keyword"] = item["target_keyword"] or item["title"]
            item["category_slug"] = slugify(item["category"])
            item["subcategory_slug"] = slugify(item["subcategory"])
            items.append(item)

    if not items:
        raise ValueError("No valid prompt rows were found in data.csv.")

    return items


def write_file(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def absolute_url(path=""):
    return BASE_URL.rstrip("/") + "/" + str(path).lstrip("/")


def page_shell(title, description, canonical, body, extra_head=""):
    safe_title = esc(title)
    safe_description = esc(description)
    canonical_url = esc(absolute_url(canonical))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="rating" content="{RATING_META}">
<title>{safe_title}</title>
<meta name="description" content="{safe_description}">
<link rel="canonical" href="{canonical_url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(SITE_NAME)}">
<meta property="og:title" content="{safe_title}">
<meta property="og:description" content="{safe_description}">
<meta property="og:url" content="{canonical_url}">
<meta name="twitter:card" content="summary">
{extra_head}
<style>
:root{{--bg:#0b0b12;--panel:#151522;--panel2:#1d1b2b;--text:#f5f2fa;--muted:#aaa5b8;--accent:#e879b9;--accent2:#a78bfa;--border:#302b40;--good:#86efac}}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth}}
body{{margin:0;background:var(--bg);color:var(--text);font:16px/1.65 system-ui,-apple-system,Segoe UI,sans-serif}}
a{{color:var(--accent);text-decoration:none}}
a:hover{{text-decoration:underline}}
button,input,select{{font:inherit}}
button,.button{{display:inline-block;border:0;border-radius:10px;padding:11px 16px;background:var(--accent);color:#190d19;font-weight:750;cursor:pointer}}
button:hover,.button:hover{{filter:brightness(1.1);text-decoration:none}}
button.secondary,.button.secondary{{background:var(--panel2);color:var(--text);border:1px solid var(--border)}}
.wrap{{width:min(1120px,calc(100% - 36px));margin:auto}}
header{{border-bottom:1px solid var(--border);background:#10101a}}
.nav{{min-height:68px;display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap}}
.brand{{font-weight:850;font-size:1.15rem;color:var(--text)}}
.navlinks{{display:flex;gap:18px;flex-wrap:wrap}}
.hero{{padding:66px 0 48px;text-align:center;background:radial-gradient(ellipse at top,#35203d 0%,#15101f 42%,var(--bg) 78%)}}
.hero h1{{font-size:clamp(2rem,5vw,3.4rem);line-height:1.12;margin:0 auto 16px;max-width:850px}}
.hero p{{color:var(--muted);max-width:720px;margin:0 auto 24px}}
.search{{width:min(680px,100%);padding:15px 18px;border-radius:12px;border:1px solid var(--border);background:#171522;color:var(--text)}}
.section{{padding:34px 0}}
.section h2{{font-size:1.65rem;margin:0 0 18px}}
.muted{{color:var(--muted)}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px}}
.card{{display:block;background:var(--panel);border:1px solid var(--border);border-radius:15px;padding:19px;color:var(--text);transition:transform .15s,border-color .15s}}
.card:hover{{transform:translateY(-2px);border-color:var(--accent);text-decoration:none}}
.card h3{{margin:0 0 8px;font-size:1.08rem}}
.card p{{margin:0;color:var(--muted);font-size:.93rem}}
.count{{display:inline-block;margin-top:12px;color:var(--accent);font-size:.88rem;font-weight:750}}
.tag-list{{display:flex;gap:9px;flex-wrap:wrap}}
.tag{{background:var(--panel2);border:1px solid var(--border);border-radius:999px;padding:6px 12px;font-size:.88rem}}
.content{{max-width:850px;margin:0 auto}}
.content h1{{font-size:clamp(1.9rem,4vw,2.8rem);line-height:1.2}}
.breadcrumbs{{font-size:.9rem;color:var(--muted);margin:22px 0}}
.prompt-box{{background:var(--panel);border:1px solid var(--border);border-radius:16px;padding:22px;margin:22px 0}}
.prompt-text{{white-space:pre-wrap;overflow-wrap:anywhere;background:#0d0d16;border:1px solid var(--border);padding:20px;border-radius:12px;line-height:1.8}}
.controls{{display:flex;gap:9px;flex-wrap:wrap;margin:14px 0}}
.field{{display:grid;gap:6px;margin:12px 0}}
.field input,.field select{{width:100%;padding:11px;border:1px solid var(--border);border-radius:9px;background:#10101a;color:var(--text)}}
.affiliate{{margin:22px 0;padding:20px;border:1px solid #68405d;background:linear-gradient(120deg,#29182d,#21172b);border-radius:14px}}
.affiliate p{{margin:0 0 12px}}
.audio-box{{padding:18px;background:var(--panel);border:1px solid var(--border);border-radius:14px;margin:22px 0}}
.audio-box label{{display:block;margin:10px 0 5px}}
.audio-box select,.audio-box input{{max-width:100%}}
.pagination{{display:flex;gap:12px;align-items:center;justify-content:center;margin:28px 0;flex-wrap:wrap}}
.faq{{border-top:1px solid var(--border);padding:15px 0}}
footer{{border-top:1px solid var(--border);padding:32px 0;color:var(--muted);margin-top:45px}}
footer .footlinks{{display:flex;gap:16px;flex-wrap:wrap}}
.sticky-affiliate{{display:none}}
.age-overlay{{position:fixed;inset:0;z-index:9999;background:#05050bf2;display:flex;align-items:center;justify-content:center;padding:20px}}
.age-dialog{{max-width:470px;background:var(--panel);border:1px solid var(--border);border-radius:18px;padding:28px;text-align:center;box-shadow:0 20px 80px #0009}}
.age-dialog h2{{margin-top:0}}
.age-dialog p{{color:var(--muted)}}
.hidden{{display:none!important}}
.ad-slot{{min-height:1px}}
@media(max-width:650px){{
 .wrap{{width:min(100% - 26px,1120px)}}
 .hero{{padding:46px 0 34px}}
 .nav{{padding:12px 0}}
 .navlinks{{gap:12px;font-size:.9rem}}
 .sticky-affiliate{{display:block;position:fixed;z-index:50;bottom:0;left:0;right:0;padding:10px 12px;background:#100e19ee;border-top:1px solid var(--border);text-align:center}}
 .sticky-affiliate .button{{display:block;padding:10px}}
 body{{padding-bottom:66px}}
}}
</style>
</head>
<body>
<header><div class="wrap nav">
<a class="brand" href="/">{esc(SITE_NAME)}</a>
<nav class="navlinks">
<a href="/">Home</a><a href="/#categories">Categories</a><a href="/#latest">Latest Prompts</a>
</nav>
</div></header>
{body}
<footer><div class="wrap">
<div class="footlinks">
<a href="/">Home</a><a href="/dmca.html">DMCA</a><a href="/2257.html">18 U.S.C. 2257</a>
<a href="mailto:{esc(CONTACT_EMAIL)}">Contact</a>
</div>
<p>© {date.today().year} {esc(SITE_NAME)}. All rights reserved.</p>
</div></footer>
<div class="age-overlay hidden" id="age-overlay" role="dialog" aria-modal="true" aria-labelledby="age-title">
<div class="age-dialog">
<h2 id="age-title">Adults Only — 18+</h2>
<p>This website is intended only for adults aged 18 or older. By continuing, you confirm that you are at least 18 years old and agree to use the site responsibly.</p>
<button id="age-yes">I am 18 or older</button>
<button class="secondary" id="age-no">Exit</button>
</div></div>
<div class="sticky-affiliate"><a class="button" href="{esc(AFFILIATE_URL)}" rel="nofollow sponsored">{esc(AFFILIATE_CTA_TEXT)}</a></div>
<script>
(function(){{
 const overlay=document.getElementById('age-overlay');
 if(!localStorage.getItem('aigp_adult_confirmed')) overlay.classList.remove('hidden');
 const yes=document.getElementById('age-yes');
 const no=document.getElementById('age-no');
 if(yes) yes.addEventListener('click',function(){{
   localStorage.setItem('aigp_adult_confirmed','yes');
   overlay.classList.add('hidden');
 }});
 if(no) no.addEventListener('click',function(){{
   document.body.innerHTML='<main style="padding:50px;text-align:center"><h1>Access restricted</h1><p>You must be 18 or older to view this website.</p></main>';
 }});
}})();
</script>
</body></html>"""


def prompt_card(item):
    return f"""<a class="card prompt-card" href="/prompt/{quote(item['slug'])}.html"
 data-search="{esc((item['title']+' '+item['target_keyword']+' '+' '.join(item['tags_list'])).lower())}">
<h3>{esc(item['title'])}</h3>
<p>{esc(item['description'][:155] or item['target_keyword'])}</p>
<span class="count">Explore prompt →</span>
</a>"""


def category_card(category, category_slug, count):
    return f"""<a class="card" href="/category/{quote(category_slug)}/page-1.html">
<h3>{esc(category)}</h3>
<p>Explore prompts in {esc(category)}.</p>
<span class="count">{count} prompts</span>
</a>"""


def generate_home(items):
    # Group rows by category so each unique category is rendered exactly once.
    category_groups = defaultdict(list)
    category_names = {}

    for item in items:
        key = item["category_slug"]
        category_groups[key].append(item)
        category_names.setdefault(key, item["category"])

    # Use the number of rows in each group as the true prompt count.
    category_counts = {
        category_slug: len(category_items)
        for category_slug, category_items in category_groups.items()
    }

    categories_html = "".join(
        category_card(
            category_names[category_slug],
            category_slug,
            category_counts[category_slug]
        )
        for category_slug in sorted(
            category_groups,
            key=lambda key: category_names[key].casefold()
        )
    )

    subcategories = defaultdict(list)
    for item in items:
        subcategories[(item["subcategory_slug"], item["subcategory"])].append(item)

    subcategory_html = "".join(
        f'<a class="tag" href="/topic/{quote(slug)}.html">{esc(name)} ({len(group)})</a>'
        for (slug, name), group in sorted(
            subcategories.items(), key=lambda entry: entry[0][1].casefold()
        )
    )

    tag_counts = Counter(
        tag for item in items for tag in item["tags_list"]
    )
    tag_html = "".join(
        f'<a class="tag" href="/tag/{quote(slugify(tag))}.html">{esc(tag)} ({count})</a>'
        for tag, count in tag_counts.most_common(40)
    )

    newest = sorted(items, key=lambda item: item["date_obj"], reverse=True)[:30]
    newest_html = "".join(prompt_card(item) for item in newest)

    body = f"""
<main>
<section class="hero"><div class="wrap">
<h1>AI Girlfriend Prompts for More Personal Conversations</h1>
<p>Discover creative AI companion prompts, character ideas, personality styles, and voice roleplay scripts.</p>
<input class="search" id="home-search" type="search" placeholder="Search prompts, keywords, and tags..." aria-label="Search prompts">
<p id="search-status" class="muted"></p>
</div></section>
<div class="ad-slot"><!-- AD_SLOT_TOP_BANNER --></div>
<section class="section wrap" id="categories">
<h2>Browse Prompt Categories</h2>
<div class="grid">{categories_html}</div>
</section>
<section class="section wrap">
<h2>Browse Topics</h2>
<div class="tag-list">{subcategory_html}</div>
</section>
<section class="section wrap">
<h2>Explore Prompt Tags</h2>
<div class="tag-list">{tag_html}</div>
</section>
<div class="ad-slot"><!-- AD_SLOT_MID_CONTENT --></div>
<section class="section wrap" id="latest">
<h2>30 Newest AI Girlfriend Prompts</h2>
<div class="grid" id="latest-grid">{newest_html}</div>
<p id="no-results" class="muted hidden">No matching prompts found.</p>
</section>
</main>
<script>
(function(){{
 const input=document.getElementById('home-search');
 const cards=Array.from(document.querySelectorAll('.prompt-card'));
 const status=document.getElementById('search-status');
 const empty=document.getElementById('no-results');
 input.addEventListener('input',function(){{
   const query=input.value.trim().toLowerCase();
   let visible=0;
   cards.forEach(function(card){{
     const match=!query || card.dataset.search.includes(query);
     card.classList.toggle('hidden',!match);
     if(match) visible++;
   }});
   status.textContent=query ? visible+' matching latest prompts shown' : '';
   empty.classList.toggle('hidden',visible!==0);
 }});
}})();
</script>
"""
    write_file(DIST / "index.html", page_shell(
        f"{SITE_NAME} | AI Companion & Voice Roleplay Prompts",
        "Browse AI girlfriend prompts, AI companion scripts, character ideas, and voice roleplay prompts.",
        "/",
        body
    ))


def json_ld_script(data):
    serialized = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    serialized = serialized.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return f'<script type="application/ld+json">{serialized}</script>'


def related_items(item, items):
    same_topic = [
        candidate for candidate in items
        if candidate["slug"] != item["slug"]
        and candidate["subcategory_slug"] == item["subcategory_slug"]
    ]

    shared_tags = [
        candidate for candidate in items
        if candidate["slug"] != item["slug"]
        and set(tag.casefold() for tag in candidate["tags_list"])
        & set(tag.casefold() for tag in item["tags_list"])
    ]

    chosen = []
    seen = set()

    for candidate in same_topic[:4] + shared_tags[:4]:
        if candidate["slug"] not in seen:
            chosen.append(candidate)
            seen.add(candidate["slug"])

    if len(chosen) < RELATED_ITEMS:
        for candidate in items:
            if candidate["slug"] != item["slug"] and candidate["slug"] not in seen:
                chosen.append(candidate)
                seen.add(candidate["slug"])
                if len(chosen) >= RELATED_ITEMS:
                    break

    return chosen[:RELATED_ITEMS]


def generate_prompt_page(item, items):
    slug = item["slug"]
    title = item["title"]
    keyword = item["target_keyword"]
    canonical = f"/prompt/{slug}.html"
    description = item["description"] or f"Explore this {keyword} AI companion prompt and customize it for your preferred character and conversation style."

    prompt_json = json.dumps(item["prompt_or_script"], ensure_ascii=False)
    prompt_json = prompt_json.replace("<", "\\u003c").replace(">", "\\u003e")

    faq_entries = []
    for question_key, answer_key in (("faq_q1", "faq_a1"), ("faq_q2", "faq_a2")):
        question = item[question_key]
        answer = item[answer_key]
        if question and answer:
            faq_entries.append({
                "@type": "Question",
                "name": question,
                "acceptedAnswer": {"@type": "Answer", "text": answer}
            })

    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": absolute_url("/")},
            {"@type": "ListItem", "position": 2, "name": item["category"], "item": absolute_url(f"/category/{item['category_slug']}/page-1.html")},
            {"@type": "ListItem", "position": 3, "name": title, "item": absolute_url(canonical)}
        ]
    }

    article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "datePublished": item["date_obj"].isoformat(),
        "mainEntityOfPage": absolute_url(canonical),
        "author": {"@type": "Organization", "name": SITE_NAME},
        "publisher": {"@type": "Organization", "name": SITE_NAME}
    }

    howto = {
        "@context": "https://schema.org",
        "@type": "HowTo",
        "name": f"How to use: {title}",
        "description": description,
        "step": [
            {"@type": "HowToStep", "name": "Customize the characters", "text": "Enter your preferred name, AI character name, and personality tone."},
            {"@type": "HowToStep", "name": "Personalize the prompt", "text": "Review the prompt and adjust any details to suit your conversation."},
            {"@type": "HowToStep", "name": "Copy and use", "text": "Copy the customized prompt and paste it into your preferred AI companion platform."}
        ]
    }

    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": faq_entries
    }

    schemas = "".join(
        json_ld_script(schema)
        for schema in (article, howto, breadcrumb, faq_schema)
    )

    related = related_items(item, items)
    related_html = "".join(prompt_card(candidate) for candidate in related)

    tags_html = " ".join(
        f'<a class="tag" href="/tag/{quote(slugify(tag))}.html">{esc(tag)}</a>'
        for tag in item["tags_list"]
    )

    faq_html = "".join(
        f'<div class="faq"><h3>{esc(item[q])}</h3><p>{esc(item[a])}</p></div>'
        for q, a in (("faq_q1", "faq_a1"), ("faq_q2", "faq_a2"))
        if item[q] and item[a]
    )

    body = f"""
<main class="wrap">
<div class="content">
<nav class="breadcrumbs"><a href="/">Home</a> / <a href="/category/{quote(item['category_slug'])}/page-1.html">{esc(item['category'])}</a> / {esc(title)}</nav>
<h1>{esc(title)}</h1>
<p class="muted">{esc(description)}</p>
<p class="muted">Category: <a href="/category/{quote(item['category_slug'])}/page-1.html">{esc(item['category'])}</a> · Topic: <a href="/topic/{quote(item['subcategory_slug'])}.html">{esc(item['subcategory'])}</a></p>
<div class="tag-list">{tags_html}</div>

<section class="prompt-box">
<h2>Customize Your AI Companion Prompt</h2>
<div class="field"><label for="your-name">Your Name</label><input id="your-name" placeholder="Enter your name" autocomplete="given-name"></div>
<div class="field"><label for="ai-name">AI Name</label><input id="ai-name" placeholder="Enter an AI character name"></div>
<div class="field"><label for="personality-tone">Personality Tone</label>
<select id="personality-tone">
<option value="warm and affectionate">Warm and affectionate</option>
<option value="playful and teasing">Playful and teasing</option>
<option value="romantic and gentle">Romantic and gentle</option>
<option value="confident and charismatic">Confident and charismatic</option>
<option value="shy and sweet">Shy and sweet</option>
<option value="calm and reassuring">Calm and reassuring</option>
<option value="witty and adventurous">Witty and adventurous</option>
</select></div>
<div class="controls">
<button type="button" id="copy-prompt">Copy Prompt</button>
<button type="button" class="secondary" id="font-down" aria-label="Decrease prompt font size">A−</button>
<button type="button" class="secondary" id="font-up" aria-label="Increase prompt font size">A+</button>
</div>
<p class="muted" id="copy-status" aria-live="polite">Customize the fields above, then copy your prompt.</p>
<p class="muted"><span id="char-count">0</span> characters · Approximately <span id="token-count">0</span> tokens</p>
<div class="prompt-text" id="prompt-output"></div>
</section>

<div class="affiliate">
<!-- AD_SLOT_MID_CONTENT -->
<p><strong>Want to try your prompt with an AI voice companion?</strong></p>
<a class="button" href="{esc(AFFILIATE_URL)}" rel="nofollow sponsored">{esc(AFFILIATE_CTA_TEXT)}</a>
</div>

<section class="audio-box">
<h2>Ambient Mood Player</h2>
<p class="muted">Create a gentle background atmosphere using your browser's built-in audio engine.</p>
<label for="audio-mode">Choose an ambience</label>
<select id="audio-mode">
<option value="rain">Late Night Rain</option>
<option value="heartbeat">Soft Heartbeat</option>
<option value="fireplace">Cozy Fireplace Brown Noise</option>
</select>
<label for="audio-volume">Volume</label>
<input id="audio-volume" type="range" min="0" max="1" step="0.05" value="0.25">
<div class="controls">
<button type="button" id="audio-play">Play ambience</button>
<button type="button" class="secondary" id="audio-stop">Stop</button>
</div>
<p class="muted" id="audio-status" aria-live="polite">Audio starts only after you press Play.</p>
</section>

<section class="section">
<h2>About This Prompt</h2>
<p>{esc(description)}</p>
<p>This prompt is designed for customizable AI companion conversations. Replace the example names and adapt the tone to match your preferences.</p>
</section>

<section class="section">
<h2>Frequently Asked Questions</h2>
{faq_html or '<p class="muted">There are no additional FAQs for this prompt yet.</p>'}
</section>

<section class="section">
<h2>Related AI Girlfriend Prompts</h2>
<div class="grid">{related_html}</div>
</section>
</div>
</main>
<script>
(function(){{
 const original={prompt_json};
 const nameInput=document.getElementById('your-name');
 const aiInput=document.getElementById('ai-name');
 const toneInput=document.getElementById('personality-tone');
 const output=document.getElementById('prompt-output');
 const charCount=document.getElementById('char-count');
 const tokenCount=document.getElementById('token-count');
 const status=document.getElementById('copy-status');
 let fontSize=16;

 function render(){{
   const yourName=nameInput.value.trim()||'Your Name';
   const aiName=aiInput.value.trim()||'AI Name';
   const tone=toneInput.value;
   let result=original;
   const replacements={{
     '{{your_name}}':yourName,
     '{{ai_name}}':aiName,
     '{{personality_tone}}':tone,
     '[Your Name]':yourName,
     '[AI Name]':aiName,
     '[Personality Tone]':tone
   }};
   Object.keys(replacements).forEach(function(key){{
     result=result.split(key).join(replacements[key]);
   }});
   output.textContent=result;
   charCount.textContent=result.length.toLocaleString();
   tokenCount.textContent=Math.ceil(result.trim().split(/\\s+/).filter(Boolean).length*1.3).toLocaleString();
   return result;
 }}

 [nameInput,aiInput,toneInput].forEach(function(field){{
   field.addEventListener('input',render);
   field.addEventListener('change',render);
 }});

 document.getElementById('copy-prompt').addEventListener('click',async function(){{
   try{{
     await navigator.clipboard.writeText(render());
     status.textContent='Prompt copied successfully!';
   }}catch(error){{
     const range=document.createRange();
     range.selectNodeContents(output);
     const selection=window.getSelection();
     selection.removeAllRanges();
     selection.addRange(range);
     status.textContent='Select the highlighted prompt and copy it manually.';
   }}
 }});

 document.getElementById('font-up').addEventListener('click',function(){{
   fontSize=Math.min(28,fontSize+1);
   output.style.fontSize=fontSize+'px';
 }});
 document.getElementById('font-down').addEventListener('click',function(){{
   fontSize=Math.max(12,fontSize-1);
   output.style.fontSize=fontSize+'px';
 }});

 render();

 let audioContext=null;
 let masterGain=null;
 let activeNodes=[];
 let noiseBuffer=null;

 function stopAudio(){{
   activeNodes.forEach(function(node){{
     try{{if(node.stop)node.stop();}}catch(error){{}}
     try{{node.disconnect();}}catch(error){{}}
   }});
   activeNodes=[];
   if(masterGain){{
     try{{masterGain.disconnect();}}catch(error){{}}
     masterGain=null;
   }}
   document.getElementById('audio-status').textContent='Ambience stopped.';
 }}

 function getNoiseBuffer(){{
   if(noiseBuffer)return noiseBuffer;
   const length=audioContext.sampleRate*3;
   noiseBuffer=audioContext.createBuffer(1,length,audioContext.sampleRate);
   const data=noiseBuffer.getChannelData(0);
   for(let i=0;i<length;i++)data[i]=Math.random()*2-1;
   return noiseBuffer;
 }}

 function makeNoise(filterType,frequency,gainValue){{
   const source=audioContext.createBufferSource();
   source.buffer=getNoiseBuffer();
   source.loop=true;
   const filter=audioContext.createBiquadFilter();
   filter.type=filterType;
   filter.frequency.value=frequency;
   const gain=audioContext.createGain();
   gain.gain.value=gainValue;
   source.connect(filter);
   filter.connect(gain);
   gain.connect(masterGain);
   source.start();
   activeNodes.push(source,filter,gain);
 }}

 function makeOscillator(frequency,type,gainValue){{
   const oscillator=audioContext.createOscillator();
   const gain=audioContext.createGain();
   oscillator.type=type;
   oscillator.frequency.value=frequency;
   gain.gain.value=gainValue;
   oscillator.connect(gain);
   gain.connect(masterGain);
   oscillator.start();
   activeNodes.push(oscillator,gain);
 }}

 async function playAudio(){{
   stopAudio();
   const statusEl=document.getElementById('audio-status');
   const mode=document.getElementById('audio-mode').value;
   try{{
     const AudioContextClass=window.AudioContext||window.webkitAudioContext;
     if(!AudioContextClass)throw new Error('Web Audio is not supported in this browser.');
     if(!audioContext)audioContext=new AudioContextClass();
     if(audioContext.state==='suspended')await audioContext.resume();

     masterGain=audioContext.createGain();
     masterGain.gain.value=Number(document.getElementById('audio-volume').value);
     masterGain.connect(audioContext.destination);

     if(mode==='rain'){{
       makeNoise('lowpass',1200,0.75);
       makeNoise('highpass',450,0.12);
       makeOscillator(90,'sine',0.025);
       statusEl.textContent='Playing Late Night Rain.';
     }}else if(mode==='heartbeat'){{
       makeNoise('lowpass',180,0.06);
       makeOscillator(48,'sine',0.18);
       makeOscillator(72,'sine',0.07);
       statusEl.textContent='Playing Soft Heartbeat ambience.';
     }}else{{
       makeNoise('lowpass',320,0.65);
       makeNoise('highpass',900,0.08);
       makeOscillator(55,'triangle',0.025);
       statusEl.textContent='Playing Cozy Fireplace Brown Noise.';
     }}
   }}catch(error){{
     stopAudio();
     statusEl.textContent=error.message||'Unable to start audio.';
   }}
 }}

 document.getElementById('audio-play').addEventListener('click',playAudio);
 document.getElementById('audio-stop').addEventListener('click',stopAudio);
 document.getElementById('audio-volume').addEventListener('input',function(){{
   if(masterGain)masterGain.gain.value=Number(this.value);
 }});
 window.addEventListener('pagehide',stopAudio);
}})();
</script>
{schemas}
"""
    write_file(DIST / "prompt" / f"{slug}.html", page_shell(
        f"{keyword} | {SITE_NAME}",
        description,
        canonical,
        body,
        '<meta name="keywords" content="' + esc(keyword) + '">'
    ))


def pagination_html(page, total_pages, base_path):
    if total_pages <= 1:
        return ""
    previous = (
        f'<a class="button secondary" href="{base_path}/page-{page-1}.html">← Previous</a>'
        if page > 1 else ""
    )
    following = (
        f'<a class="button secondary" href="{base_path}/page-{page+1}.html">Next →</a>'
        if page < total_pages else ""
    )
    return f'<nav class="pagination" aria-label="Pagination">{previous}<span>Page {page} of {total_pages}</span>{following}</nav>'


def generate_listing_page(title, description, items, output_path, canonical,
                          base_path, page=1, total_pages=1):
    cards = "".join(prompt_card(item) for item in items)
    pagination = pagination_html(page, total_pages, base_path)

    extra_head = ""
    if page > 1:
        extra_head += f'<link rel="prev" href="{esc(absolute_url(base_path + "/page-" + str(page-1) + ".html"))}">'
    if page < total_pages:
        extra_head += f'<link rel="next" href="{esc(absolute_url(base_path + "/page-" + str(page+1) + ".html"))}">'

    body = f"""
<main class="wrap section">
<nav class="breadcrumbs"><a href="/">Home</a> / {esc(title)}</nav>
<h1>{esc(title)}</h1>
<p class="muted">{esc(description)}</p>
<div class="grid">{cards}</div>
{pagination}
</main>
"""
    write_file(output_path, page_shell(
        f"{title} | {SITE_NAME}",
        description,
        canonical,
        body,
        extra_head
    ))


def generate_categories(items):
    # One dictionary entry per unique category slug; every row is appended
    # to its category group, so the displayed count is the full group size.
    categories = defaultdict(list)
    category_names = {}

    for item in items:
        category_slug = item["category_slug"]
        categories[category_slug].append(item)
        category_names.setdefault(category_slug, item["category"])

    for category_slug, category_items in categories.items():
        category_items.sort(key=lambda item: item["date_obj"], reverse=True)
        total_pages = max(1, math.ceil(len(category_items) / ITEMS_PER_PAGE))
        base_path = f"/category/{category_slug}"

        for page in range(1, total_pages + 1):
            start = (page - 1) * ITEMS_PER_PAGE
            page_items = category_items[start:start + ITEMS_PER_PAGE]
            output = DIST / "category" / category_slug / f"page-{page}.html"
            canonical = f"{base_path}/page-{page}.html"

            generate_listing_page(
                f"{category_names[category_slug]} Prompts",
                f"Browse {len(category_items)} AI companion prompts in the {category_names[category_slug]} category.",
                page_items,
                output,
                canonical,
                base_path,
                page,
                total_pages
            )


def generate_subcategories(items):
    groups = defaultdict(list)
    names = {}

    for item in items:
        key = item["subcategory_slug"]
        groups[key].append(item)
        names.setdefault(key, item["subcategory"])

    for key, group in groups.items():
        group.sort(key=lambda item: item["date_obj"], reverse=True)
        generate_listing_page(
            f"{names[key]} AI Prompts",
            f"Explore {len(group)} prompts about {names[key]}.",
            group,
            DIST / "topic" / f"{key}.html",
            f"/topic/{key}.html",
            f"/topic/{key}"
        )


def generate_tags(items):
    groups = defaultdict(list)
    names = {}

    for item in items:
        for tag in item["tags_list"]:
            key = slugify(tag)
            groups[key].append(item)
            names.setdefault(key, tag)

    for key, group in groups.items():
        unique_items = []
        seen = set()
        for item in group:
            if item["slug"] not in seen:
                unique_items.append(item)
                seen.add(item["slug"])

        unique_items.sort(key=lambda item: item["date_obj"], reverse=True)
        generate_listing_page(
            f"{names[key]} Prompts",
            f"Browse AI companion prompts tagged {names[key]}.",
            unique_items,
            DIST / "tag" / f"{key}.html",
            f"/tag/{key}.html",
            f"/tag/{key}"
        )


def generate_compliance_pages():
    dmca_body = f"""
<main class="wrap section content">
<h1>DMCA Copyright Policy</h1>
<p>{esc(SITE_NAME)} respects intellectual property rights and responds to valid notices under the Digital Millennium Copyright Act.</p>
<h2>Submit a takedown request</h2>
<p>Send a notice to <a href="mailto:{esc(CONTACT_EMAIL)}">{esc(CONTACT_EMAIL)}</a> containing:</p>
<ul>
<li>Identification of the copyrighted work claimed to be infringed.</li>
<li>Identification of the material and its location on this website.</li>
<li>Your contact information.</li>
<li>A statement of good-faith belief that the use is unauthorized.</li>
<li>A statement, under penalty of perjury, that the information is accurate and that you are authorized to act.</li>
<li>Your physical or electronic signature.</li>
</ul>
<p>We may remove or disable access to material that is the subject of a compliant notice.</p>
</main>
"""
    write_file(DIST / "dmca.html", page_shell(
        f"DMCA Policy | {SITE_NAME}",
        "Copyright and DMCA takedown policy.",
        "/dmca.html",
        dmca_body
    ))

    body_2257 = """
<main class="wrap section content">
<h1>18 U.S.C. 2257 Compliance Statement</h1>
<p>This website is an AI companion prompt directory. The content consists of text prompts, descriptions, and fictional roleplay concepts. It does not host or produce visual depictions of actual sexually explicit conduct.</p>
<p>Any character concepts described on this website are fictional. This website is intended for adults aged 18 or older.</p>
<p>For questions about this statement, contact the website operator.</p>
</main>
"""
    write_file(DIST / "2257.html", page_shell(
        f"18 U.S.C. 2257 Statement | {SITE_NAME}",
        "Age and 18 U.S.C. 2257 compliance statement.",
        "/2257.html",
        body_2257
    ))


SITEMAP_XSL = """<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:s="http://www.sitemaps.org/schemas/sitemap/0.9">
<xsl:output method="html" encoding="UTF-8" indent="yes"/>
<xsl:template match="/">
<html><head><title>Sitemap</title>
<style>
body{font:15px system-ui;background:#10101a;color:#eee;padding:30px}
main{max-width:1100px;margin:auto}
h1{color:#f09aca}table{width:100%;border-collapse:collapse;background:#191827}
th,td{text-align:left;padding:12px;border-bottom:1px solid #393247}
th{color:#f09aca}a{color:#c4a5fd;overflow-wrap:anywhere}
p{color:#aaa}
</style></head><body><main>
<h1>XML Sitemap</h1>
<p>Use this sitemap to explore the URLs published by this website.</p>
<xsl:choose>
<xsl:when test="s:urlset">
<table><tr><th>URL</th><th>Last modified</th></tr>
<xsl:for-each select="s:urlset/s:url">
<tr><td><a><xsl:attribute name="href"><xsl:value-of select="s:loc"/></xsl:attribute><xsl:value-of select="s:loc"/></a></td>
<td><xsl:value-of select="s:lastmod"/></td></tr>
</xsl:for-each></table>
</xsl:when>
<xsl:when test="s:sitemapindex">
<table><tr><th>Sitemap</th><th>Last modified</th></tr>
<xsl:for-each select="s:sitemapindex/s:sitemap">
<tr><td><a><xsl:attribute name="href"><xsl:value-of select="s:loc"/></xsl:attribute><xsl:value-of select="s:loc"/></a></td>
<td><xsl:value-of select="s:lastmod"/></td></tr>
</xsl:for-each></table>
</xsl:when>
</xsl:choose>
</main></body></html>
</xsl:template></xsl:stylesheet>
"""


def xml_escape(value):
    return (
        str(value).replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def generate_sitemaps(items):
    urls = {"/", "/dmca.html", "/2257.html"}

    for item in items:
        urls.add(f"/prompt/{item['slug']}.html")

    category_groups = defaultdict(list)
    for item in items:
        category_groups[item["category_slug"]].append(item)

    for category_slug, group in category_groups.items():
        pages = max(1, math.ceil(len(group) / ITEMS_PER_PAGE))
        for page in range(1, pages + 1):
            urls.add(f"/category/{category_slug}/page-{page}.html")

    for item in items:
        urls.add(f"/topic/{item['subcategory_slug']}.html")
        for tag in item["tags_list"]:
            urls.add(f"/tag/{slugify(tag)}.html")

    sorted_urls = sorted(urls)
    chunks = [
        sorted_urls[i:i + 1000]
        for i in range(0, len(sorted_urls), 1000)
    ] or [[]]

    write_file(DIST / "sitemap.xsl", SITEMAP_XSL)

    child_names = []
    for index, chunk in enumerate(chunks, start=1):
        filename = f"sitemap-{index}.xml"
        child_names.append(filename)
        entries = []

        for path in chunk:
            entries.append(
                "<url>"
                f"<loc>{xml_escape(absolute_url(path))}</loc>"
                f"<lastmod>{date.today().isoformat()}</lastmod>"
                "</url>"
            )

        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<?xml-stylesheet type="text/xsl" href="/sitemap.xsl"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(entries)
            + "\n</urlset>"
        )
        write_file(DIST / filename, xml)

    sitemap_entries = "".join(
        f"<sitemap><loc>{xml_escape(absolute_url('/' + name))}</loc>"
        f"<lastmod>{date.today().isoformat()}</lastmod></sitemap>"
        for name in child_names
    )

    index_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<?xml-stylesheet type="text/xsl" href="/sitemap.xsl"?>\n'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + sitemap_entries
        + "\n</sitemapindex>"
    )
    write_file(DIST / "sitemap.xml", index_xml)


def generate_robots():
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        f"Sitemap: {absolute_url('/sitemap.xml')}\n"
    )
    write_file(DIST / "robots.txt", content)


def verify_build(items):
    required_files = [
        DIST / "index.html",
        DIST / "robots.txt",
        DIST / "sitemap.xml",
        DIST / "sitemap-1.xml",
        DIST / "sitemap.xsl",
        DIST / "dmca.html",
        DIST / "2257.html"
    ]

    for path in required_files:
        if not path.exists():
            raise RuntimeError(f"Build verification failed: missing {path}")

    homepage = (DIST / "index.html").read_text(encoding="utf-8")
    if "Browse Prompt Categories" not in homepage:
        raise RuntimeError("Homepage category section was not generated.")

    # Confirm category cards are unique and counts equal the actual row totals.
    category_counts = Counter(item["category_slug"] for item in items)
    for category_slug, count in category_counts.items():
        expected = f"{count} prompts"
        if expected not in homepage:
            raise RuntimeError(
                f"Category count missing from homepage for {category_slug}: {expected}"
            )

    for item in items:
        detail = DIST / "prompt" / f"{item['slug']}.html"
        if not detail.exists():
            raise RuntimeError(f"Missing prompt page: {detail}")

    print(f"Verified {len(items)} prompt pages.")
    print(f"Verified {len(category_counts)} unique category groups.")
    print("Required site files and sitemap are present.")


def build():
    print(f"Building {SITE_NAME}...")
    items = read_csv()

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True, exist_ok=True)

    generate_home(items)

    for item in items:
        generate_prompt_page(item, items)

    generate_categories(items)
    generate_subcategories(items)
    generate_tags(items)
    generate_compliance_pages()
    generate_robots()
    generate_sitemaps(items)
    verify_build(items)

    print()
    print("Build complete.")
    print(f"Prompts: {len(items)}")
    print(f"Categories: {len(set(item['category_slug'] for item in items))}")
    print(f"Output: {DIST}")


if __name__ == "__main__":
    try:
        build()
    except Exception as exc:
        print(f"Build failed: {exc}", file=sys.stderr)
        sys.exit(1)
