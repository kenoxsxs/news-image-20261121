#!/usr/bin/env python3
"""World news front page — Saturday 21 November 2026.

Deterministic PIL renderer: no network, no randomness, no time dependence.
Run twice and the PNG is byte-identical. Output: entry.png, 1024x1024, <= 1 MiB.
Composed fresh in this session from the refined front-page image (design
reference) and the verified research notes; every headline, summary and
source line was transcribed from that image by hand.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")

# ---------------------------------------------------------------- palette
NAVY = (46, 52, 104)
NAVY_DK = (24, 30, 52)
GOLD = (212, 178, 92)
GOLD_LT = (232, 205, 120)
CREAM = (250, 247, 238)
PAPER = (255, 255, 255)
INK = (26, 26, 26)
MUTED = (110, 110, 110)
FAINT = (220, 214, 200)
RED = (190, 96, 110)
TAN = (198, 141, 95)
PURPLE = (140, 125, 181)
TEAL = (77, 155, 144)
STEEL = (99, 129, 169)
PINK = (197, 117, 147)
GREEN = (110, 160, 110)
SRC = (100, 140, 150)

FONT_DIRS = ("/usr/share/fonts/truetype/dejavu",
             "/usr/share/fonts/truetype/liberation")


def font(name, size):
    for d in FONT_DIRS:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    raise OSError("font not found: " + name)


def serif_b(s):
    return font("LiberationSerif-Bold.ttf", s)


def serif(s):
    return font("LiberationSerif-Regular.ttf", s)


def serif_i(s):
    return font("LiberationSerif-Italic.ttf", s)


def sans(s):
    return font("DejaVuSans.ttf", s)


def sans_b(s):
    return font("DejaVuSans-Bold.ttf", s)


# ---------------------------------------------------------------- text tools
def text_w(draw, s, f):
    return draw.textlength(s, font=f)


def wrap(draw, text, f, max_w):
    """Greedy word wrap to a pixel width."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = (cur + " " + word).strip()
        if text_w(draw, trial, f) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit_lines(draw, text, f, max_w, max_lines, min_size, fname):
    """Wrap; shrink the font until the text fits max_lines."""
    size = f.size
    while size >= min_size:
        ff = font(fname, size)
        lines = wrap(draw, text, ff, max_w)
        if len(lines) <= max_lines:
            return ff, lines
        size -= 1
    ff = font(fname, min_size)
    return ff, wrap(draw, text, ff, max_w)[:max_lines]


def draw_lines(draw, lines, x, y, f, color, leading=None):
    lh = leading or int(f.size * 1.22)
    for ln in lines:
        draw.text((x, y), ln, font=f, fill=color)
        y += lh
    return y


def draw_justified(draw, lines, x, y, max_w, f, color, leading=None):
    """Draw lines like draw_lines, but every line except the last is
    justified to max_w, so the right margin is straight. A line is
    justified only when it is already at least 80% full, so the extra
    word spacing stays natural."""
    lh = leading or int(f.size * 1.22)
    for i, ln in enumerate(lines):
        words = ln.split(" ")
        last = (i == len(lines) - 1)
        if not last and len(words) > 1:
            lw = text_w(draw, ln, f)
            if lw >= 0.8 * max_w:
                extra = (max_w - lw) / (len(words) - 1)
                cx = x
                for wd in words:
                    draw.text((cx, y), wd, font=f, fill=color)
                    cx += text_w(draw, wd, f) + text_w(draw, " ", f) + extra
                y += lh
                continue
        draw.text((x, y), ln, font=f, fill=color)
        y += lh
    return y


