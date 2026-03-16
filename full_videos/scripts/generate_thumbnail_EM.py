from pathlib import Path
import random
import re
import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageFilter

EXCEL_FILE = Path("data/EM_full_videos_pipeline.xlsx")
THUMB_FOLDER = Path("full_videos/thumbnails")
ASSET_FOLDER = Path("full_videos/assets")
BG_FOLDER = ASSET_FOLDER / "thumbnail_backgrounds"

MAX_ROWS = 1
SIZE = (1280, 720)

HIGHLIGHT_WORDS_YELLOW = {
    "DISCIPLINE", "FREEDOM", "SUCCESS", "MONEY", "POWER",
    "FOCUS", "WIN", "WINNERS", "GOALS", "HABITS", "CHANGE", "SILENCE"
}

HIGHLIGHT_WORDS_RED = {
    "STOP", "FAIL", "FEAR", "WARNING", "NEVER", "QUIT", "LOSS"
}

STOP_WORDS = {
    "a", "an", "the", "of", "to", "for", "in", "on", "at", "by", "with",
    "your", "you", "is", "are", "be", "this", "that", "it", "if", "what"
}

REWRITE_PATTERNS = [
    (r"talking about your goals", "STOP TALKING ABOUT GOALS"),
    (r"discipline creates freedom", "DISCIPLINE = FREEDOM"),
    (r"why most people fail", "WHY MOST PEOPLE FAIL"),
    (r"how to stay consistent", "STAY CONSISTENT"),
    (r"what if you never give up", "NEVER GIVE UP"),
    (r"how successful people think", "HOW WINNERS THINK"),
    (r"stop chasing motivation", "STOP CHASING MOTIVATION"),
    (r"small habits change your life", "SMALL HABITS CHANGE LIFE"),
    (r"why silence is power", "SILENCE IS POWER"),
]

