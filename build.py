#!/usr/bin/env python3
"""
AI Girlfriend Prompts — Production Static Website Generator
============================================================

Python 3 | Zero external dependencies | Cloudflare Pages compatible

Usage:
    python3 build.py

Input:
    data.csv

Output:
    dist/

Features:
    - Dynamic Cloudflare Pages URL detection
    - CSV validation and safe parsing
    - Responsive dark-mode website
    - Interactive prompt customizer
    - One-click copy and token counter
    - Synthesized Web Audio API ambient sounds
    - Native affiliate conversion components
    - Category, subcategory and tag landing pages
    - Paginated category archives
    - Related content recommendations
    - JSON-LD structured data
    - XML sitemap index and child sitemaps
    - Custom sitemap XSL stylesheet
    - Robots.txt
    - DMCA and 18 U.S.C. § 2257 information pages
    - LocalStorage age verification
    - Internal linking architecture

Note:
No static website can be guaranteed ban-proof or guaranteed to
rank in search engines. Review content, affiliate disclosures,
age restrictions, hosting policies and applicable laws before
publishing.
"""

import os

BASE_URL = os.environ.get(
    "CF_PAGES_URL",
    "https://ai-girlfriend-prompts.pages.dev"
).rstrip("/")

SITE_NAME = "AI Girlfriend Prompts"
NICHE_TOPIC = "AI Companion & Voice Roleplay Prompts"
CONTACT_EMAIL = "nancympatten@gmail.com"
AFFILIATE_URL = "#affiliate-link"
AFFILIATE_CTA_TEXT = (
    "Test This Prompt Live with an AI Voice Girlfriend (Free Trial)"
)

import csv
import re
import json
import html
import math
import shutil
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = Path("data.csv")
OUTPUT_DIR = Path("dist")

ITEMS_PER_PAGE = 24
RELATED_LIMIT = 8
NEWEST_LIMIT = 30
SITEMAP_LIMIT = 1000

REQUIRED_COLUMNS = [
    "slug",
    "title",
    "category",
    "subcategory",
    "target_keyword",
    "prompt_or_script",
    "description",
    "tags",
    "faq_q1",
    "faq_a1",
    "faq_q2",
    "faq_a2",
    "upload_date",
]

TODAY = datetime.now(timezone.utc).date().isoformat()

# ============================================================
# HELPERS
# ============================================================

def esc(value):
    return html.escape(str(value or ""), quote=True)


def json_script(value):
    """Safely serialize data for embedded JavaScript and JSON-LD."""
    return json.dumps(
        value,
        ensure_ascii=False
    ).replace("<", "\\u003c").replace(
        ">", "\\u003e"
    ).replace("&", "\\u0026")


def slugify(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "uncategorized"


def clean(value):
    return str(value or "").strip()


def split_tags(value):
    return list(dict.fromkeys(
        tag.strip()
        for tag in re.split(r"[,;|]", clean(value))
        if tag.strip()
    ))


def parse_date(value):
    value = clean(value)

    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)

    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%m/%d/%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(
                value, fmt
            ).replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        ).replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)


def absolute_url(path):
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return BASE_URL + "/" + path.lstrip("/")


def write_file(path, content):
    path = OUTPUT_DIR / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def unique_slugs(items, field):
    used = set()

    for item in items:
        base = slugify(item.get(field, ""))
        candidate = base
        counter = 2

        while candidate in used:
            candidate = f"{base}-{counter}"
            counter += 1

        item[field + "_slug"] = candidate
        used.add(candidate)


def load_data():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            "data.csv was not found. Place data.csv next to build.py."
        )

    records = []

    with INPUT_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("data.csv is empty or has no header.")

        missing = [
            col for col in REQUIRED_COLUMNS
            if col not in reader.fieldnames
        ]

        if missing:
            raise ValueError(
                "Missing required CSV columns: " + ", ".join(missing)
            )

        for line_number, row in enumerate(reader, start=2):
            item = {
                col: clean(row.get(col))
                for col in REQUIRED_COLUMNS
            }

            if not item["title"]:
                print(
                    f"Skipping line {line_number}: missing title."
                )
                continue

            if not item["slug"]:
                item["slug"] = slugify(item["title"])

            if not item["category"]:
                item["category"] = "General Prompts"

            if not item["subcategory"]:
                item["subcategory"] = "General Roleplay"

            if not item["target_keyword"]:
                item["target_keyword"] = item["title"]

            if not item["description"]:
                item["description"] = (
                    f"Explore this {item['title']} AI companion "
                    "prompt and customize it for your preferred "
                    "voice roleplay experience."
                )

            item["tags_list"] = split_tags(item["tags"])

            if not item["tags_list"]:
                item["tags_list"] = [
                    item["category"],
                    item["subcategory"]
                ]

            item["date_object"] = parse_date(
                item["upload_date"]
            )

            records.append(item)

    if not records:
        raise ValueError("No valid prompt records found in data.csv.")

    # Ensure all detail-page URLs are unique.
    used = set()

    for item in records:
        base = slugify(item["slug"])
        candidate = base
        number = 2

        while candidate in used:
            candidate = f"{base}-{number}"
            number += 1

        item["slug"] = candidate
        used.add(candidate)

    unique_slugs(records, "category")
    unique_slugs(records, "subcategory")

    # Normalize tags into unique URL identifiers.
    tag_names = sorted({
        tag
        for item in records
        for tag in item["tags_list"]
    })

    tag_mapping = {}
    used_tags = set()

    for tag in tag_names:
        base = slugify(tag)
        candidate = base
        number = 2

        while candidate in used_tags:
            candidate = f"{base}-{number}"
            number += 1

        tag_mapping[tag] = candidate
        used_tags.add(candidate)

    for item in records:
        item["tag_slugs"] = [
            tag_mapping[tag]
            for tag in item["tags_list"]
        ]

    return records, tag_names, tag_mapping


# ============================================================
# GLOBAL CSS
# ============================================================

