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

# ── Draw orange paper plane (upper-right, ~30° launch angle) ─────────────────
import math

draw = ImageDraw.Draw(result, "RGBA")

# Plane origin (nose tip) — upper-right quadrant
px, py = int(W * 0.835), int(H * 0.295)

# Scale and rotation: plane flies toward upper-right at ~30° above horizontal
angle_deg = -32   # negative = tilted upward-right
angle = math.radians(angle_deg)
cos_a, sin_a = math.cos(angle), math.sin(angle)
scale = 110  # overall size

def rot(x, y):
    """Rotate point (x,y) around origin then offset to plane position."""
    rx = x * cos_a - y * sin_a
    ry = x * sin_a + y * cos_a
    return (px + rx, py + ry)

# ── Plane surface colors ──
orange_main  = (249, 115, 22, 255)   # #F97316
orange_dark  = (200,  80,  8, 255)   # shadow face
orange_mid   = (235, 100, 14, 255)   # mid tone
orange_light = (255, 165, 70, 255)   # highlight edge

# Geometry (in local coords, nose at origin, body extends left)
# The plane is roughly: nose → body → tail, with upper + lower wings

# --- Top wing (upper panel, lit face) ---
top_wing = [
    rot(  scale,        0),           # nose tip
    rot( -scale * 0.05, -scale * 0.52),  # top wing peak
    rot( -scale * 0.80, -scale * 0.08),  # tail top
    rot( -scale * 0.60,  scale * 0.05),  # body spine
]
draw.polygon(top_wing, fill=orange_light)

# --- Bottom wing (lower panel, shadow face) ---
bot_wing = [
    rot(  scale,        0),           # nose tip
    rot( -scale * 0.60,  scale * 0.05),  # body spine
    rot( -scale * 0.80,  scale * 0.18),  # tail bottom
    rot( -scale * 0.05,  scale * 0.30),  # bottom wing tip
]
draw.polygon(bot_wing, fill=orange_dark)

# --- Centre body spine (narrow bright crease) ---
spine = [
    rot(  scale,        0),
    rot(  scale - 4,    2),
    rot( -scale * 0.80 - 2,  scale * 0.12),
    rot( -scale * 0.80,      scale * 0.18),
    rot( -scale * 0.60,      scale * 0.05),
]
draw.polygon(spine, fill=orange_mid)

# --- Fold crease on top wing ---
crease_top = [
    rot(  scale * 0.9,   0),
    rot(  scale * 0.85, -2),
    rot( -scale * 0.55, -scale * 0.44),
    rot( -scale * 0.60, -scale * 0.40),
]
draw.polygon(crease_top, fill=orange_mid)

# --- Thin highlight along top leading edge ---
draw.line([rot(scale, 0), rot(-scale * 0.05, -scale * 0.52)],
          fill=(255, 200, 120, 200), width=2)

# ── Long cast shadow on the surface below the plane ──────────────────────────
# The shadow is a soft dark trapezoid sweeping lower-left from the plane
shadow_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sdraw = ImageDraw.Draw(shadow_layer)

# Shadow tip starts just below the plane, sweeps far lower-left
sh_tip_x, sh_tip_y = px - int(scale * 0.2 * cos_a), py + int(scale * 0.2 * abs(sin_a)) + 20
sh_far_x = int(W * 0.09)
sh_far_y = int(H * 0.88)

# Width of shadow: narrow at plane, wide at far end
perp_dx, perp_dy = sin_a, -cos_a   # perpendicular to flight direction
half_near, half_far = 12, 85

sh_poly = [
    (sh_tip_x + perp_dx * half_near, sh_tip_y + perp_dy * half_near),
    (sh_tip_x - perp_dx * half_near, sh_tip_y - perp_dy * half_near),
    (sh_far_x - perp_dy * half_far,  sh_far_y + perp_dx * half_far),
    (sh_far_x + perp_dy * half_far,  sh_far_y - perp_dx * half_far),
]
sdraw.polygon(sh_poly, fill=(0, 0, 0, 110))
# Blur the shadow for soft edge
shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=18))
result = Image.alpha_composite(result.convert("RGBA"), shadow_layer).convert("RGB")

result.save("background.jpg", quality=92, optimize=True)
print(f"Saved background.jpg  ({W}x{H})")
