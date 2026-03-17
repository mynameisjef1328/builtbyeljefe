#!/usr/bin/env python3
"""Generate a dark slate/charcoal textured background with dramatic radial light bloom."""

from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import random

W, H = 1920, 1080

rng = random.Random(42)

# ── Base dark slate ──────────────────────────────────────────────────────────
img = Image.new("RGB", (W, H), (26, 26, 26))
base = np.array(img, dtype=np.float32)

# ── Stone/concrete noise texture ─────────────────────────────────────────────
np.random.seed(42)

# Multi-octave noise for concrete look
noise = np.zeros((H, W), dtype=np.float32)
for scale, amp in [(8, 18), (16, 12), (32, 8), (64, 5), (128, 3)]:
    h_cells = H // scale + 2
    w_cells = W // scale + 2
    cell = np.random.uniform(-1, 1, (h_cells, w_cells)).astype(np.float32)
    # Upsample with PIL for smooth interpolation
    cell_img = Image.fromarray(((cell + 1) * 127.5).astype(np.uint8))
    cell_img = cell_img.resize((W, H), Image.BILINEAR)
    layer = (np.array(cell_img, dtype=np.float32) / 127.5 - 1.0) * amp
    noise += layer

# Apply noise to base (subtle — just enough for texture)
base[:, :, 0] = np.clip(base[:, :, 0] + noise, 10, 55)
base[:, :, 1] = np.clip(base[:, :, 1] + noise * 0.95, 10, 52)
base[:, :, 2] = np.clip(base[:, :, 2] + noise * 0.9, 10, 50)

# ── Radial light bloom — upper-right quadrant ─────────────────────────────────
# Light source at roughly 78% x, 10% y (upper-right)
cx = int(W * 0.78)
cy = int(H * 0.10)

yy, xx = np.mgrid[0:H, 0:W]
dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2).astype(np.float32)

# Bloom radius — spread wide for dramatic cinematic feel
bloom_radius = W * 0.72

# Soft falloff: bright core, gentle fade
bloom = np.clip(1.0 - dist / bloom_radius, 0, 1) ** 1.6
bloom = bloom * 185  # peak brightness boost

# Warm-white light tint (slightly warm)
base[:, :, 0] = np.clip(base[:, :, 0] + bloom * 1.05, 0, 255)
base[:, :, 1] = np.clip(base[:, :, 1] + bloom * 1.0,  0, 255)
base[:, :, 2] = np.clip(base[:, :, 2] + bloom * 0.88, 0, 255)

# ── Directional shadow sweep — diagonal lower-half ───────────────────────────
# Shadow sweeps from upper-right to lower-left across the lower portion
# Simulate the long cast shadow of the paper plane launch

# Shadow gradient along a diagonal axis
# Direction vector: upper-right → lower-left  (normalized ~135°)
dx, dy = -0.707, 0.707

# Project each pixel onto shadow axis (origin at right edge, mid-height)
ox, oy = W * 0.85, H * 0.25
proj = (xx - ox) * dx + (yy - oy) * dy  # positive = into shadow

# Shadow starts around centre and deepens toward lower-left
shadow_start = 0
shadow_end = W * 0.9
shadow_t = np.clip((proj - shadow_start) / shadow_end, 0, 1)

# S-curve for smooth shadow edge
shadow_mask = shadow_t ** 1.4 * 0.72  # max 72% darkening

base[:, :, 0] = np.clip(base[:, :, 0] * (1 - shadow_mask), 0, 255)
base[:, :, 1] = np.clip(base[:, :, 1] * (1 - shadow_mask), 0, 255)
base[:, :, 2] = np.clip(base[:, :, 2] * (1 - shadow_mask), 0, 255)

# ── Subtle vignette ───────────────────────────────────────────────────────────
dist_centre = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
vignette = np.clip(dist_centre * 0.35, 0, 0.5)
base[:, :, 0] = np.clip(base[:, :, 0] * (1 - vignette), 0, 255)
base[:, :, 1] = np.clip(base[:, :, 1] * (1 - vignette), 0, 255)
base[:, :, 2] = np.clip(base[:, :, 2] * (1 - vignette), 0, 255)

# ── Convert and apply mild blur to soften noise seams ─────────────────────────
result = Image.fromarray(base.astype(np.uint8), "RGB")
result = result.filter(ImageFilter.GaussianBlur(radius=0.8))

result.save("background.jpg", quality=92, optimize=True)
print(f"Saved background.jpg  ({W}x{H})")