CSS = r"""
:root {
    color-scheme: dark;
    --bg: #090b12;
    --surface: #111522;
    --surface2: #191e2d;
    --border: #292f42;
    --text: #f3f4fa;
    --muted: #a0a8bd;
    --accent: #a78bfa;
    --accent2: #ec4899;
    --green: #34d399;
    --radius: 17px;
    --max: 1160px;
}

* {
    box-sizing: border-box;
}

html {
    scroll-behavior: smooth;
}

body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: system-ui, -apple-system, BlinkMacSystemFont,
        "Segoe UI", sans-serif;
    line-height: 1.7;
}

a {
    color: var(--accent);
    text-decoration: none;
}

a:hover {
    color: #d8c8ff;
}

button, input, select, textarea {
    font: inherit;
}

button {
    cursor: pointer;
}

.container {
    width: min(var(--max), calc(100% - 36px));
    margin: auto;
}

header {
    border-bottom: 1px solid var(--border);
    background: rgba(9, 11, 18, .95);
}

.nav {
    min-height: 70px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    flex-wrap: wrap;
}

.logo {
    font-size: 20px;
    font-weight: 850;
    color: white;
    letter-spacing: -.7px;
}

.navlinks {
    display: flex;
    gap: 19px;
    flex-wrap: wrap;
    font-size: 14px;
}

.hero {
    padding: 75px 0 55px;
    text-align: center;
    background:
        radial-gradient(ellipse at 50% 0%, #39234c 0%, transparent 65%);
}

.hero h1 {
    font-size: clamp(32px, 6vw, 57px);
    line-height: 1.12;
    letter-spacing: -2px;
    margin: 0 auto 20px;
    max-width: 900px;
}

.hero p {
    color: var(--muted);
    max-width: 690px;
    margin: 0 auto 27px;
}

.searchbox {
    max-width: 650px;
    margin: 25px auto;
    display: flex;
    gap: 10px;
}

input, textarea, select {
    width: 100%;
    background: #0d111c;
    border: 1px solid var(--border);
    color: var(--text);
    padding: 13px 15px;
    border-radius: 11px;
    outline: none;
}

input:focus, textarea:focus, select:focus {
    border-color: var(--accent);
}

.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 12px 19px;
    border: 0;
    border-radius: 11px;
    color: white;
    background: linear-gradient(120deg, #8b5cf6, #ec4899);
    font-weight: 750;
    transition: transform .2s, opacity .2s;
}

.btn:hover {
    color: white;
    transform: translateY(-2px);
}

.btn.secondary {
    background: var(--surface2);
    border: 1px solid var(--border);
}

.section {
    padding: 35px 0;
}

.section-heading {
    font-size: 26px;
    letter-spacing: -.7px;
    margin-bottom: 20px;
}

.grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 17px;
}

.card {
    display: block;
    padding: 20px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    transition: .2s;
    min-width: 0;
}

.card:hover {
    border-color: var(--accent);
    transform: translateY(-3px);
}

.card h2, .card h3 {
    margin: 0 0 8px;
    color: white;
    line-height: 1.4;
}

.card p {
    color: var(--muted);
    font-size: 14px;
    margin: 8px 0;
}

.count, .badge {
    display: inline-block;
    border-radius: 30px;
    background: #28203d;
    color: #d5c2ff;
    padding: 4px 10px;
    font-size: 12px;
}

.tagcloud {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.tag {
    display: inline-block;
    border: 1px solid var(--border);
    background: var(--surface);
    padding: 7px 13px;
    border-radius: 30px;
    font-size: 13px;
}

.breadcrumb {
    color: var(--muted);
    font-size: 13px;
    padding: 20px 0;
}

.detail-title {
    font-size: clamp(30px, 5vw, 45px);
    line-height: 1.2;
    letter-spacing: -1.4px;
}

.muted {
    color: var(--muted);
}

.prompt-panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 19px;
    padding: 23px;
    margin: 25px 0;
}

.prompt-panel textarea {
    min-height: 260px;
    resize: vertical;
    line-height: 1.8;
    font-family: ui-monospace, SFMono-Regular, monospace;
    font-size: 15px;
    margin: 12px 0;
}

.controls {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    margin: 20px 0;
}

.control label {
    display: block;
    color: var(--muted);
    font-size: 13px;
    margin-bottom: 7px;
}

.prompt-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}

.prompt-actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.counter {
    color: var(--green);
    font-size: 13px;
}

.affiliate {
    border: 1px solid #7753ad;
    border-radius: 17px;
    padding: 22px;
    background: linear-gradient(120deg, #241a3b, #28182d);
    margin: 24px 0;
}

.affiliate h3 {
    margin-top: 0;
}

.affiliate p {
    color: #d0c7dc;
    font-size: 14px;
}

.audio-panel {
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 22px;
    border-radius: 17px;
    margin: 25px 0;
}

.audio-controls {
    display: flex;
    gap: 12px;
    align-items: center;
    flex-wrap: wrap;
}

.audio-controls select {
    max-width: 300px;
}

.audio-controls input[type=range] {
    max-width: 160px;
}

.pagination {
    display: flex;
    gap: 9px;
    flex-wrap: wrap;
    margin: 30px 0;
}

.pagination a, .pagination span {
    padding: 9px 14px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 9px;
}

.content {
    max-width: 850px;
}

.content h2 {
    margin-top: 30px;
}

.content p {
    color: #c5cada;
}

footer {
    margin-top: 70px;
    padding: 35px 0 100px;
    border-top: 1px solid var(--border);
    color: var(--muted);
    font-size: 13px;
}

.footerlinks {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    margin-top: 15px;
}

.age-overlay {
    position: fixed;
    inset: 0;
    z-index: 9999;
    background: rgba(0, 0, 0, .94);
    display: none;
    justify-content: center;
    align-items: center;
    padding: 20px;
}

.age-box {
    width: min(440px, 100%);
    padding: 30px;
    border-radius: 20px;
    background: var(--surface);
    border: 1px solid var(--border);
    text-align: center;
}

.age-box h2 {
    font-size: 27px;
}

.sticky-affiliate {
    display: none;
}

.empty {
    color: var(--muted);
    padding: 25px;
}

.notice {
    border-left: 3px solid var(--accent);
    padding: 12px 17px;
    background: var(--surface);
    color: var(--muted);
    margin: 20px 0;
}

@media(max-width: 800px) {
    .grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .controls {
        grid-template-columns: 1fr;
    }
}

@media(max-width: 560px) {
    .container {
        width: calc(100% - 26px);
    }

    .grid {
        grid-template-columns: 1fr;
    }

    .hero {
        padding: 48px 0 35px;
    }

    .searchbox {
        flex-direction: column;
    }

    .nav {
        padding: 14px 0;
    }

    .sticky-affiliate {
        display: block;
        position: fixed;
        z-index: 100;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 10px 12px;
        background: rgba(9, 11, 18, .97);
        border-top: 1px solid var(--border);
    }

    .sticky-affiliate .btn {
        width: 100%;
        font-size: 13px;
    }

    footer {
        padding-bottom: 100px;
    }
}
"""

# ============================================================
# GLOBAL JAVASCRIPT
# ============================================================