def get_font(size: int, bold: bool = False):
    candidates = [
        "C:/Windows/Fonts/impact.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/georgiab.ttf",
        "C:/Windows/Fonts/georgia.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for fp in candidates:
        path = Path(fp)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except Exception:
                pass
    return ImageFont.load_default()

def get_badge_font(size: int):
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
        "C:/Windows/Fonts/verdanab.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for fp in candidates:
        path = Path(fp)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except Exception:
                pass
    return ImageFont.load_default()

def clean_text(text: str) -> str:
    text = str(text or "").strip()
    text = re.sub(r"\s+", " ", text)
    return text

def normalize_text(text: str) -> str:
    text = str(text or "").strip().lower()
    text = re.sub(r"[^\w\s&=!?'-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def safe_short_title(title: str) -> str:
    title = clean_text(title)
    replacements = {
        "Why ": "",
        "How ": "",
        "The ": "",
        " And ": " & ",
        "What If ": "",
        "This Is ": "",
    }
    for old, new in replacements.items():
        title = title.replace(old, new)
    return title.strip()

def apply_known_rewrites(text: str) -> str:
    t = normalize_text(text)
    for pattern, replacement in REWRITE_PATTERNS:
        if re.search(pattern, t):
            return replacement
    return ""

def extract_keywords(text: str, max_words: int = 5):
    words = normalize_text(text).split()
    cleaned = []
    for w in words:
        if w in STOP_WORDS:
            continue
        if len(w) <= 2:
            continue
        cleaned.append(w.upper())
    return cleaned[:max_words]

def make_question_variant(text: str) -> str:
    keywords = extract_keywords(text, max_words=4)
    if not keywords:
        return ""
    phrase = " ".join(keywords)
    if not phrase.endswith("?"):
        phrase += "?"
    return phrase

def make_command_variant(text: str) -> str:
    t = normalize_text(text)

    if "goal" in t:
        return "MOVE IN SILENCE"
    if "discipline" in t:
        return "BUILD DISCIPLINE"
    if "motivation" in t:
        return "STOP WAITING"
    if "habit" in t or "habits" in t:
        return "CHANGE YOUR HABITS"
    if "focus" in t:
        return "PROTECT YOUR FOCUS"
    if "success" in t:
        return "EARN YOUR SUCCESS"
    if "fear" in t:
        return "KILL THE FEAR"
    if "mindset" in t:
        return "FIX YOUR MINDSET"

    keywords = extract_keywords(text, max_words=3)
    if not keywords:
        return ""
    return " ".join(keywords)

def compress_text(text: str, max_words: int = 5) -> str:
    words = normalize_text(text).split()
    words = [w for w in words if w not in STOP_WORDS or w in {"why", "how", "stop", "never"}]

    if not words:
        return ""

    return " ".join(words[:max_words]).upper()

def smart_thumbnail_text(title: str, hook: str, prompt: str):
    sources = [hook, title, prompt]

    for src in sources:
        rewritten = apply_known_rewrites(src)
        if rewritten:
            primary = rewritten
            break
    else:
        primary = ""
        for src in sources:
            primary = compress_text(src, max_words=5)
            if primary:
                break

    secondary = ""
    for src in sources:
        secondary = make_command_variant(src)
        if secondary:
            break

    if not primary:
        primary = "WATCH THIS"
    if not secondary:
        secondary = make_question_variant(hook or title or prompt) or "THIS CHANGES EVERYTHING"

    primary = " ".join(primary.split()[:5]).upper()
    secondary = " ".join(secondary.split()[:5]).upper()

    return primary, secondary

def build_variant_texts(row):
    title = str(row.get("Title", "") or "").strip()
    prompt = str(row.get("Prompt", "") or "").strip()
    hook = str(row.get("Hook", "") or "").strip()

    a_text, b_text = smart_thumbnail_text(title, hook, prompt)

    if len(a_text) < 6:
        a_text = safe_short_title(title).upper() or "WATCH THIS"
    if len(b_text) < 6:
        b_text = "MOVE IN SILENCE"

    return a_text, b_text

def get_word_fill(word: str):
    clean = word.upper().strip(".,!?':;")
    if clean in HIGHLIGHT_WORDS_RED:
        return "#FF4D4D"
    if clean in HIGHLIGHT_WORDS_YELLOW:
        return "#FFD84D"
    return "white"

def create_gradient_overlay(size, top_alpha=25, bottom_alpha=170):
    w, h = size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = overlay.load()

    for y in range(h):
        alpha = int(top_alpha + (bottom_alpha - top_alpha) * (y / max(h - 1, 1)))
        for x in range(w):
            px[x, y] = (0, 0, 0, alpha)

    return overlay

def add_vignette(base_img: Image.Image, strength=110):
    w, h = base_img.size
    vignette = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(vignette)

    for i in range(8):
        margin = i * 35
        alpha = int(strength * (i + 1) / 8)
        draw.rounded_rectangle(
            [margin, margin, w - margin, h - margin],
            radius=90,
            outline=alpha,
            width=35
        )

    vignette = vignette.filter(ImageFilter.GaussianBlur(70))

    black = Image.new("RGBA", (w, h), (0, 0, 0, 180))
    dark_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dark_layer.paste(black, (0, 0), vignette)

    base_img.alpha_composite(dark_layer)

def pick_background():
    if BG_FOLDER.exists():
        files = []
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
            files.extend(BG_FOLDER.glob(ext))
        if files:
            return random.choice(files)
    return None

def build_background():
    w, h = SIZE
    bg_path = pick_background()

    if bg_path and bg_path.exists():
        img = Image.open(bg_path).convert("RGB")
        img = img.resize((w, h), Image.Resampling.LANCZOS)
    else:
        img = Image.new("RGB", (w, h), (18, 20, 28))
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, w, h], fill=(22, 26, 38))
        draw.ellipse([-200, -100, 500, 450], fill=(170, 120, 25))
        draw.ellipse([800, 250, 1450, 900], fill=(145, 20, 20))
        img = img.filter(ImageFilter.GaussianBlur(40))

    img = img.filter(ImageFilter.GaussianBlur(1))
    img = img.convert("RGBA")

    gradient = create_gradient_overlay((w, h), top_alpha=25, bottom_alpha=170)
    img.alpha_composite(gradient)

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.rounded_rectangle(
        [40, 90, w - 40, h - 90],
        radius=34,
        fill=(0, 0, 0, 95)
    )
    d.rounded_rectangle(
        [52, 102, w - 52, h - 102],
        radius=30,
        outline=(255, 255, 255, 150),
        width=3
    )
    img.alpha_composite(overlay)

    add_vignette(img)

    return img.convert("RGB")

def wrap_text(draw, text, font, max_width, stroke_width=4):
    words = clean_text(text).split()
    lines = []
    current = ""

    for word in words:
        test = word if not current else f"{current} {word}"
        bbox = draw.textbbox((0, 0), test, font=font, stroke_width=stroke_width)
        width = bbox[2] - bbox[0]
        if width <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines

