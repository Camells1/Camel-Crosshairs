"""Distinct animated backdrops per theme, echoing Camel Launcher's biome
scenes (stars, embers, bubbles, vines, planets) without needing SVG/CSS."""
import math
import random

import theme


def _star_points(cx, cy, r_outer, r_inner):
    """8 alternating-radius points -> a classic 4-point sparkle/star shape."""
    pts = []
    for i in range(8):
        angle = math.pi / 4 * i - math.pi / 2
        r = r_outer if i % 2 == 0 else r_inner
        pts.extend([cx + r * math.cos(angle), cy + r * math.sin(angle)])
    return pts


def _spawn_dust(width, height, n=10):
    """Desert: slow drifting dust motes, no twinkle — reads as heat haze."""
    particles = []
    for _ in range(n):
        particles.append({
            "type": "drift", "r": random.randint(1, 2),
            "x": random.uniform(0, width), "y": random.uniform(0, height),
            "dx": random.uniform(0.03, 0.09), "dy": random.uniform(-0.02, 0.02),
            "color": theme.ACCENT_HI,
        })
    return particles


def _spawn_stars(width, height, n=18):
    """Starburst: small sparkle glyphs (cross shape), not plain dots."""
    particles = []
    for _ in range(n):
        particles.append({
            "type": "sparkle", "r": random.randint(2, 4),
            "x": random.uniform(0, width), "y": random.uniform(0, height),
            "phase": random.uniform(0, 6.28), "speed": random.uniform(0.05, 0.12),
            "color": theme.ACCENT_HI,
        })
    return particles


def _spawn_bubbles(width, height, n=14, outline=False):
    """Volcano / Ocean: rising bubbles — filled embers or outlined water bubbles."""
    particles = []
    for _ in range(n):
        particles.append({
            "type": "rise", "r": random.randint(2, 4),
            "x": random.uniform(0, width), "y": random.uniform(0, height),
            "speed": random.uniform(0.2, 0.55), "wobble": random.uniform(0, 6.28),
            "color": theme.ACCENT_HI if outline else theme.ACCENT,
            "outline": outline,
        })
    return particles


def _spawn_vines(width, height, n=3):
    """Jungle: a few vines hanging from the top, gently swaying."""
    particles = []
    spacing = width / max(1, n + 1)
    for i in range(n):
        x = spacing * (i + 1)
        length = random.randint(int(height * 0.5), int(height * 0.85))
        particles.append({
            "type": "vine", "x": x, "length": length,
            "phase": random.uniform(0, 6.28), "speed": random.uniform(0.02, 0.04),
            "color": theme.ACCENT, "leaf_color": theme.ACCENT_HI,
        })
    return particles


def _spawn_planets(width, height, n=3):
    """Space: a few small ringed planets drifting, plus a light starfield."""
    particles = []
    for _ in range(n):
        particles.append({
            "type": "planet", "r": random.randint(4, 7),
            "x": random.uniform(0, width), "y": random.uniform(0, height * 0.8),
            "dx": random.uniform(-0.04, 0.04), "dy": random.uniform(-0.015, 0.015),
            "color": theme.ACCENT_HI,
        })
    for _ in range(10):
        particles.append({
            "type": "sparkle", "r": random.randint(1, 2),
            "x": random.uniform(0, width), "y": random.uniform(0, height),
            "phase": random.uniform(0, 6.28), "speed": random.uniform(0.04, 0.09),
            "color": theme.FG_MUTED,
        })
    return particles


def _particles_for(accent_name, width, height):
    if accent_name == "starburst":
        return _spawn_stars(width, height)
    if accent_name == "clay":
        return _spawn_bubbles(width, height, outline=False)
    if accent_name == "azure":
        return _spawn_bubbles(width, height, outline=True)
    if accent_name == "oasis":
        return _spawn_vines(width, height)
    if accent_name == "mauve":
        return _spawn_planets(width, height)
    return _spawn_dust(width, height)  # desert