JS = r"""
(function () {
    "use strict";

    // Age verification.
    const ageOverlay = document.getElementById("ageOverlay");

    if (ageOverlay) {
        let verified = false;

        try {
            verified = localStorage.getItem("age_verified_18") === "yes";
        } catch (e) {}

        if (!verified) {
            ageOverlay.style.display = "flex";
        }

        const enter = document.getElementById("ageEnter");
        const exit = document.getElementById("ageExit");

        if (enter) {
            enter.addEventListener("click", function () {
                try {
                    localStorage.setItem("age_verified_18", "yes");
                } catch (e) {}

                ageOverlay.style.display = "none";
            });
        }

        if (exit) {
            exit.addEventListener("click", function () {
                window.location.href = "https://www.google.com/";
            });
        }
    }

    // Homepage instant search.
    const search = document.getElementById("promptSearch");
    const searchCards = document.querySelectorAll("[data-search-card]");
    const resultCount = document.getElementById("searchResultCount");

    if (search) {
        search.addEventListener("input", function () {
            const query = this.value.toLowerCase().trim();
            let count = 0;

            searchCards.forEach(function (card) {
                const text = card.dataset.search || "";
                const visible = text.includes(query);

                card.style.display = visible ? "" : "none";

                if (visible) count++;
            });

            if (resultCount) {
                resultCount.textContent =
                    count + " matching prompts";
            }
        });
    }

    // Prompt customizer.
    const promptBox = document.getElementById("promptText");

    if (promptBox) {
        const original = promptBox.dataset.original || "";

        const nameInput = document.getElementById("yourName");
        const aiInput = document.getElementById("aiName");
        const toneInput = document.getElementById("personalityTone");

        function replaceAll(text, key, value) {
            return text.split(key).join(value);
        }

        function updatePrompt() {
            let text = original;

            text = replaceAll(
                text, "{{YOUR_NAME}}",
                nameInput.value.trim() || "Your Name"
            );

            text = replaceAll(
                text, "{{AI_NAME}}",
                aiInput.value.trim() || "AI Name"
            );

            text = replaceAll(
                text, "{{PERSONALITY_TONE}}",
                toneInput.value.trim() || "Warm and engaging"
            );

            // Also support common alternative placeholders.
            text = replaceAll(
                text, "[Your Name]",
                nameInput.value.trim() || "Your Name"
            );

            text = replaceAll(
                text, "[AI Name]",
                aiInput.value.trim() || "AI Name"
            );

            text = replaceAll(
                text, "[Personality Tone]",
                toneInput.value.trim() || "Warm and engaging"
            );

            promptBox.value = text;
            updateCounter();
        }

        [nameInput, aiInput, toneInput].forEach(function (input) {
            if (input) {
                input.addEventListener("input", updatePrompt);
            }
        });

        function updateCounter() {
            const text = promptBox.value;
            const characters = text.length;
            const words = text.trim()
                ? text.trim().split(/\s+/).length : 0;

            // Approximate token count, not a model-specific tokenizer.
            const tokens = Math.ceil(
                text.trim().length / 4
            );

            const badge = document.getElementById("tokenCounter");

            if (badge) {
                badge.textContent =
                    characters + " characters · " +
                    words + " words · ~" + tokens + " tokens";
            }
        }

        const copyButton = document.getElementById("copyPrompt");

        if (copyButton) {
            copyButton.addEventListener("click", async function () {
                try {
                    await navigator.clipboard.writeText(
                        promptBox.value
                    );
                } catch (e) {
                    promptBox.select();
                    document.execCommand("copy");
                }

                const old = this.textContent;
                this.textContent = "Copied!";

                setTimeout(() => {
                    this.textContent = old;
                }, 1800);
            });
        }

        const increase = document.getElementById("fontIncrease");
        const decrease = document.getElementById("fontDecrease");

        if (increase) {
            increase.addEventListener("click", function () {
                const size = parseFloat(
                    getComputedStyle(promptBox).fontSize
                );

                promptBox.style.fontSize =
                    Math.min(size + 2, 30) + "px";
            });
        }

        if (decrease) {
            decrease.addEventListener("click", function () {
                const size = parseFloat(
                    getComputedStyle(promptBox).fontSize
                );

                promptBox.style.fontSize =
                    Math.max(size - 2, 10) + "px";
            });
        }

        updateCounter();
    }

    // Synthesized ambient audio.
    const audioButton = document.getElementById("audioToggle");

    if (audioButton) {
        let context = null;
        let master = null;
        let nodes = [];
        let playing = false;

        const mode = document.getElementById("soundMode");
        const volume = document.getElementById("soundVolume");

        function stopSound() {
            nodes.forEach(function (node) {
                try {
                    node.stop();
                } catch (e) {}

                try {
                    node.disconnect();
                } catch (e) {}
            });

            nodes = [];
        }

        function createNoise(type) {
            const bufferSize = context.sampleRate * 3;
            const buffer = context.createBuffer(
                1, bufferSize, context.sampleRate
            );

            const data = buffer.getChannelData(0);

            let previous = 0;

            for (let i = 0; i < bufferSize; i++) {
                const white = Math.random() * 2 - 1;

                if (type === "rain") {
                    data[i] = white * 0.28;
                } else if (type === "fire") {
                    data[i] = (
                        previous * 0.92 + white * 0.08
                    ) * 0.8;
                } else {
                    data[i] = white * 0.035;
                }

                previous = data[i];
            }

            const source = context.createBufferSource();
            source.buffer = buffer;
            source.loop = true;

            const filter = context.createBiquadFilter();

            filter.type = "lowpass";
            filter.frequency.value =
                type === "rain" ? 1300 :
                type === "fire" ? 500 : 250;

            const gain = context.createGain();
            gain.gain.value = type === "heartbeat" ? 0.7 : 0.8;

            source.connect(filter);
            filter.connect(gain);
            gain.connect(master);

            source.start();

            nodes.push(source, filter, gain);

            if (type === "heartbeat") {
                const oscillator = context.createOscillator();
                const heartbeatGain = context.createGain();

                oscillator.type = "sine";
                oscillator.frequency.value = 48;
                heartbeatGain.gain.value = 0.0001;

                oscillator.connect(heartbeatGain);
                heartbeatGain.connect(master);
                oscillator.start();

                nodes.push(oscillator, heartbeatGain);

                const beat = function () {
                    if (!playing) return;

                    const now = context.currentTime;

                    heartbeatGain.gain.cancelScheduledValues(now);
                    heartbeatGain.gain.setValueAtTime(
                        0.0001, now
                    );

                    heartbeatGain.gain.linearRampToValueAtTime(
                        0.16, now + 0.08
                    );

                    heartbeatGain.gain.exponentialRampToValueAtTime(
                        0.0001, now + 0.35
                    );

                    setTimeout(beat, 950);
                };

                beat();
            }
        }

        function startSound() {
            if (!context) {
                const AudioContext =
                    window.AudioContext ||
                    window.webkitAudioContext;

                if (!AudioContext) {
                    alert("Web Audio API is not supported.");
                    return;
                }

                context = new AudioContext();
                master = context.createGain();
                master.gain.value = Number(volume.value) / 100;
                master.connect(context.destination);
            }

            context.resume();

            stopSound();

            playing = true;

            const selected =
                mode.value === "rain" ? "rain" :
                mode.value === "heartbeat" ? "heartbeat" :
                "fire";

            createNoise(selected);

            audioButton.textContent = "Pause Ambient Sound";
        }

        audioButton.addEventListener("click", function () {
            if (playing) {
                playing = false;
                stopSound();

                audioButton.textContent = "Play Ambient Sound";
            } else {
                startSound();
            }
        });

        mode.addEventListener("change", function () {
            if (playing) startSound();
        });

        volume.addEventListener("input", function () {
            if (master) {
                master.gain.value =
                    Number(volume.value) / 100;
            }
        });
    }
})();
"""

# ============================================================
# HTML COMPONENTS
# ============================================================