# ---------------------------------------------------------------- flags
def draw_union_jack(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(0, 36, 125))
    d.line([x, y, x + w, y + h], fill=(255, 255, 255), width=5)
    d.line([x + w, y, x, y + h], fill=(255, 255, 255), width=5)
    d.line([x, y, x + w, y + h], fill=(200, 16, 46), width=2)
    d.line([x + w, y, x, y + h], fill=(200, 16, 46), width=2)
    d.rectangle([x + w // 2 - 4, y, x + w // 2 + 4, y + h], fill=(255, 255, 255))
    d.rectangle([x, y + h // 2 - 4, x + w, y + h // 2 + 4], fill=(255, 255, 255))
    d.rectangle([x + w // 2 - 2, y, x + w // 2 + 2, y + h], fill=(200, 16, 46))
    d.rectangle([x, y + h // 2 - 2, x + w, y + h // 2 + 2], fill=(200, 16, 46))


def draw_eu_flag(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(0, 51, 153))
    for k in range(12):
        ang = -math.pi / 2 + k * math.pi / 6
        sx = x + w // 2 + int(11 * math.cos(ang))
        sy = y + h // 2 + int(8 * math.sin(ang))
        d.ellipse([sx - 1, sy - 1, sx + 1, sy + 1], fill=(255, 204, 0))


def draw_id_flag(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h // 2], fill=(210, 0, 0))
    d.rectangle([x, y + h // 2, x + w, y + h], fill=(255, 255, 255))
    d.rectangle([x, y, x + w, y + h], outline=(180, 180, 180), width=1)


# ---------------------------------------------------------------- visuals
# Each draws its own scene inside a 112x88 box at (x0, y0).
def v_candles(d, x0, y0, w=112, h=88):
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=(44, 36, 64))
    for gy in range(4):
        gy_y = y0 + 14 + gy * 18
        d.line([x0 + 6, gy_y, x0 + w - 6, gy_y], fill=(74, 64, 96), width=1)
    closes = [16, 26, 34, 46, 54, 66]
    cols = [(60, 180, 110), (226, 80, 80), (226, 80, 80),
            (60, 180, 110), (226, 80, 80), (226, 80, 80)]
    for i, c in enumerate(closes):
        cx = x0 + 12 + i * 15
        top = y0 + c
        d.line([cx + 4, top - 6, cx + 4, top + 15], fill=cols[i], width=2)
        d.rectangle([cx, top, cx + 9, top + 11], fill=cols[i])
    d.line([x0 + 8, y0 + 14, x0 + w - 8, y0 + 74], fill=(255, 255, 255), width=2)
    d.text((x0 + 6, y0 + 4), "NASDAQ", font=sans_b(8), fill=(255, 255, 255))
    d.text((x0 + 6, y0 + h - 16), "-5.28%", font=sans_b(11), fill=(255, 255, 255))


def v_seismo(d, x0, y0, w=112, h=88):
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=(44, 56, 110))
    pts = []
    n = 30
    for i in range(n + 1):
        px = x0 + 4 + i * (w - 8) / n
        if i in (14, 15, 16):
            amp = [30, -26, 18][i - 14]
        elif i in (13, 17):
            amp = 10 if i == 13 else -8
        else:
            amp = ((i * 7) % 5) - 2
        pts.append((px, y0 + h // 2 + amp))
    d.line(pts, fill=(240, 200, 90), width=2)
    d.ellipse([x0 + w - 30, y0 + 6, x0 + w - 6, y0 + 30], fill=RED)
    d.text((x0 + w - 27, y0 + 11), "6.8", font=sans_b(11), fill=(255, 255, 255))
    d.text((x0 + 6, y0 + h - 15), "PERU · JUNÍN", font=sans_b(8),
           fill=(255, 255, 255))


def v_flags_uk(d, x0, y0, w=112, h=88):
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=PURPLE)
    draw_union_jack(d, x0 + 8, y0 + 10, 42, 28)
    draw_eu_flag(d, x0 + 62, y0 + 10, 42, 28)
    d.text((x0 + 8, y0 + 44), "100,000", font=sans_b(16), fill=(255, 255, 255))
    d.text((x0 + 8, y0 + 64), "youth visas a year", font=sans_b(8),
           fill=(255, 255, 255))
    d.text((x0 + 8, y0 + 76), "UK–EU DEAL", font=sans_b(8), fill=GOLD_LT)


def v_flags_id(d, x0, y0, w=112, h=88):
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=TEAL)
    draw_id_flag(d, x0 + 8, y0 + 10, 42, 28)
    draw_eu_flag(d, x0 + 62, y0 + 10, 42, 28)
    d.text((x0 + 8, y0 + 44), "98.5%", font=sans_b(16), fill=(255, 255, 255))
    d.text((x0 + 8, y0 + 64), "of tariff lines", font=sans_b(8), fill=(255, 255, 255))
    d.text((x0 + 8, y0 + 76), "IEU-CEPA", font=sans_b(8), fill=GOLD_LT)


def v_cop(d, x0, y0, w=112, h=88):
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=GREEN)
    cx, cy, r = x0 + 56, y0 + 22, 15
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255),
              outline=NAVY, width=2)
    d.line([cx, cy, cx, cy - 10], fill=NAVY, width=2)
    d.line([cx, cy, cx + 8, cy + 4], fill=NAVY, width=2)
    t = "OVERTIME"
    d.text((x0 + (w - text_w(d, t, sans_b(10))) / 2, y0 + 42), t,
           font=sans_b(10), fill=(255, 255, 255))
    t2 = "fossil fuels"
    tx = x0 + (w - text_w(d, t2, sans_b(11))) / 2
    d.text((tx, y0 + 56), t2, font=sans_b(11), fill=(178, 34, 34))
    d.line([tx - 2, y0 + 63, tx + text_w(d, t2, sans_b(11)) + 2, y0 + 63],
           fill=(178, 34, 34), width=2)
    t3 = "ANTALYA · COP31"
    d.text((x0 + (w - text_w(d, t3, sans_b(8))) / 2, y0 + 72), t3,
           font=sans_b(8), fill=(255, 255, 255))


def v_poland(d, x0, y0, w=112, h=88):
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=PURPLE)
    poly = [(20, 30), (34, 16), (58, 12), (80, 18), (92, 32), (86, 50),
            (80, 68), (58, 76), (36, 72), (24, 56)]
    poly = [(x0 + px, y0 + py) for px, py in poly]
    d.polygon(poly, fill=(255, 255, 255))
    low = [(24, 50), (92, 44), (88, 52), (80, 68), (58, 76), (36, 72), (24, 56)]
    low = [(x0 + px, y0 + py) for px, py in low]
    d.polygon(low, fill=(220, 60, 70))
    d.polygon(poly, outline=NAVY)
    for dx, dy in ((84, 34), (90, 44), (78, 48)):
        d.ellipse([x0 + dx - 4, y0 + dy - 4, x0 + dx + 4, y0 + dy + 4],
                  fill=(255, 204, 0), outline=(255, 255, 255))
    d.text((x0 + 6, y0 + 4), "POLAND", font=sans_b(9), fill=(255, 255, 255))
    d.text((x0 + 6, y0 + h - 14), "3 impact sites", font=sans_b(8),
           fill=(255, 255, 255))


def v_cyclone(d, x0, y0, w=112, h=88):
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=STEEL)
    cx, cy = x0 + 56, y0 + 22
    for k in range(5):
        r0 = 4 + k * 3
        a0 = k * 0.9
        pts = []
        for i in range(25):
            a = a0 + 4.4 * i / 24
            r = r0 + k * 3 * i / 24
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        d.line(pts, fill=(255, 255, 255), width=2)
    d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=(255, 255, 255))
    t = "~300,000"
    d.text((x0 + (w - text_w(d, t, sans_b(15))) / 2, y0 + 48), t,
           font=sans_b(15), fill=(255, 255, 255))
    t2 = "evacuated · Odisha"
    d.text((x0 + (w - text_w(d, t2, sans_b(8))) / 2, y0 + 68), t2,
           font=sans_b(8), fill=(255, 255, 255))


def v_cricket(d, x0, y0, w=112, h=88):
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=GREEN)
    d.text((x0 + 6, y0 + 4), "13th", font=sans_b(9), fill=(255, 255, 255))
    d.text((x0 + 44, y0 + 2), "★", font=sans_b(12), fill=GOLD_LT)
    d.text((x0 + 56, y0 + 6), "100", font=serif_b(26), fill=GOLD_LT)
    d.rounded_rectangle([x0 + 12, y0 + 32, x0 + 34, y0 + 74], radius=4,
                        fill=(214, 178, 120), outline=(150, 110, 60))
    d.rectangle([x0 + 20, y0 + 14, x0 + 26, y0 + 34], fill=(120, 80, 40))
    for sx in (44, 50, 56):
        d.rectangle([x0 + sx, y0 + 46, x0 + sx + 3, y0 + 74], fill=(240, 220, 180))
    d.ellipse([x0 + 72, y0 + 56, x0 + 84, y0 + 68], fill=(178, 34, 34))
    d.text((x0 + 6, y0 + h - 14), "Wellington", font=sans_b(8),
           fill=(255, 255, 255))


def v_riyadh(d, x0, y0, w=112, h=88):
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=NAVY_DK)
    base = y0 + h - 16
    d.rectangle([x0 + 48, y0 + 14, x0 + 64, base], fill=(120, 140, 180))
    d.polygon([(x0 + 48, y0 + 14), (x0 + 56, y0 + 26), (x0 + 64, y0 + 14)],
              fill=NAVY_DK)
    for bx, bw_, bh_ in ((8, 12, 30), (26, 10, 42), (68, 12, 36), (84, 10, 26)):
        d.rectangle([x0 + bx, base - bh_, x0 + bx + bw_, base],
                    fill=(90, 110, 150))
    for wx in (12, 30, 52, 72, 88):
        for wy in (base - 24, base - 14):
            d.rectangle([x0 + wx, wy, x0 + wx + 2, wy + 2], fill=(255, 220, 120))
    for ax, ay in ((22, 20), (56, 12), (88, 22)):
        d.arc([x0 + ax - 12, y0 + ay - 4, x0 + ax + 12, y0 + ay + 16],
              start=200, end=340, fill=GOLD_LT, width=2)
        d.ellipse([x0 + ax - 2, y0 + ay - 2, x0 + ax + 2, y0 + ay + 2],
                  fill=GOLD_LT)
    d.text((x0 + 6, y0 + h - 13), "3 missiles intercepted", font=sans_b(8),
           fill=(255, 255, 255))


def v_gaza(d, x0, y0, w=112, h=88):
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=TAN)
    strip = [(16, 22), (92, 14), (96, 32), (34, 46), (22, 64), (12, 42)]
    strip = [(x0 + px, y0 + py) for px, py in strip]
    d.polygon(strip, fill=(255, 255, 255), outline=NAVY)
    for dx, dy in ((34, 26), (52, 22), (70, 20), (44, 36), (62, 32), (28, 50)):
        d.ellipse([x0 + dx - 3, y0 + dy - 3, x0 + dx + 3, y0 + dy + 3],
                  fill=(178, 34, 34))
    d.text((x0 + 6, y0 + 4), "GAZA", font=sans_b(9), fill=(255, 255, 255))
    d.text((x0 + 6, y0 + h - 26), "6 killed", font=sans_b(10),
           fill=(255, 255, 255))
    d.text((x0 + 6, y0 + h - 14), "1,600+ since truce", font=sans_b(8),
           fill=(255, 255, 255))


