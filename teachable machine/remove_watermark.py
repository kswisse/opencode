from PIL import Image
import numpy as np

SRC = "player.png"
DST = "player_clean.png"

PAL = [
    (35, 24, 21),     # hair / outline
    (16, 101, 178),   # blue shirt
    (249, 189, 0),    # yellow
    (255, 217, 202),  # skin
    (242, 143, 12),   # orange
    (255, 228, 215),  # light skin shade
    (255, 255, 255),  # eye whites
]
WS = [0.0, 255.0]           # watermark ink colors
TOL = 14.0                  # residual tolerance
A_MIN, A_MAX = 0.05, 0.45   # plausible watermark alpha range

im = Image.open(SRC).convert("RGB")
arr = np.asarray(im).astype(np.float32)
H, Wd, _ = arr.shape

best_res = np.full((H, Wd), np.inf, np.float32)
best_a = np.zeros((H, Wd), np.float32)
best_base = arr.copy()

for c in PAL:
    c = np.array(c, np.float32)
    for Wv in WS:
        d = Wv - c
        denom = float(d @ d)
        if denom == 0:
            continue
        diff = arr - c
        a = np.clip((diff @ d) / denom, 0.0, A_MAX)
        recon = c[None, None, :] + a[:, :, None] * d[None, None, :]
        res = np.linalg.norm(arr - recon, axis=2)
        better = res < best_res
        best_res = np.where(better, res, best_res)
        best_a = np.where(better, a, best_a)
        best_base = np.where(better[:, :, None], np.broadcast_to(c, arr.shape), best_base)

watermarked = (best_res < TOL) & (best_a > A_MIN)
out = np.where(watermarked[:, :, None], best_base, arr)

print("watermarked px:", int(watermarked.sum()), "/", H * Wd)

# --- background removal: flood fill from border, de-watermarked grays near 255/235 ---
def is_bg(a):
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    gray = (np.abs(r - g) < 8) & (np.abs(g - b) < 8)
    near_white = (r > 246) | (np.abs(r - 235) < 6)
    return gray & near_white

# de-watermark first for bg test too (watermark on bg handled above since 255/235 in palette)
mask = is_bg(out)
# flood fill from borders
from collections import deque
bg = np.zeros((H, Wd), bool)
q = deque()
for x in range(Wd):
    for y in (0, H - 1):
        if mask[y, x] and not bg[y, x]:
            bg[y, x] = True; q.append((y, x))
for y in range(H):
    for x in (0, Wd - 1):
        if mask[y, x] and not bg[y, x]:
            bg[y, x] = True; q.append((y, x))
while q:
    y, x = q.popleft()
    for ny, nx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
        if 0 <= ny < H and 0 <= nx < Wd and mask[ny, nx] and not bg[ny, nx]:
            bg[ny, nx] = True; q.append((ny, nx))
print("bg px:", int(bg.sum()))

# halo cleanup: light desaturated pixels adjacent to bg
halo = out.copy()
for _ in range(3):
    nb = np.zeros_like(bg)
    nb[1:, :] |= bg[:-1, :]; nb[:-1, :] |= bg[1:, :]
    nb[:, 1:] |= bg[:, :-1]; nb[:, :-1] |= bg[:, 1:]
    ring = nb & ~bg
    r, g, b = halo[:, :, 0], halo[:, :, 1], halo[:, :, 2]
    light_gray = (r > 180) & (np.abs(r - g) < 14) & (np.abs(g - b) < 14)
    newbg = ring & light_gray
    if not newbg.any():
        break
    bg |= newbg
print("bg after halo:", int(bg.sum()))

rgba = np.dstack([out.astype(np.uint8), np.where(bg, 0, 255).astype(np.uint8)])
Image.fromarray(rgba, "RGBA").save(DST)
print("saved", DST)