def header():
    return f"""
<header>
    <div class="container nav">
        <a class="logo" href="/">{esc(SITE_NAME)}</a>
        <nav class="navlinks" aria-label="Main navigation">
            <a href="/">Home</a>
            <a href="/#categories">Categories</a>
            <a href="/#latest">Latest Prompts</a>
            <a href="/dmca.html">DMCA</a>
        </nav>
    </div>
</header>
"""


def footer():
    return f"""
<footer>
    <div class="container">
        <strong>{esc(SITE_NAME)}</strong>
        <p>{esc(NICHE_TOPIC)}</p>
        <div class="footerlinks">
            <a href="/">Home</a>
            <a href="/dmca.html">DMCA Policy</a>
            <a href="/2257.html">2257 Statement</a>
            <a href="mailto:{esc(CONTACT_EMAIL)}">Contact</a>
        </div>
        <p>
            All prompts are provided for informational and
            entertainment purposes. Use AI services responsibly
            and follow their individual terms and age restrictions.
        </p>
        <p>© {datetime.now().year} {esc(SITE_NAME)}.</p>
    </div>
</footer>
"""


def age_modal():
    return """
<div class="age-overlay" id="ageOverlay">
    <div class="age-box">
        <h2>Adults Only — 18+</h2>
        <p>
            This website is intended for adults aged 18 or older.
            By continuing, you confirm that you meet the legal
            age requirement applicable in your location.
        </p>
        <button class="btn" id="ageEnter">
            I Am 18 or Older — Enter
        </button>
        <p>
            <button class="btn secondary" id="ageExit">
                Exit Website
            </button>
        </p>
        <small class="muted">
            Age verification is a browser-based confirmation
            and is not identity or age authentication.
        </small>
    </div>
</div>
"""


def document(title, description, canonical, body,
             jsonld=None, pagination_head=""):

    structured = ""

    if jsonld:
        structured = (
            '<script type="application/ld+json">'
            + json_script(jsonld)
            + '</script>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description[:300])}">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta name="rating" content="RTA-5042-1996-1400-1577-RTA">
<link rel="canonical" href="{esc(canonical)}">
{pagination_head}
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description[:300])}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:site_name" content="{esc(SITE_NAME)}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description[:200])}">
<style>{CSS}</style>
{structured}
</head>
<body>
{header()}
{body}
{footer()}
{age_modal()}
<script>{JS}</script>
</body>
</html>
"""


def affiliate_box():
    return f"""
<!-- AD_SLOT_MID_CONTENT -->
<div class="affiliate">
    <span class="badge">AI COMPANION EXPERIENCE</span>
    <h3>Bring Your AI Character to Life</h3>
    <p>
        Take your customized prompt to an AI companion platform
        and explore an interactive voice experience.
    </p>
    <a class="btn" href="{esc(AFFILIATE_URL)}"
       rel="nofollow sponsored noopener"
       target="_blank">
        {esc(AFFILIATE_CTA_TEXT)}
    </a>
    <p>
        <small>
            Affiliate disclosure: We may earn a commission
            when you use qualifying partner links.
        </small>
    </p>
</div>
"""


def sticky_affiliate():
    return f"""
<!-- AD_SLOT_STICKY_FOOTER -->
<div class="sticky-affiliate">
    <a class="btn"
       href="{esc(AFFILIATE_URL)}"
       rel="nofollow sponsored noopener"
       target="_blank">
       Launch in AI Companion
    </a>
</div>
"""


def card(item):
    searchable = " ".join([
        item["title"],
        item["target_keyword"],
        item["category"],
        item["subcategory"],
        item["description"],
        " ".join(item["tags_list"])
    ]).lower()

    return f"""
<a class="card"
   href="/prompt/{quote(item['slug'])}.html"
   data-search-card
   data-search="{esc(searchable)}">
    <span class="badge">{esc(item['category'])}</span>
    <h3>{esc(item['title'])}</h3>
    <p>{esc(item['description'][:165])}</p>
    <span class="muted">
        {esc(item['subcategory'])}
    </span>
    <p><strong>Explore Prompt →</strong></p>
</a>
"""


def card_grid(items):
    if not items:
        return '<p class="empty">No prompts found.</p>'

    return '<div class="grid">' + "".join(
        card(item) for item in items
    ) + '</div>'


def breadcrumb(items):
    links = []

    for name, url in items:
        if url:
            links.append(
                f'<a href="{esc(url)}">{esc(name)}</a>'
            )
        else:
            links.append(f'<span>{esc(name)}</span>')

    return (
        '<div class="breadcrumb">'
        + " / ".join(links)
        + '</div>'
    )


def page_headline(title, description):
    return f"""
<section class="section">
    <div class="container">
        <h1 class="detail-title">{esc(title)}</h1>
        <p class="muted">{esc(description)}</p>
    </div>
</section>
"""


# ============================================================
# JSON-LD STRUCTURED DATA
# ============================================================

def make_detail_schema(item):
    url = absolute_url(
        "/prompt/" + quote(item["slug"]) + ".html"
    )

    category_url = absolute_url(
        "/category/" + item["category_slug"] + "/page-1.html"
    )

    schemas = [
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": item["title"],
            "description": item["description"],
            "datePublished": (
                item["upload_date"] or TODAY
            ),
            "dateModified": (
                item["upload_date"] or TODAY
            ),
            "author": {
                "@type": "Organization",
                "name": SITE_NAME
            },
            "publisher": {
                "@type": "Organization",
                "name": SITE_NAME
            },
            "mainEntityOfPage": url,
            "articleSection": item["category"],
            "keywords": ", ".join([
                item["target_keyword"]
            ] + item["tags_list"])
        },
        {
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": "How to Customize and Use " + item["title"],
            "description": item["description"],
            "totalTime": "PT3M",
            "step": [
                {
                    "@type": "HowToStep",
                    "name": "Customize the character",
                    "text": (
                        "Enter your preferred name, AI character "
                        "name and personality tone in the "
                        "interactive customization fields."
                    )
                },
                {
                    "@type": "HowToStep",
                    "name": "Review the prompt",
                    "text": (
                        "Review the generated prompt and adjust "
                        "the wording to suit your preferences."
                    )
                },
                {
                    "@type": "HowToStep",
                    "name": "Copy the prompt",
                    "text": (
                        "Use the Copy Prompt button to copy "
                        "your customized text."
                    )
                },
                {
                    "@type": "HowToStep",
                    "name": "Use your AI companion platform",
                    "text": (
                        "Paste the prompt into a compatible "
                        "AI companion application and follow "
                        "that platform's policies."
                    )
                }
            ]
        },
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "name": "Home",
                    "item": BASE_URL + "/"
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "name": item["category"],
                    "item": category_url
                },
                {
                    "@type": "ListItem",
                    "position": 3,
                    "name": item["title"],
                    "item": url
                }
            ]
        }
    ]

    questions = []

    for q, a in [
        (item["faq_q1"], item["faq_a1"]),
        (item["faq_q2"], item["faq_a2"])
    ]:
        if q and a:
            questions.append({
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": a
                }
            })

    if questions:
        schemas.append({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": questions
        })

    return schemas


# ============================================================
# DETAIL PAGE GENERATOR
# ============================================================

def related_items(item, all_items):
    same_subcategory = [
        x for x in all_items
        if x["slug"] != item["slug"]
        and x["subcategory_slug"] == item["subcategory_slug"]
    ]

    same_subcategory.sort(
        key=lambda x: x["date_object"],
        reverse=True
    )

    related = same_subcategory[:4]

    related_slugs = {
        x["slug"] for x in related
    }

    shared_tags = []

    for other in all_items:
        if other["slug"] == item["slug"]:
            continue

        if other["slug"] in related_slugs:
            continue

        overlap = len(
            set(item["tags_list"])
            & set(other["tags_list"])
        )

        if overlap:
            shared_tags.append((overlap, other))

    shared_tags.sort(
        key=lambda pair: (
            pair[0],
            pair[1]["date_object"]
        ),
        reverse=True
    )

    related.extend([
        other
        for _, other in shared_tags[:4]
    ])

    # Fill any missing recommendations from the same category.
    if len(related) < RELATED_LIMIT:
        for other in all_items:
            if (
                other["slug"] != item["slug"]
                and other["slug"] not in related_slugs
            ):
                related.append(other)
                related_slugs.add(other["slug"])

            if len(related) >= RELATED_LIMIT:
                break

    return related[:RELATED_LIMIT]


def generate_detail(item, all_items):
    canonical_path = (
        "/prompt/" + quote(item["slug"]) + ".html"
    )

    canonical = absolute_url(canonical_path)

    title = (
        item["target_keyword"]
        + " | "
        + SITE_NAME
    )

    prompt = item["prompt_or_script"]

    # Keep raw content in a data attribute safely escaped.
    original_json = json_script(prompt)

    prompt_section = f"""