def _draw(canvas, p):
    if p["type"] == "vine":
        p["item"] = canvas.create_line(p["x"], 0, p["x"], p["length"], fill=p["color"], width=2, smooth=True)
        leaf_ys = [p["length"] * f for f in (0.3, 0.6, 0.9)]
        p["leaf_items"] = [
            canvas.create_oval(p["x"] - 3, y - 3, p["x"] + 3, y + 3, fill=p["leaf_color"], outline="")
            for y in leaf_ys
        ]
        p["leaf_frac"] = (0.3, 0.6, 0.9)
        return
    r = p["r"]
    if p["type"] == "sparkle":
        p["item"] = canvas.create_polygon(
            _star_points(p["x"], p["y"], r * 2, r * 0.7), fill=p["color"], outline="",
        )
        return
    if p.get("outline"):
        item = canvas.create_oval(p["x"] - r, p["y"] - r, p["x"] + r, p["y"] + r, outline=p["color"], fill="")
    else:
        item = canvas.create_oval(p["x"] - r, p["y"] - r, p["x"] + r, p["y"] + r, fill=p["color"], outline="")
    p["item"] = item
    if p["type"] == "planet":
        ring = canvas.create_oval(p["x"] - r * 1.9, p["y"] - r * 0.6, p["x"] + r * 1.9, p["y"] + r * 0.6,
                                   outline=p["color"], width=1)
        p["ring"] = ring


def animate(canvas, width, height, accent_name):
    """Draw theme-appropriate particles on `canvas` and keep them moving
    until the canvas is destroyed. Safe to call once per canvas."""
    particles = _particles_for(accent_name, width, height)
    for p in particles:
        _draw(canvas, p)

    def tick():
        if not canvas.winfo_exists():
            return
        for p in particles:
            t = p["type"]
            if t == "sparkle":
                p["phase"] += p["speed"]
                visible = (math.sin(p["phase"]) + 1) / 2
                canvas.itemconfig(p["item"], state=("normal" if visible > 0.35 else "hidden"))
            elif t == "drift":
                p["x"] += p["dx"]
                p["y"] += p["dy"]
                if p["x"] > width + 3:
                    p["x"] = -3
                r = p["r"]
                canvas.coords(p["item"], p["x"] - r, p["y"] - r, p["x"] + r, p["y"] + r)
            elif t == "rise":
                p["wobble"] += 0.05
                p["y"] -= p["speed"]
                p["x"] += math.sin(p["wobble"]) * 0.2
                if p["y"] < -5:
                    p["y"] = height + 5
                    p["x"] = random.uniform(0, width)
                r = p["r"]
                canvas.coords(p["item"], p["x"] - r, p["y"] - r, p["x"] + r, p["y"] + r)
            elif t == "planet":
                p["x"] += p["dx"]
                p["y"] += p["dy"]
                if p["x"] < -10:
                    p["x"] = width + 10
                elif p["x"] > width + 10:
                    p["x"] = -10
                r = p["r"]
                canvas.coords(p["item"], p["x"] - r, p["y"] - r, p["x"] + r, p["y"] + r)
                canvas.coords(p["ring"], p["x"] - r * 1.9, p["y"] - r * 0.6, p["x"] + r * 1.9, p["y"] + r * 0.6)
            elif t == "vine":
                p["phase"] += p["speed"]
                sway = math.sin(p["phase"]) * 6
                x0, y0, x1, y1 = p["x"], 0, p["x"] + sway, p["length"]
                mid_x = (x0 + x1) / 2 + sway * 0.4
                canvas.coords(p["item"], x0, y0, mid_x, p["length"] * 0.5, x1, y1)
                for leaf_item, frac in zip(p["leaf_items"], p["leaf_frac"]):
                    ly = p["length"] * frac
                    lx = p["x"] + sway * frac
                    canvas.coords(leaf_item, lx - 3, ly - 3, lx + 3, ly + 3)
        canvas.after(60, tick)

    tick()