VISUALS = {
    "candles": v_candles,
    "seismo": v_seismo,
    "flags_uk": v_flags_uk,
    "flags_id": v_flags_id,
    "cop": v_cop,
    "poland": v_poland,
    "cyclone": v_cyclone,
    "cricket": v_cricket,
    "riyadh": v_riyadh,
    "gaza": v_gaza,
}

# ---------------------------------------------------------------- story data
# (kicker, headline, summary, source, visual) — transcribed from the image.
DRAWN = [
    ("AMERICAS • MARKETS",
     "Wall Street plunges as AI sell-off deepens",
     "S&P 500 −3.70% to 6,910.39, Nasdaq −5.28% to 22,617.73. Nvidia fell 14% "
     "amid an accounting probe; a seventh straight S&P loss.",
     "AP; Reuters; Fox Business", "candles"),
    ("AMERICAS • DISASTER",
     "Peru shaken by magnitude 6.8 earthquake",
     "A deep quake in Junín sent Lima residents into the streets. No casualties "
     "or major damage reported yet; USGS put it at 6.7.",
     "Reuters; AP; GFZ", "seismo"),
    ("EUROPE • TRADE",
     "UK and EU seal landmark post-Brexit package",
     "Food trade eased, carbon markets linked, youth scheme of 100,000 visas a "
     "year. Burnham claims £17bn a year; a tuition-fee row clouds rollout.",
     "PA/LBC; Brussels Times; UK Gov", "flags_uk"),
    ("ASIA-PACIFIC • TRADE",
     "Indonesia and EU set to sign landmark trade deal",
     "Due for signing in Brussels today after a decade of talks: up to 98.5% of "
     "tariff lines liberalised, ~€600m a year saved; start targeted for early 2027.",
     "ANTARA; Reuters; EU Council", "flags_id"),
    ("GLOBAL • CLIMATE",
     "COP31 runs into overtime in Antalya",
     "Nearly 200 nations argued past the deadline over a draft with no mention "
     "of fossil fuels. The EU warned it risked becoming a 'fossil summit'.",
     "The Guardian; Reuters; Al Jazeera", "cop"),
    ("EUROPE • SECURITY",
     "Missiles land in Poland; NATO chief heads to Warsaw",
     "A Kh-101 hit near Nowy Lipowiec; Warsaw says a second object was "
     "probably a missile, a third most likely a drone. Tusk: a provocation. "
     "Rutte arrives Saturday.",
     "Reuters; AFP; Kyiv Independent", "poland"),
    ("ASIA-PACIFIC • WEATHER",
     "Cyclone Akvan hits Odisha; ~300,000 evacuated",
     "Landfall near Gopalpur on Friday, then the storm weakened. Nearly 300,000 "
     "people had been moved to 2,523 relief camps; dozens of trains were cancelled.",
     "The Quint; India.com; Newsbytes", "cyclone"),
    ("SPORT • CRICKET",
     "Rahul completes his SENA set in Wellington",
     "Rahul's 13th Test hundred (207 balls), the first by an Indian opener in "
     "all SENA countries. India were 344/2 at tea, 24 behind.",
     "ESPNcricinfo; IANS; ANI", "cricket"),
    ("MIDDLE EAST • SECURITY",
     "Saudi defences down three Houthi missiles over Riyadh",
     "Three ballistic missiles aimed at the capital were destroyed early "
     "Saturday, days after a Houthi strike damaged the PIF tower.",
     "Reuters; AFP; Arab News", "riyadh"),
    ("MIDDLE EAST • GAZA",
     "Six killed in Gaza strikes despite the ceasefire",
     "Four died in an airstrike near Bureij, one in a drone strike in "
     "Deir al-Balah, one north of Nuseirat. AFP tally: 1,600+ killed since "
     "the truce.",
     "AFP; Al Jazeera", "gaza"),
]

