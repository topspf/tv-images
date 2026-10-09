"""Compose the 1920x1080 TV frame: Kotel-style stone wall, schedule at 80%, dark bands for header/clock."""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1920, 1080
TOP, BOTTOM = 190, 150  # header band, clock band
SCALE = 0.8

sched_path, out_path = sys.argv[1], sys.argv[2]
bg_path = sys.argv[3] if len(sys.argv) > 3 else None
rng = np.random.default_rng(7)


def stone_wall():
    # Large Herodian-style limestone ashlars with margins, warm Jerusalem-stone palette.
    img = np.zeros((H, W, 3), np.float32)
    base = np.array([226, 204, 168], np.float32)
    row_h = 135
    y = -40
    r = 0
    while y < H:
        x = -rng.integers(0, 300)
        while x < W:
            w = int(rng.integers(260, 520))
            tint = base * rng.uniform(0.86, 1.06) * np.array([1.0, rng.uniform(0.97, 1.0), rng.uniform(0.9, 0.98)], np.float32)
            x0, x1, y0, y1 = max(x, 0), min(x + w, W), max(y, 0), min(y + row_h, H)
            if x1 > x0 and y1 > y0:
                img[y0:y1, x0:x1] = tint
                # chiselled margin: slightly darker border inside each block
                m = 14
                img[y0:min(y0 + m, y1), x0:x1] *= 0.93
                img[max(y1 - m, y0):y1, x0:x1] *= 0.9
                img[y0:y1, x0:min(x0 + m, x1)] *= 0.93
                img[y0:y1, max(x1 - m, x0):x1] *= 0.9
                # mortar joint
                img[max(y1 - 3, y0):y1, x0:x1] = base * 0.45
                img[y0:y1, max(x1 - 3, x0):x1] = base * 0.45
            x += w
        y += row_h
        r += 1
    noise = rng.normal(0, 9, (H, W, 1)).astype(np.float32)
    coarse = np.array(Image.fromarray(rng.normal(128, 40, (H // 16, W // 16)).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32)[..., None]
    img = img + noise + (coarse - 128) * 0.25
    # warm evening light, darker toward the top
    grad = np.linspace(0.78, 1.0, H, dtype=np.float32)[:, None, None]
    img *= grad
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))


if bg_path:
    bg = Image.open(bg_path).convert("RGB")
    s = max(W / bg.width, H / bg.height)
    bg = bg.resize((round(bg.width * s), round(bg.height * s)), Image.LANCZOS)
    l, t = (bg.width - W) // 2, (bg.height - H) // 2
    frame = bg.crop((l, t, l + W, t + H))
else:
    frame = stone_wall()

frame = frame.convert("RGBA")
# dark translucent bands so white header/clock text stays readable
bands = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(bands)
d.rectangle([0, 0, W, TOP], fill=(20, 16, 10, 150))
d.rectangle([0, H - BOTTOM, W, H], fill=(20, 16, 10, 150))
frame = Image.alpha_composite(frame, bands)

sched = Image.open(sched_path).convert("RGBA")
sw, sh = round(sched.width * SCALE), round(sched.height * SCALE)
avail = H - TOP - BOTTOM
if sh > avail:
    k = avail / sh
    sw, sh = round(sw * k), round(sh * k)
sched = sched.resize((sw, sh), Image.LANCZOS)
x, y = (W - sw) // 2, TOP + (avail - sh) // 2

shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(shadow).rectangle([x + 6, y + 10, x + sw + 6, y + sh + 10], fill=(0, 0, 0, 170))
frame = Image.alpha_composite(frame, shadow.filter(ImageFilter.GaussianBlur(14)))
frame.alpha_composite(sched, (x, y))
frame.convert("RGB").save(out_path, optimize=True)
print(out_path, (x, y, sw, sh))
