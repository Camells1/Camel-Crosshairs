"""Generates 100 premade crosshair presets: 20 colors x 5 shape styles."""

COLORS = [
    ("Neon Green", "#39FF14"),
    ("Crimson Red", "#FF3131"),
    ("Cyan", "#00E5FF"),
    ("Magenta", "#FF00FF"),
    ("Yellow", "#FFEA00"),
    ("White", "#FFFFFF"),
    ("Orange", "#FF8C00"),
    ("Hot Pink", "#FF1493"),
    ("Purple", "#9B30FF"),
    ("Sky Blue", "#1E90FF"),
    ("Lime", "#ADFF2F"),
    ("Turquoise", "#00CED1"),
    ("Gold", "#FFD700"),
    ("Deep Crimson", "#DC143C"),
    ("Pale Blue", "#87CEEB"),
    ("Violet", "#EE82EE"),
    ("Mint", "#98FF98"),
    ("Coral", "#FF7F50"),
    ("Aqua", "#40E0D0"),
    ("Rose", "#FF66CC"),
]

SHAPE_STYLES = [
    {"suffix": "Classic Cross", "shape": "cross", "size": 10, "thickness": 2, "gap": 4, "outline_width": 1},
    {"suffix": "Micro Dot", "shape": "dot", "size": 4, "thickness": 3, "gap": 0, "outline_width": 1},
    {"suffix": "Bold X", "shape": "x", "size": 14, "thickness": 3, "gap": 5, "outline_width": 1},
    {"suffix": "Cross + Dot", "shape": "cross_dot", "size": 8, "thickness": 2, "gap": 6, "outline_width": 1},
    {"suffix": "Thin Circle", "shape": "circle", "size": 12, "thickness": 1, "gap": 0, "outline_width": 0},
]


def generate_presets():
    presets = []
    for color_name, color_hex in COLORS:
        for style in SHAPE_STYLES:
            presets.append({
                "name": f"{color_name} {style['suffix']}",
                "shape": style["shape"],
                "color": color_hex,
                "outline_color": "#000000",
                "outline_width": style["outline_width"],
                "size": style["size"],
                "thickness": style["thickness"],
                "gap": style["gap"],
            })
    return presets


PRESETS = generate_presets()