# (headline, source) — column-major: 7 down column 1, 7 down column 2, 6 down 3.
BRIEFS = [
    ("Trump vows a 'tremendous tax' on US firms building AI data centres "
     "abroad; no rate or legal basis given", "AP; CTV News"),
    ("Virginia child dies of measles — the first US measles death of 2026; "
     "220 cases in the state", "ABC News; VDH"),
    ("Nasdaq 100 down 10.4%, worst since March 2020; S&P 500 down 8.6%, "
     "worst since April 2025; VIX 35.89", "CNBC; MarketWatch"),
    ("Poland to give the US access to missile debris; three impact sites "
     "under investigation", "AFP; Reuters"),
    ("Syria, Jordan, Iraq and Lebanon sign agriculture pact in Beirut to "
     "boost food security", "Arab News; Shafaq News"),
    ("Coalition strikes Houthi sites in Sanaa, Saada, Taiz and Hodeidah "
     "after the hit on Riyadh's PIF tower", "Arab News; Reuters"),
    ("Jaiswal's 85 and a 130-run opening stand set up India's reply to "
     "New Zealand's 368", "Sportskeeda; India.com"),
    ("Second judge blocks Trump's 250-ft arch: Brinkema's injunction "
     "open-ended, Chutkan's order runs to 3 Dec", "AP; Reuters"),
    ("Nvidia's worst week since Oct 2008, down 23%, after Huang's 12 Nov "
     "resignation and an accounting probe", "CNN; AP"),
    ("Arch plaintiffs include the Kennedy family and Vietnam veterans; "
     "planning panel approved it 8–4", "AP; Bloomberg"),
    ("UK–EU carbon-market link shields £6.5bn of British exports from the "
     "EU's carbon border tax", "PA/LBC"),
    ("Signal blocks screenshots by default to stop AI agents reading your "
     "chats", "Reuters; Engadget"),
    ("Israel says it completed a rare ground incursion in central Gaza a "
     "day before Friday's strikes", "AFP"),
    ("Foreign investors pour a record ₹1.22 lakh crore into Indian shares "
     "in November", "The Hindu BusinessLine; Reuters"),
    ("Palisades Fire: Rinderknecht convicted on two arson counts at "
     "retrial; sentencing 17 Mar 2027", "CBS LA; ABC7"),
    ("Anthropic's IPO fizzles: priced at $83, peaked at $115.10 on "
     "Thursday, closed Friday near $88.91", "Telegraph; SBS"),
    ("Denmark expels Russia's defence attaché over alleged plot to kill "
     "rapper Kyivstoner; two Danes held", "Al Jazeera; Copenhagen Post"),
    ("At COP31, Panama threatens to walk out as a dozen-plus countries "
     "demand a fossil-fuel transition", "Al Jazeera"),
    ("Iraqi forces enter Kataib Hezbollah's Jurf al-Sakhar stronghold "
     "under a deal; HQ opens Saturday", "Reuters; Al Jazeera"),
    ("Antonelli fastest in Las Vegas qualifying (1:33.893) but a grid "
     "penalty hands pole to Verstappen", "RacingNews365; PlanetF1"),
]

