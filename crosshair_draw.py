import tkinter as tk


def draw_crosshair(canvas, cx, cy, shape, color, outline_color="", outline_width=0,
                    size=10, thickness=2, gap=4):
    """Draw a crosshair shape centered at (cx, cy) on any Tk canvas.

    Shared by the real overlay window and the small preset thumbnails so
    both always render identically.
    """
    length = max(1, int(size))
    gap = max(0, int(gap))
    thickness = max(1, int(thickness))
    ow = max(0, int(outline_width))

    def line(x1, y1, x2, y2):
        if ow > 0 and outline_color:
            canvas.create_line(x1, y1, x2, y2, fill=outline_color,
                                width=thickness + ow * 2, capstyle=tk.PROJECTING)
        canvas.create_line(x1, y1, x2, y2, fill=color, width=thickness, capstyle=tk.PROJECTING)

    def oval(x1, y1, x2, y2, fill_flag=False):
        if ow > 0 and outline_color:
            canvas.create_oval(
                x1 - ow, y1 - ow, x2 + ow, y2 + ow,
                outline=outline_color, width=thickness + ow,
                fill=(outline_color if fill_flag else ""),
            )
        canvas.create_oval(
            x1, y1, x2, y2, outline=color, width=thickness,
            fill=(color if fill_flag else ""),
        )

    if shape in ("cross", "cross_dot", "t"):
        line(cx, cy - gap - length, cx, cy - gap)
        if shape != "t":
            line(cx, cy + gap, cx, cy + gap + length)
        line(cx - gap - length, cy, cx - gap, cy)
        line(cx + gap, cy, cx + gap + length, cy)
    elif shape == "x":
        d = int(length * 0.7071)
        g = int(gap * 0.7071)
        line(cx - g - d, cy - g - d, cx - g, cy - g)
        line(cx + g, cy + g, cx + g + d, cy + g + d)
        line(cx - g - d, cy + g + d, cx - g, cy + g)
        line(cx + g, cy - g, cx + g + d, cy - g - d)
    elif shape == "circle":
        oval(cx - length, cy - length, cx + length, cy + length)

    if shape in ("dot", "cross_dot"):
        r = max(1, thickness)
        oval(cx - r, cy - r, cx + r, cy + r, fill_flag=True)