<div class="container">
    {breadcrumb([
        ("Home", "/"),
        (
            item["category"],
            "/category/" + item["category_slug"] + "/page-1.html"
        ),
        (item["title"], None)
    ])}

    <section>
        <span class="badge">{esc(item['category'])}</span>

        <h1 class="detail-title">{esc(item['title'])}</h1>

        <p class="muted">
            {esc(item['description'])}
        </p>

        <p class="muted">
            Keyword: {esc(item['target_keyword'])}
        </p>
    </section>

    <section class="prompt-panel">
        <h2>Customize Your AI Character</h2>

        <p class="muted">
            Personalize the names and personality tone.
            Changes update the prompt instantly.
        </p>

        <div class="controls">
            <div class="control">
                <label for="yourName">Your Name</label>
                <input id="yourName"
                       type="text"
                       maxlength="80"
                       placeholder="Enter your name">
            </div>

            <div class="control">
                <label for="aiName">AI Name</label>
                <input id="aiName"
                       type="text"
                       maxlength="80"
                       placeholder="Enter AI character name">
            </div>

            <div class="control">
                <label for="personalityTone">
                    Personality Tone
                </label>
                <input id="personalityTone"
                       type="text"
                       maxlength="100"
                       placeholder="Warm and engaging"
                       value="Warm and engaging">
            </div>
        </div>

        <div class="prompt-toolbar">
            <strong>Ready-to-Copy AI Prompt</strong>
            <span class="counter" id="tokenCounter">
                Calculating...
            </span>
        </div>

        <textarea id="promptText"
                  spellcheck="false"
                  aria-label="Customized AI prompt"
                  data-original="{esc(prompt)}"></textarea>

        <div class="prompt-toolbar">
            <div class="prompt-actions">
                <button class="btn" id="copyPrompt">
                    Copy Prompt
                </button>

                <button class="btn secondary" id="fontIncrease">
                    A+
                </button>

                <button class="btn secondary" id="fontDecrease">
                    A-
                </button>
            </div>
        </div>
    </section>

    {affiliate_box()}

    <section class="audio-panel">
        <h2>Ambient Mood Player</h2>

        <p class="muted">
            Enjoy locally synthesized ambient background
            sounds while customizing your prompt.
            No external audio files are loaded.
        </p>

        <div class="audio-controls">
            <button class="btn" id="audioToggle">
                Play Ambient Sound
            </button>

            <select id="soundMode"
                    aria-label="Choose ambient sound">
                <option value="rain">
                    Late Night Rain
                </option>

                <option value="heartbeat">
                    Soft Heartbeat
                </option>

                <option value="fire">
                    Cozy Fireplace Brown Noise
                </option>
            </select>

            <label for="soundVolume">Volume</label>

            <input id="soundVolume"
                   type="range"
                   min="0"
                   max="100"
                   value="35">
        </div>
    </section>

    <section class="content">
        <h2>About This AI Roleplay Prompt</h2>

        <p>{esc(item['description'])}</p>

        <h2>How to Use This Prompt</h2>

        <ol>
            <li>Enter your preferred name.</li>
            <li>Choose an AI character name.</li>
            <li>Set the personality tone.</li>
            <li>Review your customized prompt.</li>
            <li>Copy and paste it into a compatible AI application.</li>
        </ol>

        <h2>Prompt Category</h2>

        <p>
            <a href="/category/{item['category_slug']}/page-1.html">
                {esc(item['category'])}
            </a>
        </p>

        <h2>Explore Related Topics</h2>

        <p>
            <a href="/topic/{item['subcategory_slug']}.html">
                {esc(item['subcategory'])}
            </a>
        </p>

        <h2>Tags</h2>

        <div class="tagcloud">
            {''.join(
                f'<a class="tag" href="/tag/{tag_slug}.html">'
                f'{esc(tag)}</a>'
                for tag, tag_slug in zip(
                    item["tags_list"],
                    item["tag_slugs"]
                )
            )}
        </div>

        <h2>Frequently Asked Questions</h2>

        {''.join(
            f'<div><h3>{esc(q)}</h3><p>{esc(a)}</p></div>'
            for q, a in [
                (item["faq_q1"], item["faq_a1"]),
                (item["faq_q2"], item["faq_a2"])
            ]
            if q and a
        )}
    </section>

    <section class="section">
        <h2 class="section-heading">
            Related AI Prompts
        </h2>

        {card_grid(related_items(item, all_items))}
    </section>

    <div class="notice">
        AI-generated roleplay prompts are intended for
        lawful, consensual and age-appropriate fictional use.
        Respect the rules of any third-party AI platform.
    </div>
</div>

{sticky_affiliate()}
"""

    html_page = document(
        title,
        item["description"],
        canonical,
        prompt_section,
        make_detail_schema(item)
    )

    write_file(
        "prompt/" + item["slug"] + ".html",
        html_page
    )


# ============================================================
# HOMEPAGE
# ============================================================

def generate_home(items, tag_names, tag_mapping):
    newest = sorted(
        items,
        key=lambda x: x["date_object"],
        reverse=True
    )[:NEWEST_LIMIT]

    categories = defaultdict(list)
    subcategories = defaultdict(list)
    tags = defaultdict(list)

    for item in items:
        categories[
            item["category_slug"]
        ].append(item)

        subcategories[
            item["subcategory_slug"]
        ].append(item)

        for tag_slug in item["tag_slugs"]:
            tags[tag_slug].append(item)

    category_html = []

    for category_slug, group in sorted(
        categories.items(),
        key=lambda x: x[0]
    ):
        name = group[0]["category"]

        category_html.append(f"""