STATS = [
    ("−5.28%", "NASDAQ FALLS", RED),
    ("6.8", "PERU QUAKE", TAN),
    ("100,000", "UK–EU YOUTH VISAS / YR", PURPLE),
    ("~300,000", "EVACUATED, AKVAN", TEAL),
    ("250 ft", "TRUMP ARCH BLOCKED", STEEL),
    ("100", "RAHUL'S CENTURY", PINK),
]

REGIONS = [
    ("AMERICAS", 10, STEEL), ("EUROPE", 5, PURPLE), ("MIDDLE EAST", 6, TAN),
    ("ASIA-PACIFIC", 3, TEAL), ("SPORT", 3, PINK), ("GLOBAL", 3, GREEN),
]

KICKER_COLOURS = {
    "AMERICAS": STEEL, "EUROPE": PURPLE, "ASIA-PACIFIC": TEAL,
    "GLOBAL": GREEN, "SPORT": PINK, "MIDDLE EAST": TAN,
}

STRAP = ("Nasdaq's worst week since March 2020  •  Peru M6.8 quake  •  "
         "UK–EU deal sealed  •  Rahul completes SENA hundreds")

FOOTER_1 = ("Sources: AP • Reuters • AFP • Al Jazeera • The Guardian • Arab News "
            "• ANTARA • EU Council • ESPNcricinfo • IANS • ANI • Formula1.com "
            "• CBS/ABC • Kyiv Independent • LBC/PA • Brussels Times • The Quint "
            "• Telegraph • SBS")