def fit_text(draw, text, max_width, max_lines=4, start_size=92, min_size=42, stroke_width=5):
    for size in range(start_size, min_size - 1, -2):
        font = get_font(size, bold=True)
        lines = wrap_text(draw, text, font, max_width, stroke_width=stroke_width)
        if len(lines) <= max_lines:
            return font, lines
    font = get_font(min_size, bold=True)
    lines = wrap_text(draw, text, font, max_width, stroke_width=stroke_width)[:max_lines]
    return font, lines

def draw_text_with_shadow(draw, pos, text, font, fill, stroke_width=5, stroke_fill="black"):
    x, y = pos
    shadow_offsets = [(4, 4), (2, 2)]
    for dx, dy in shadow_offsets:
        draw.text(
            (x + dx, y + dy),
            text,
            font=font,
            fill=(0, 0, 0),
            stroke_width=stroke_width,
            stroke_fill=(0, 0, 0),
        )
    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill,
        stroke_width=stroke_width,
        stroke_fill=stroke_fill,
    )

def draw_centered_highlighted_lines(draw, lines, font, canvas_width, start_y, line_spacing=10, stroke_width=5):
    current_y = start_y

    for line in lines:
        words = line.split()
        total_width = 0
        token_widths = []

        for idx, word in enumerate(words):
            token = word + (" " if idx < len(words) - 1 else "")
            bbox = draw.textbbox((0, 0), token, font=font, stroke_width=stroke_width)
            token_w = bbox[2] - bbox[0]
            token_widths.append(token_w)
            total_width += token_w

        line_bbox = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_width)
        line_h = line_bbox[3] - line_bbox[1]

        start_x = (canvas_width - total_width) / 2
        cursor_x = start_x

        for idx, word in enumerate(words):
            token = word + (" " if idx < len(words) - 1 else "")
            fill = get_word_fill(word)

            draw_text_with_shadow(
                draw,
                (cursor_x, current_y),
                token,
                font,
                fill,
                stroke_width=stroke_width
            )
            cursor_x += token_widths[idx]

        current_y += line_h + line_spacing

def draw_spaced_text(draw, x, y, text, font, fill, spacing=2):
    cursor_x = x
    for ch in text:
        draw.text((cursor_x, y), ch, font=font, fill=fill)
        bbox = draw.textbbox((0, 0), ch, font=font)
        ch_w = bbox[2] - bbox[0]
        cursor_x += ch_w + spacing

def draw_badge(draw, text, x, y, fill=(220, 30, 30), text_fill="white"):
    font = get_badge_font(34)
    spacing = 2
    total_text_width = 0
    max_text_height = 0

    for ch in text:
        bbox = draw.textbbox((0, 0), ch, font=font)
        ch_w = bbox[2] - bbox[0]
        ch_h = bbox[3] - bbox[1]
        total_text_width += ch_w + spacing
        max_text_height = max(max_text_height, ch_h)

    if text:
        total_text_width -= spacing

    pad_x = 26
    pad_y = 14

    box_x1 = x
    box_y1 = y
    box_x2 = x + total_text_width + pad_x * 2
    box_y2 = y + max_text_height + pad_y * 2

    draw.rounded_rectangle(
        [box_x1, box_y1, box_x2, box_y2],
        radius=28,
        fill=fill
    )

    text_x = x + pad_x
    text_y = y + pad_y - 1

    draw_spaced_text(draw, text_x, text_y, text, font=font, fill=text_fill, spacing=spacing)

def add_logo(img: Image.Image):
    logo_path = ASSET_FOLDER / "logo.png"
    if not logo_path.exists():
        return img

    try:
        logo = Image.open(logo_path).convert("RGBA")
        logo.thumbnail((170, 170))

        margin = 28
        x = img.width - logo.width - margin
        y = img.height - logo.height - margin

        plate = Image.new("RGBA", img.size, (0, 0, 0, 0))
        pd = ImageDraw.Draw(plate)
        pd.rounded_rectangle(
            [x - 10, y - 10, x + logo.width + 10, y + logo.height + 10],
            radius=18,
            fill=(0, 0, 0, 120)
        )

        img = img.convert("RGBA")
        img.alpha_composite(plate)
        img.paste(logo, (x, y), logo)

        return img.convert("RGB")
    except Exception:
        return img