<a class="card"
   href="/category/{category_slug}/page-1.html">
    <h3>{esc(name)}</h3>
    <span class="count">{len(group)} prompts</span>
    <p>Explore AI prompts in this category.</p>
</a>
""")

    subcategory_html = []

    for sub_slug, group in sorted(subcategories.items()):
        name = group[0]["subcategory"]

        subcategory_html.append(f"""
<a class="tag"
   href="/topic/{sub_slug}.html">
    {esc(name)} ({len(group)})
</a>
""")

    tag_html = []

    for tag in tag_names:
        tag_slug = tag_mapping[tag]

        tag_html.append(f"""
<a class="tag"
   href="/tag/{tag_slug}.html">
    {esc(tag)} ({len(tags[tag_slug])})
</a>
""")

    body = f"""
<section class="hero">
    <div class="container">
        <span class="badge">AI COMPANION PROMPT LIBRARY</span>

        <h1>Discover Your Perfect AI Girlfriend Prompt</h1>

        <p>
            Explore customizable AI companion prompts,
            fictional character personalities and voice
            roleplay scripts. Personalize your experience
            and create conversations that match your style.
        </p>

        <div class="searchbox">
            <input id="promptSearch"
                   type="search"
                   placeholder="Search prompts, keywords or tags..."
                   aria-label="Search AI prompts">

            <a class="btn" href="#latest">
                Explore Prompts
            </a>
        </div>

        <p id="searchResultCount" class="muted">
            {len(items)} prompts available
        </p>
    </div>
</section>

<section class="section" id="categories">
    <div class="container">
        <h2 class="section-heading">
            Browse Prompt Categories
        </h2>

        <div class="grid">
            {''.join(category_html)}
        </div>
    </div>
</section>

<section class="section">
    <div class="container">
        <h2 class="section-heading">
            Explore Subcategories
        </h2>

        <div class="tagcloud">
            {''.join(subcategory_html)}
        </div>
    </div>
</section>

<section class="section">
    <div class="container">
        <h2 class="section-heading">
            Popular Prompt Tags
        </h2>

        <div class="tagcloud">
            {''.join(tag_html)}
        </div>
    </div>
</section>

<!-- AD_SLOT_TOP_BANNER -->
<!-- AD_SLOT_POPUNDER -->

<section class="section" id="latest">
    <div class="container">
        <h2 class="section-heading">
            Latest AI Girlfriend Prompts
        </h2>

        <p class="muted">
            Discover the newest additions to our prompt library.
        </p>

        {card_grid(newest)}
    </div>
</section>

<section class="section">
    <div class="container">
        <h2 class="section-heading">
            About {esc(SITE_NAME)}
        </h2>

        <div class="content">
            <p>
                {esc(SITE_NAME)} is a searchable library
                of customizable AI companion and voice
                roleplay prompts. Discover fictional character
                concepts, conversation starters and personality
                templates organized into useful topic clusters.
            </p>

            <p>
                Each prompt includes an interactive editor
                that lets you personalize names and personality
                settings before copying your customized text.
            </p>

            <p>
                Browse categories, subcategories and tags
                to discover relevant ideas without downloading
                external media.
            </p>
        </div>
    </div>
</section>
"""

    body += sticky_affiliate()

    html_page = document(
        SITE_NAME + " | " + NICHE_TOPIC,
        (
            "Discover customizable AI girlfriend prompts, "
            "AI companion personalities, voice roleplay scripts "
            "and interactive character templates."
        ),
        absolute_url("/"),
        body
    )

    write_file("index.html", html_page)


# ============================================================
# CATEGORY HUBS
# ============================================================

def generate_categories(items):
    categories = defaultdict(list)

    for item in items:
        categories[item["category_slug"]].append(item)

    for category_slug, group in categories.items():
        group.sort(
            key=lambda x: x["date_object"],
            reverse=True
        )

        category_name = group[0]["category"]

        page_count = max(
            1,
            math.ceil(len(group) / ITEMS_PER_PAGE)
        )

        for page_number in range(1, page_count + 1):
            start = (
                page_number - 1
            ) * ITEMS_PER_PAGE

            page_items = group[
                start:start + ITEMS_PER_PAGE
            ]

            path = (
                f"/category/{category_slug}/"
                f"page-{page_number}.html"
            )

            canonical = absolute_url(path)

            title = (
                f"{category_name} AI Prompts"
                + (
                    f" - Page {page_number}"
                    if page_number > 1 else ""
                )
                + f" | {SITE_NAME}"
            )

            description = (
                f"Explore {len(group)} AI companion and "
                f"voice roleplay prompts in {category_name}. "
                "Browse customizable prompts and related topics."
            )

            pagination_head = ""

            if page_number > 1:
                pagination_head += (
                    f'<link rel="prev" href="{absolute_url(
                        f"/category/{category_slug}/page-{page_number-1}.html"
                    )}">'
                )

            if page_number < page_count:
                pagination_head += (
                    f'<link rel="next" href="{absolute_url(
                        f"/category/{category_slug}/page-{page_number+1}.html"
                    )}">'
                )

            pagination = '<div class="pagination">'

            if page_number > 1:
                pagination += (
                    f'<a href="/category/{category_slug}/'
                    f'page-{page_number-1}.html">← Previous</a>'
                )

            for number in range(1, page_count + 1):
                if number == page_number:
                    pagination += (
                        f'<span>{number}</span>'
                    )
                else:
                    pagination += (
                        f'<a href="/category/{category_slug}/'
                        f'page-{number}.html">{number}</a>'
                    )

            if page_number < page_count:
                pagination += (
                    f'<a href="/category/{category_slug}/'
                    f'page-{page_number+1}.html">Next →</a>'
                )

            pagination += '</div>'

            body = f"""
<div class="container">
    {breadcrumb([
        ("Home", "/"),
        (category_name, None)
    ])}

    {page_headline(
        category_name + " AI Prompts",
        description
    )}

    <p class="muted">
        Page {page_number} of {page_count}
        · {len(group)} total prompts
    </p>

    {card_grid(page_items)}

    {pagination}

    <div class="notice">
        Browse the complete collection of
        {esc(category_name)} prompts.
    </div>
</div>
"""

            write_file(
                f"category/{category_slug}/page-{page_number}.html",
                document(
                    title,
                    description,
                    canonical,
                    body,
                    pagination_head=pagination_head
                )
            )


# ============================================================
# SUBCATEGORY HUBS
# ============================================================

def generate_topics(items):
    topics = defaultdict(list)

    for item in items:
        topics[item["subcategory_slug"]].append(item)

    for sub_slug, group in topics.items():
        group.sort(
            key=lambda x: x["date_object"],
            reverse=True
        )

        name = group[0]["subcategory"]

        title = name + " AI Roleplay Prompts | " + SITE_NAME

        description = (
            f"Discover {len(group)} customizable AI companion "
            f"prompts and character roleplay ideas about {name}."
        )

        body = f"""