FOOTER_2 = ("Facts checked against live reports as of 21 Nov 2026. Figures are "
            "provisional and may change as stories develop; casualty and market "
            "numbers follow the cited agencies.")


# ---------------------------------------------------------------- card drawing
def draw_card(d, x, y, w, h, kicker, headline, summary, source, visual):
    d.rounded_rectangle([x, y, x + w, y + h], radius=6, fill=PAPER,
                        outline=FAINT, width=1)
    vw = 112
    VISUALS[visual](d, x + 1, y + 1, vw, h - 2)
    d.line([x + vw + 2, y + 4, x + vw + 2, y + h - 4], fill=FAINT, width=1)
    tx = x + vw + 10
    tw = w - vw - 18
    cy = y + 7
    region = kicker.split(" • ")[0]
    kc = KICKER_COLOURS.get(region, STEEL)
    kw = text_w(d, kicker, sans_b(9)) + 14
    d.rounded_rectangle([tx, cy, tx + kw, cy + 16], radius=8, fill=kc)
    d.text((tx + 7, cy + 3), kicker, font=sans_b(9), fill=(255, 255, 255))
    cy += 22
    hf, hlines = fit_lines(d, headline, serif_b(15), tw, 2, 15,
                           "LiberationSerif-Bold.ttf")
    cy = draw_lines(d, hlines, tx, cy, hf, INK)
    cy += 1
    sf, slines = fit_lines(d, summary, sans(9), tw, 2, 9, "DejaVuSans.ttf")
    cy = draw_lines(d, slines, tx, cy, sf, (58, 58, 58))
    d.text((tx, y + h - 13), source, font=sans(9), fill=SRC)


def draw_brief(d, x, y, w, headline, source, bar, src_col):
    d.rectangle([x, y, x + 3, y + 26], fill=bar)
    hf, hlines = fit_lines(d, headline, sans_b(10), w - 10, 2, 10,
                           "DejaVuSans-Bold.ttf")
    y2 = draw_justified(d, hlines, x + 10, y, w - 10, hf, INK, leading=12)
    d.text((x + 10, y2), source, font=sans(8), fill=src_col)