def add_bottom_tag(draw, text, img_w, img_h):
    font = get_font(26, bold=True)
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=2)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    x = 30
    y = img_h - th - 44
    pad_x = 18
    pad_y = 10

    draw.rounded_rectangle(
        [x - pad_x, y - pad_y, x + tw + pad_x, y + th + pad_y],
        radius=18,
        fill=(0, 0, 0)
    )
    draw.text(
        (x, y),
        text,
        font=font,
        fill="white",
        stroke_width=2,
        stroke_fill="black"
    )

def create_thumbnail_a(row, output_path: Path):
    w, h = SIZE
    img = build_background()
    draw = ImageDraw.Draw(img)

    title_a, _ = build_variant_texts(row)

    max_text_width = w - 140

    font_big, lines = fit_text(
        draw,
        title_a,
        max_width=max_text_width,
        max_lines=3,
        start_size=112,
        min_size=56
    )

    draw_centered_highlighted_lines(
        draw,
        lines,
        font_big,
        canvas_width=w,
        start_y=145,
        line_spacing=8,
        stroke_width=5
    )

    draw_badge(draw, "FULL VIDEO", 60, 40, fill=(220, 30, 30), text_fill="white")

    brand_font = get_font(34, bold=True)
    brand_text = "UNLOCK YOUR POTENTIAL"
    bb = draw.textbbox((0, 0), brand_text, font=brand_font, stroke_width=3)
    bw = bb[2] - bb[0]
    bx = (w - bw) / 2
    draw_text_with_shadow(draw, (bx, 590), brand_text, brand_font, "#FFD84D", stroke_width=3)

    img = add_logo(img)
    draw = ImageDraw.Draw(img)
    add_bottom_tag(draw, "MOTIVATION", w, h)

    img.save(output_path, quality=95)

def create_thumbnail_b(row, output_path: Path):
    w, h = SIZE
    img = build_background()
    draw = ImageDraw.Draw(img)

    _, title_b = build_variant_texts(row)

    max_text_width = w - 140

    font_big, lines = fit_text(
        draw,
        title_b,
        max_width=max_text_width,
        max_lines=3,
        start_size=110,
        min_size=54
    )

    draw_centered_highlighted_lines(
        draw,
        lines,
        font_big,
        canvas_width=w,
        start_y=150,
        line_spacing=8,
        stroke_width=5
    )

    draw_badge(draw, "WATCH THIS", 60, 40, fill=(255, 196, 0), text_fill="black")

    urgency_font = get_font(30, bold=True)
    urgency_text = "KEEP IT PRIVATE. PROVE IT LATER."
    ub = draw.textbbox((0, 0), urgency_text, font=urgency_font, stroke_width=3)
    uw = ub[2] - ub[0]
    ux = (w - uw) / 2
    draw_text_with_shadow(draw, (ux, 585), urgency_text, urgency_font, "#FFD84D", stroke_width=3)

    img = add_logo(img)
    draw = ImageDraw.Draw(img)
    add_bottom_tag(draw, "A/B TEST", w, h)

    img.save(output_path, quality=95)

def main():
    df = pd.read_excel(EXCEL_FILE)
    print("Thumbnail script started")
    print(f"Rows in file: {len(df)}")

    for col in ["Thumbnail File", "Status", "Title", "Prompt", "Hook"]:
        if col in df.columns:
            df[col] = df[col].astype("object")

    THUMB_FOLDER.mkdir(parents=True, exist_ok=True)

    processed = 0
    success = 0
    failed = 0

    for i, row in df.iterrows():
        status = clean_text(row.get("Status", "")).lower()
        print(f"Row {i+2} | Status = '{status}'")

        if status != "video_done":
            continue

        if processed >= MAX_ROWS:
            break

        print(f"Processing row {i+2}...")

        try:
            video_id = int(row.get("ID"))
            thumb_a = THUMB_FOLDER / f"full_video_{video_id:03d}_A.png"
            thumb_b = THUMB_FOLDER / f"full_video_{video_id:03d}_B.png"

            create_thumbnail_a(row, thumb_a)
            create_thumbnail_b(row, thumb_b)

            df.at[i, "Thumbnail File"] = f"{thumb_a} | {thumb_b}"
            df.at[i, "Status"] = "thumbnail_done"

            success += 1
            processed += 1
            print(f"Saved thumbnails: {thumb_a.name}, {thumb_b.name}")

        except Exception as e:
            failed += 1
            processed += 1
            print(f"Error row {i+2}: {e}")

    df.to_excel(EXCEL_FILE, index=False)

    print("\nThumbnail generation complete")
    print(f"Processed: {processed}")
    print(f"Success:   {success}")
    print(f"Failed:    {failed}")

if __name__ == "__main__":
    main()