<div class="container">
    {breadcrumb([
        ("Home", "/"),
        (name, None)
    ])}

    {page_headline(name + " Prompts", description)}

    <p class="muted">
        {len(group)} prompts in this topic.
    </p>

    {card_grid(group)}

    <section class="section">
        <h2>Explore More Topics</h2>

        <div class="tagcloud">
            <a class="tag" href="/">All Topics</a>
        </div>
    </section>
</div>
"""

        write_file(
            f"topic/{sub_slug}.html",
            document(
                title,
                description,
                absolute_url(f"/topic/{sub_slug}.html"),
                body
            )
        )


# ============================================================
# TAG HUBS
# ============================================================

def generate_tags(items, tag_names, tag_mapping):
    tag_groups = defaultdict(list)

    for item in items:
        for tag in item["tags_list"]:
            tag_groups[tag].append(item)

    for tag in tag_names:
        tag_slug = tag_mapping[tag]
        group = tag_groups[tag]

        group.sort(
            key=lambda x: x["date_object"],
            reverse=True
        )

        title = (
            f"{tag} AI Prompts and Roleplay Ideas | {SITE_NAME}"
        )

        description = (
            f"Browse {len(group)} AI companion prompts "
            f"tagged with {tag}. Discover related characters "
            "and customizable roleplay ideas."
        )

        body = f"""
<div class="container">
    {breadcrumb([
        ("Home", "/"),
        ("Tags", None),
        (tag, None)
    ])}

    {page_headline(
        tag + " AI Prompts",
        description
    )}

    <p class="muted">
        {len(group)} matching prompts.
    </p>

    {card_grid(group)}
</div>
"""

        write_file(
            f"tag/{tag_slug}.html",
            document(
                title,
                description,
                absolute_url(f"/tag/{tag_slug}.html"),
                body
            )
        )


# ============================================================
# COMPLIANCE PAGES
# ============================================================

def generate_dmca():
    body = f"""
<div class="container content">
    <h1>DMCA Copyright Policy</h1>

    <p>
        {esc(SITE_NAME)} respects intellectual property rights
        and expects visitors and contributors to do the same.
    </p>

    <h2>Submitting a Copyright Complaint</h2>

    <p>
        If you believe that material appearing on this website
        infringes your copyright, please send a written notice
        to our designated contact address.
    </p>

    <p><strong>Email:</strong>
        <a href="mailto:{esc(CONTACT_EMAIL)}">
            {esc(CONTACT_EMAIL)}
        </a>
    </p>

    <h2>Information to Include</h2>

    <ol>
        <li>Identification of the copyrighted work.</li>
        <li>The exact URL of the allegedly infringing material.</li>
        <li>Your contact information.</li>
        <li>A statement of good-faith belief that the use is unauthorized.</li>
        <li>A statement under penalty of perjury that the information is accurate and that you are authorized to act.</li>
        <li>Your physical or electronic signature.</li>
    </ol>

    <h2>Counter-Notification</h2>

    <p>
        If content has been removed following a copyright
        complaint and you believe the removal was mistaken,
        contact us with the applicable counter-notification
        information and supporting details.
    </p>

    <h2>Repeat Infringement</h2>

    <p>
        Appropriate action may be taken against repeat
        infringers, where applicable.
    </p>

    <h2>Important</h2>

    <p>
        This page describes our intended notice-handling
        process and is not a representation that the website
        qualifies for any particular statutory safe harbor.
        Legal notices should be reviewed and handled in
        accordance with applicable law.
    </p>
</div>
"""

    write_file(
        "dmca.html",
        document(
            "DMCA Copyright Policy | " + SITE_NAME,
            "DMCA copyright complaint and contact information.",
            absolute_url("/dmca.html"),
            body
        )
    )


def generate_2257():
    body = f"""
<div class="container content">
    <h1>18 U.S.C. § 2257 Statement</h1>

    <p>
        This website is primarily a directory of textual
        AI companion prompts, fictional roleplay templates
        and related informational material.
    </p>

    <h2>Nature of Website Content</h2>

    <p>
        The website generator does not create, host or embed
        external pornographic images or videos. Its primary
        output consists of text-based prompt descriptions
        and interactive text customization tools.
    </p>

    <h2>Third-Party Platforms</h2>

    <p>
        Links to third-party services may be provided.
        Those services operate independently and maintain
        their own content, policies and legal obligations.
    </p>

    <h2>Compliance Information</h2>

    <p>
        This statement is informational only. It does not
        constitute a legal determination that any particular
        content or operator is exempt from record-keeping,
        labeling or other obligations under 18 U.S.C. § 2257
        or applicable regulations.
    </p>

    <p>
        The website operator should obtain qualified legal
        advice to determine whether additional compliance
        measures, records or disclosures are required.
    </p>

    <h2>Contact</h2>

    <p>
        Questions may be sent to:
        <a href="mailto:{esc(CONTACT_EMAIL)}">
            {esc(CONTACT_EMAIL)}
        </a>
    </p>
</div>
"""

    write_file(
        "2257.html",
        document(
            "18 U.S.C. Section 2257 Statement | " + SITE_NAME,
            "Website content and 2257 informational statement.",
            absolute_url("/2257.html"),
            body
        )
    )


# ============================================================
# XML SITEMAP XSL
# ============================================================

def generate_sitemap_xsl():
    xsl = r"""<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:s="http://www.sitemaps.org/schemas/sitemap/0.9">

<xsl:output method="html" encoding="UTF-8" indent="yes"/>