# ---------------------------------------------------------------- page layout
def build():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)

    # ---- masthead (0..94)
    d.rectangle([0, 0, W, 94], fill=NAVY)
    for r in (34, 58, 84):
        d.ellipse([930 - r, 44 - r, 930 + r, 44 + r],
                  outline=(70, 76, 130), width=1)
    d.text((16, 10), "T H E   W O R L D   I N   O N E   D A Y",
           font=sans_b(11), fill=GOLD_LT)
    d.text((16, 28), "SATURDAY, 21 NOVEMBER 2026",
           font=serif_b(33), fill=(255, 255, 255))
    d.text((16, 68), "Thirty stories from a world that did not slow down",
           font=serif_i(12), fill=(190, 200, 220))
    d.rounded_rectangle([830, 12, 1006, 82], radius=10, fill=PAPER,
                        outline=GOLD, width=2)
    d.text((918 - text_w(d, "30", serif_b(30)) / 2, 18), "30",
           font=serif_b(30), fill=NAVY)
    d.text((918 - text_w(d, "10 TOP STORIES • 20 BRIEFS", sans_b(8)) / 2, 56),
           "10 TOP STORIES • 20 BRIEFS", font=sans_b(8), fill=NAVY)
    # thin multicolour bar under the masthead
    segs = [RED, PURPLE, TEAL, GREEN, PINK]
    bw = W / len(segs)
    for i, c in enumerate(segs):
        d.rectangle([i * bw, 94, (i + 1) * bw, 98], fill=c)

    # ---- TOP LINES strip (98..128)
    d.rectangle([0, 98, W, 128], fill=RED)
    d.rounded_rectangle([10, 106, 96, 122], radius=8, fill=PAPER)
    d.text((53 - text_w(d, "TOP LINES", sans_b(10)) / 2, 109), "TOP LINES",
           font=sans_b(10), fill=RED)
    d.text((106, 108), STRAP, font=sans_b(12), fill=(255, 255, 255))

    # ---- stat tiles (134..190)
    tw_, th = 160, 56
    for i, (num, label, col) in enumerate(STATS):
        x = 12 + i * (tw_ + 8)
        d.rounded_rectangle([x, 134, x + tw_, 134 + th], radius=8, fill=col)
        nf = serif_b(26)
        d.text((x + (tw_ - text_w(d, num, nf)) / 2, 140), num,
               font=nf, fill=(255, 255, 255))
        lf = sans_b(9)
        d.text((x + (tw_ - text_w(d, label, lf)) / 2, 170), label,
               font=lf, fill=(255, 255, 255))

    # ---- region chips (196..218)
    chips = ["%s %d" % (name, n) for name, n, _ in REGIONS]
    widths = [text_w(d, c, sans_b(10)) + 22 for c in chips]
    total = sum(widths) + 10 * (len(chips) - 1)
    cx = (W - total) / 2
    for (name, n, col), c, cw_ in zip(REGIONS, chips, widths):
        d.rounded_rectangle([cx, 196, cx + cw_, 218], radius=11, fill=col)
        d.text((cx + 11, 201), c, font=sans_b(10), fill=(255, 255, 255))
        cx += cw_ + 10

    # ---- ten drawn stories (226..698): 2 cols x 5 rows
    cw, ch, gx, gy = 492, 88, 8, 8
    for i, (kicker, headline, summary, source, visual) in enumerate(DRAWN):
        x = 10 + (i % 2) * (cw + gx)
        y = 226 + (i // 2) * (ch + gy)
        draw_card(d, x, y, cw, ch, kicker, headline, summary, source, visual)

    # ---- briefs header (704..726)
    d.rectangle([10, 704, 14, 722], fill=GOLD)
    d.text((22, 706), "ALSO TODAY — 20 MORE BRIEFS", font=sans_b(12), fill=NAVY)
    d.line([10, 726, W - 10, 726], fill=FAINT, width=1)

    # ---- briefs (732..972): 3 cols, column-major
    col_x = [10, 352, 694]
    col_w = 318
    bar_cols = [PINK, STEEL, TAN]
    src_cols = [(158, 84, 112), (74, 98, 132), (158, 98, 50)]
    for i, (headline, source) in enumerate(BRIEFS):
        col, row = i // 7, i % 7
        x = col_x[col]
        y = 732 + row * 34
        draw_brief(d, x, y, col_w, headline, source, bar_cols[col],
                   src_cols[col])

    # ---- footer (980..1024)
    d.rectangle([0, 978, W, 980], fill=GOLD)
    d.rectangle([0, 980, W, 1024], fill=NAVY)
    d.text((10, 986), FOOTER_1, font=sans(8), fill=(200, 208, 224))
    d.text((10, 1002), FOOTER_2, font=sans(8), fill=(200, 208, 224))
    return img


if __name__ == "__main__":
    build().save(OUT, format="PNG")
    print("wrote", OUT)