<xsl:template match="/">
<html>
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>XML Sitemap Directory</title>
<style>
body {
    margin:0;
    background:#090b12;
    color:#f3f4fa;
    font-family:system-ui,sans-serif;
}
main {
    max-width:1000px;
    margin:50px auto;
    padding:20px;
}
h1 { color:#c4a6ff; }
p { color:#a0a8bd; }
table {
    width:100%;
    border-collapse:collapse;
    background:#111522;
    border-radius:12px;
    overflow:hidden;
}
th,td {
    text-align:left;
    padding:14px;
    border-bottom:1px solid #292f42;
}
th { color:#c4a6ff; }
a { color:#bba1ff; }
a:hover { color:#fff; }
</style>
</head>
<body>
<main>
<h1>XML Sitemap Directory</h1>
<p>Search engine discovery index.</p>
<table>
<thead>
<tr><th>URL</th><th>Last Modified</th></tr>
</thead>
<tbody>
<xsl:for-each select="s:urlset/s:url">
<tr>
<td>
<a href="{s:loc}">
<xsl:value-of select="s:loc"/>
</a>
</td>
<td><xsl:value-of select="s:lastmod"/></td>
</tr>
</xsl:for-each>
<xsl:for-each select="s:sitemapindex/s:sitemap">
<tr>
<td>
<a href="{s:loc}">
<xsl:value-of select="s:loc"/>
</a>
</td>
<td><xsl:value-of select="s:lastmod"/></td>
</tr>
</xsl:for-each>
</tbody>
</table>
</main>
</body>
</html>
</xsl:template>
</xsl:stylesheet>
"""

    write_file("sitemap.xsl", xsl)


# ============================================================
# SITEMAPS
# ============================================================

def generate_sitemaps(items):
    urls = set()

    def add(path):
        urls.add(absolute_url(path))

    add("/")
    add("/dmca.html")
    add("/2257.html")

    for item in items:
        add("/prompt/" + quote(item["slug"]) + ".html")

    categories = defaultdict(list)
    topics = set()
    tags = set()

    for item in items:
        categories[item["category_slug"]].append(item)
        topics.add(item["subcategory_slug"])
        tags.update(item["tag_slugs"])

    for category_slug, group in categories.items():
        pages = max(
            1,
            math.ceil(len(group) / ITEMS_PER_PAGE)
        )

        for page in range(1, pages + 1):
            add(
                f"/category/{category_slug}/page-{page}.html"
            )

    for topic in topics:
        add("/topic/" + topic + ".html")

    for tag in tags:
        add("/tag/" + tag + ".html")

    sorted_urls = sorted(urls)

    chunks = [
        sorted_urls[i:i + SITEMAP_LIMIT]
        for i in range(0, len(sorted_urls), SITEMAP_LIMIT)
    ]

    if not chunks:
        chunks = [[]]

    for index, chunk in enumerate(chunks, start=1):
        records = []

        for url in chunk:
            records.append(f"""
    <url>
        <loc>{esc(url)}</loc>
        <lastmod>{TODAY}</lastmod>
    </url>""")

        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<?xml-stylesheet type="text/xsl" href="/sitemap.xsl"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            + "".join(records)
            + "\n</urlset>"
        )

        write_file(
            f"sitemap-{index}.xml",
            xml
        )

    sitemap_records = []

    for index in range(1, len(chunks) + 1):
        sitemap_records.append(f"""
    <sitemap>
        <loc>{absolute_url(f'/sitemap-{index}.xml')}</loc>
        <lastmod>{TODAY}</lastmod>
    </sitemap>""")

    sitemap_index = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<?xml-stylesheet type="text/xsl" href="/sitemap.xsl"?>\n'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(sitemap_records)
        + "\n</sitemapindex>"
    )

    write_file("sitemap.xml", sitemap_index)

    generate_sitemap_xsl()

    robots = f"""User-agent: *
Allow: /

Sitemap: {BASE_URL}/sitemap.xml
"""

    write_file("robots.txt", robots)


# ============================================================
# CLOUDFLARE PAGES HEADERS
# ============================================================

def generate_headers():
    headers = r"""/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  X-Frame-Options: SAMEORIGIN

/*.html
  Content-Type: text/html; charset=utf-8

/*.xml
  Content-Type: application/xml; charset=utf-8

/*.xsl
  Content-Type: application/xslt+xml; charset=utf-8

/*.txt
  Content-Type: text/plain; charset=utf-8
"""

    write_file("_headers", headers)


# ============================================================
# BUILD REPORT
# ============================================================

def generate_report(items, tag_names):
    categories = len({
        item["category_slug"] for item in items
    })

    topics = len({
        item["subcategory_slug"] for item in items
    })

    report = f"""
{SITE_NAME}
========================================

Build completed successfully.

Website URL:
{BASE_URL}

Total prompts: {len(items)}
Categories: {categories}
Subcategories: {topics}
Unique tags: {len(tag_names)}

Generated files:
- index.html
- prompt/*.html
- category/*/page-*.html
- topic/*.html
- tag/*.html
- sitemap.xml
- sitemap-*.xml
- sitemap.xsl
- robots.txt
- dmca.html
- 2257.html
- _headers

Output directory:
{OUTPUT_DIR.resolve()}
"""

    write_file("BUILD_REPORT.txt", report)


# ============================================================
# MAIN BUILD FUNCTION
# ============================================================

def build():
    print("=" * 60)
    print(SITE_NAME)
    print("Static Website Generator")
    print("=" * 60)

    print("\n[1/12] Loading CSV data...")

    items, tag_names, tag_mapping = load_data()

    print(f"Loaded {len(items)} prompts.")

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("\n[2/12] Generating homepage...")

    generate_home(
        items,
        tag_names,
        tag_mapping
    )

    print("\n[3/12] Generating prompt detail pages...")

    for index, item in enumerate(items, start=1):
        generate_detail(item, items)

        if index % 100 == 0:
            print(
                f"Generated {index}/{len(items)} detail pages."
            )

    print(
        f"Generated {len(items)} detail pages."
    )

    print("\n[4/12] Generating category hubs...")

    generate_categories(items)

    print("\n[5/12] Generating subcategory hubs...")

    generate_topics(items)

    print("\n[6/12] Generating tag hubs...")

    generate_tags(
        items,
        tag_names,
        tag_mapping
    )

    print("\n[7/12] Generating DMCA page...")

    generate_dmca()

    print("\n[8/12] Generating 2257 statement...")

    generate_2257()

    print("\n[9/12] Generating XML sitemaps...")

    generate_sitemaps(items)

    print("\n[10/12] Generating Cloudflare headers...")

    generate_headers()

    print("\n[11/12] Generating build report...")

    generate_report(items, tag_names)

    print("\n[12/12] Build verification...")

    required_files = [
        "index.html",
        "sitemap.xml",
        "sitemap.xsl",
        "robots.txt",
        "dmca.html",
        "2257.html",
        "_headers",
    ]

    missing = [
        filename
        for filename in required_files
        if not (OUTPUT_DIR / filename).exists()
    ]

    if missing:
        raise RuntimeError(
            "Build verification failed: "
            + ", ".join(missing)
        )

    html_count = len(
        list(OUTPUT_DIR.rglob("*.html"))
    )

    total_files = len(
        list(OUTPUT_DIR.rglob("*"))
    )

    total_size = sum(
        path.stat().st_size
        for path in OUTPUT_DIR.rglob("*")
        if path.is_file()
    )

    print("\n" + "=" * 60)
    print("BUILD SUCCESSFUL")
    print("=" * 60)

    print(f"Prompts: {len(items)}")
    print(f"HTML pages: {html_count}")
    print(f"Total files: {total_files}")
    print(
        f"Total size: {total_size / (1024 * 1024):.2f} MB"
    )

    print(f"\nOutput: {OUTPUT_DIR.resolve()}")

    print("\nCloudflare Pages deployment:")
    print("Upload the contents of the dist/ directory.")

    print("\nImportant publishing checklist:")
    print("- Verify all generated content is accurate and useful.")
    print("- Replace #affiliate-link with a real partner URL.")
    print("- Disclose affiliate relationships clearly.")
    print("- Review local age-verification requirements.")
    print("- Review applicable copyright and record-keeping laws.")
    print("- Test all links and interactive functionality.")
    print("- Submit sitemap.xml to search engines.")
    print("- Do not assume age gates or metadata establish legal compliance.")

    print("\nDone!")


if __name__ == "__main__":
    try:
        build()
    except Exception as error:
        print("\nBUILD FAILED:")
        print(str(error))
        raise
