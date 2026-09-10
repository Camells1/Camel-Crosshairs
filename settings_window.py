import os
import sys
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, simpledialog, ttk

from PIL import Image, ImageTk

import backdrop
import config
import theme
from crosshair_draw import draw_crosshair
from presets import PRESETS

SHAPES = [
    ("Cross", "cross"),
    ("Cross + Dot", "cross_dot"),
    ("Dot", "dot"),
    ("X", "x"),
    ("T", "t"),
    ("Circle", "circle"),
]

WINDOW_W, WINDOW_H = 640, 820
TOP_W, TOP_H = WINDOW_W - 28, 190
RAIL_W, RAIL_H = 140, 520
PREVIEW_SIZE = 130
THUMB_SIZE = 64
CARD_W, CARD_H = THUMB_SIZE + 26, THUMB_SIZE + 42


def _asset_path(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "assets", name)


class SettingsWindow:
    def __init__(self, master, settings, overlay, on_change, on_exit, on_accent_change=None):
        self.settings = settings
        self.overlay = overlay
        self.on_change = on_change
        self.on_exit = on_exit
        self.on_accent_change = on_accent_change

        self.win = tk.Toplevel(master)
        theme.apply_theme(self.win)
        self.win.configure(bg=theme.BG)
        self.win.title("Camel Crosshairs")
        self.win.geometry(f"{WINDOW_W}x{WINDOW_H}")
        self.win.resizable(False, False)
        self._apply_window_icon()
        # The window's native close (X) button quits the whole app, crosshair
        # included — matches what closing a window normally means. "Hide
        # Panel" (bottom bar) is the dedicated minimize-to-tray action.
        self.win.protocol("WM_DELETE_WINDOW", self.on_exit)

        self.mode_var = tk.StringVar(value=self.settings.get("mode", "shape"))
        self.shape_var = tk.StringVar()
        self.custom_presets = config.load_custom_presets()
        self._thumb_image_refs = []

        self._build_top()
        self._build_body()
        self._build_bottom()

        self._load_from_settings()

    def _apply_window_icon(self):
        """Window/taskbar icon follows the active theme, same as Camel
        Launcher's per-accent logo files. iconphoto (unlike iconbitmap)
        accepts a PNG-based image directly."""
        try:
            img = Image.open(_asset_path(os.path.join("logos", theme.LOGO_FILE))).convert("RGBA")
            img.thumbnail((64, 64), Image.LANCZOS)
            self._window_icon_photo = ImageTk.PhotoImage(img)
            self.win.iconphoto(False, self._window_icon_photo)
        except Exception:
            pass

    # ---------- top: gradient hero panel, live preview + mode switch ----------

    def _build_top(self):
        top = theme.gradient_canvas(
            self.win, TOP_W, TOP_H, theme.CARD, theme.PANEL,
            highlightthickness=1, highlightbackground=theme.CARD_BORDER,
        )
        top.pack(padx=14, pady=14)
        backdrop.animate(top, TOP_W, TOP_H, theme.ACCENT_NAME)

        self.preview_canvas = tk.Canvas(
            top, width=PREVIEW_SIZE, height=PREVIEW_SIZE, bg=theme.PREVIEW_BG,
            highlightthickness=1, highlightbackground=theme.CARD_BORDER,
        )
        top.create_window(20, 20, anchor="nw", window=self.preview_canvas)

        try:
            logo_img = Image.open(_asset_path(os.path.join("logos", theme.LOGO_FILE))).convert("RGBA")
            logo_img.thumbnail((60, 60), Image.LANCZOS)
            # Fade the alpha channel so the logo reads as a watermark sitting
            # IN the panel rather than a sticker on top of it.
            r, g, b, a = logo_img.split()
            a = a.point(lambda v: int(v * 0.3))
            logo_img.putalpha(a)
            self._logo_photo = ImageTk.PhotoImage(logo_img)
            top.create_image(TOP_W - 16, 16, image=self._logo_photo, anchor="ne")
        except Exception:
            pass

        text_x = 20 + PREVIEW_SIZE + 24
        title_bg = theme.gradient_color_at(theme.CARD, theme.PANEL, 0.06)
        desc_bg = theme.gradient_color_at(theme.CARD, theme.PANEL, 0.24)
        seg_bg = theme.gradient_color_at(theme.CARD, theme.PANEL, 0.55)

        title_lbl = tk.Label(top, text="Camel Crosshairs", bg=title_bg, fg=theme.FG, font=theme.FONT_TITLE)
        top.create_window(text_x, 20, anchor="nw", window=title_lbl)

        desc_lbl = tk.Label(
            top, text="Pick a preset, tweak a shape, or upload your own image.",
            bg=desc_bg, fg=theme.FG_MUTED, font=theme.FONT,
            wraplength=TOP_W - text_x - 34, justify="left",
        )
        top.create_window(text_x, 50, anchor="nw", window=desc_lbl)

        seg_row = tk.Frame(top, bg=seg_bg)
        self.shape_seg_btn = theme.segmented_button(seg_row, "Shape", lambda: self._set_mode("shape"))
        self.image_seg_btn = theme.segmented_button(seg_row, "Image", lambda: self._set_mode("image"))
        self.shape_seg_btn.pack(side="left")
        self.image_seg_btn.pack(side="left", padx=(6, 0))
        top.create_window(text_x, 100, anchor="nw", window=seg_row)

        save_btn = ttk.Button(top, text="+ Save as Preset", style="Accent.TButton", command=self._save_as_preset)
        top.create_window(text_x, 144, anchor="nw", window=save_btn)

    def _set_mode(self, mode):
        self.mode_var.set(mode)
        self._update_segmented()
        self._apply()

    def _update_segmented(self):
        mode = self.mode_var.get()
        for btn, val in ((self.shape_seg_btn, "shape"), (self.image_seg_btn, "image")):
            active = mode == val
            btn.config(
                bg=theme.ACCENT if active else theme.CARD,
                fg="#2b1608" if active else theme.FG_MUTED,
            )

    # ---------- body: left icon rail + swappable pages (Camel Launcher style) ----------

    def _build_body(self):
        body = tk.Frame(self.win, bg=theme.BG)
        body.pack(fill="both", expand=True, padx=14, pady=(0, 0))

        rail = theme.gradient_canvas(body, RAIL_W, RAIL_H, theme.RAIL, theme.PREVIEW_BG)
        rail.pack(side="left", fill="y")

        content = tk.Frame(body, bg=theme.BG)
        content.pack(side="left", fill="both", expand=True, padx=(14, 0))

        page_defs = [
            ("presets", "Presets"),
            ("shape", "Shape"),
            ("image", "Image"),
            ("display", "Display"),
            ("appearance", "Appearance"),
        ]

        self.pages = {}
        self.rail_buttons = {}
        y = 20
        for key, label in page_defs:
            page = tk.Frame(content, bg=theme.BG)
            self.pages[key] = page
            btn = theme.rail_button(rail, label, lambda k=key: self._show_page(k))
            rail.create_window(RAIL_W // 2, y, anchor="n", window=btn)
            y += 56
            self.rail_buttons[key] = btn

        self._build_presets_tab(self.pages["presets"])
        self._build_shape_tab(self.pages["shape"])
        self._build_image_tab(self.pages["image"])
        self._build_display_tab(self.pages["display"])
        self._build_appearance_page(self.pages["appearance"])

        self._show_page(getattr(self, "_current_page", "presets"))

    def _show_page(self, key):
        for k, page in self.pages.items():
            if k == key:
                page.pack(fill="both", expand=True)
            else:
                page.pack_forget()
        for k, btn in self.rail_buttons.items():
            active = k == key
            btn.config(
                bg=theme.ACCENT if active else theme.CARD,
                fg="#2b1608" if active else theme.FG_MUTED,
            )
        self._current_page = key

    # ---------- Appearance page ----------

    def _build_appearance_page(self, parent):
        wrap = ttk.Frame(parent)
        wrap.pack(fill="both", expand=True)

        ttk.Label(wrap, text="Theme", style="Title.TLabel").pack(anchor="w", padx=14, pady=(10, 4))
        ttk.Label(
            wrap,
            text="Pick an accent + background for this settings window "
                 "(your crosshair's own color is set separately, in Shape).",
            style="Muted.TLabel", wraplength=360,
        ).pack(anchor="w", padx=14, pady=(0, 14))

        grid = tk.Frame(wrap, bg=theme.BG)
        grid.pack(anchor="w", padx=10)

        for i, (name, info) in enumerate(theme.ACCENTS.items()):
            r, c = divmod(i, 3)
            card = self._make_accent_swatch(grid, name, info)
            card.grid(row=r, column=c, padx=8, pady=8)

    def _make_accent_swatch(self, parent, name, info):
        active = theme.ACCENT_NAME == name
        card = theme.gradient_canvas(
            parent, 96, 96, theme.CARD, theme.PANEL,
            highlightthickness=2, highlightbackground=(theme.ACCENT if active else theme.CARD_BORDER),
            cursor="hand2",
        )
        swatch = tk.Canvas(card, width=48, height=48, bg=theme.CARD, highlightthickness=0)
        card.create_window(48, 14, anchor="n", window=swatch)
        swatch.create_oval(4, 4, 44, 44, fill=info["accent"], outline="")

        label_bg = theme.gradient_color_at(theme.CARD, theme.PANEL, 0.85)
        lbl = tk.Label(
            card, text=info["label"], bg=label_bg,
            fg=(theme.FG if active else theme.FG_MUTED), font=theme.FONT_SMALL,
        )
        card.create_window(48, 68, anchor="n", window=lbl)

        def apply(_e=None):
            self._set_accent(name)

        for w in (card, swatch, lbl):
            w.bind("<Button-1>", apply)

        return card

    def _set_accent(self, name):
        self.settings["ui_accent"] = name
        self.on_change(self.settings)
        theme.set_accent(name)
        self._rebuild_ui()
        if self.on_accent_change:
            self.on_accent_change()

    def _rebuild_ui(self):
        for child in self.win.winfo_children():
            child.destroy()
        theme.apply_theme(self.win)
        self.win.configure(bg=theme.BG)
        self._apply_window_icon()
        self._build_top()
        self._build_body()
        self._build_bottom()
        self._load_from_settings()

    # ---------- Presets tab ----------

    def _build_presets_tab(self, parent):
        outer = tk.Frame(parent, bg=theme.BG)
        outer.pack(fill="both", expand=True, pady=(8, 0))

        canvas = tk.Canvas(outer, bg=theme.BG, highlightthickness=0)
        vbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        vbar.pack(side="right", fill="y")

        self._presets_grid = tk.Frame(canvas, bg=theme.BG)
        grid_window = canvas.create_window((0, 0), window=self._presets_grid, anchor="nw")

        def on_configure(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_resize(event):
            canvas.itemconfig(grid_window, width=event.width)

        self._presets_grid.bind("<Configure>", on_configure)
        canvas.bind("<Configure>", on_canvas_resize)

        def on_wheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def bind_wheel(_e):
            canvas.bind_all("<MouseWheel>", on_wheel)

        def unbind_wheel(_e):
            canvas.unbind_all("<MouseWheel>")

        outer.bind("<Enter>", bind_wheel)
        outer.bind("<Leave>", unbind_wheel)

        self._populate_presets_grid()

    def _populate_presets_grid(self):
        for child in self._presets_grid.winfo_children():
            child.destroy()
        self._thumb_image_refs.clear()

        cols = 5
        row_cursor = 0

        if self.custom_presets:
            hdr = tk.Label(
                self._presets_grid, text=f"My Presets ({len(self.custom_presets)})",
                bg=theme.BG, fg=theme.FG, font=theme.FONT_TITLE, anchor="w",
            )
            hdr.grid(row=row_cursor, column=0, columnspan=cols, sticky="w", padx=6, pady=(4, 2))
            row_cursor += 1
            for i, preset in enumerate(self.custom_presets):
                r, c = divmod(i, cols)
                card = self._make_preset_card(self._presets_grid, preset, deletable=True)
                card.grid(row=row_cursor + r, column=c, padx=5, pady=5)
            row_cursor += (len(self.custom_presets) + cols - 1) // cols

        hdr2 = tk.Label(
            self._presets_grid, text=f"Built-in Presets ({len(PRESETS)})",
            bg=theme.BG, fg=theme.FG, font=theme.FONT_TITLE, anchor="w",
        )
        hdr2.grid(row=row_cursor, column=0, columnspan=cols, sticky="w", padx=6, pady=(10, 2))
        row_cursor += 1
        for i, preset in enumerate(PRESETS):
            r, c = divmod(i, cols)
            card = self._make_preset_card(self._presets_grid, preset, deletable=False)
            card.grid(row=row_cursor + r, column=c, padx=5, pady=5)

    def _make_preset_card(self, parent, preset, deletable=False):
        card = theme.gradient_canvas(
            parent, CARD_W, CARD_H, theme.CARD, theme.PANEL,
            highlightthickness=1, highlightbackground=theme.CARD_BORDER, cursor="hand2",
        )
        cv = tk.Canvas(card, width=THUMB_SIZE, height=THUMB_SIZE, bg=theme.PREVIEW_BG, highlightthickness=0)
        card.create_window(CARD_W // 2, 10, anchor="n", window=cv)
        self._draw_preset_thumb(cv, preset)

        top_bg = theme.gradient_color_at(theme.CARD, theme.PANEL, 0.05)
        label_bg = theme.gradient_color_at(theme.CARD, theme.PANEL, 0.85)
        lbl = tk.Label(
            card, text=preset.get("name", "Custom"), bg=label_bg, fg=theme.FG_MUTED,
            font=theme.FONT_SMALL, wraplength=THUMB_SIZE + 18, justify="center",
        )
        card.create_window(CARD_W // 2, THUMB_SIZE + 16, anchor="n", window=lbl)

        def apply(_e=None):
            self._apply_preset(preset)

        def on_enter(_e=None):
            card.config(highlightbackground=theme.ACCENT)

        def on_leave(_e=None):
            card.config(highlightbackground=theme.CARD_BORDER)

        for w in (card, cv, lbl):
            w.bind("<Button-1>", apply)
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)

        if deletable:
            del_btn = tk.Label(
                card, text="×", bg=top_bg, fg=theme.FG_MUTED,
                font=theme.FONT_BOLD, cursor="hand2",
            )
            card.create_window(CARD_W - 4, 2, anchor="ne", window=del_btn)

            def on_delete(_e=None):
                self._delete_custom_preset(preset)

            del_btn.bind("<Button-1>", on_delete)
            del_btn.bind("<Enter>", lambda _e: del_btn.config(fg="#ff6b6b"))
            del_btn.bind("<Leave>", lambda _e: del_btn.config(fg=theme.FG_MUTED))

        return card

    def _draw_preset_thumb(self, cv, preset):
        if preset.get("mode") == "image" and preset.get("image_path"):
            try:
                img = Image.open(preset["image_path"]).convert("RGBA")
                scale = max(1, preset.get("image_scale", 100)) / 100.0 * 0.55
                w = max(1, int(img.width * scale))
                h = max(1, int(img.height * scale))
                if w > THUMB_SIZE or h > THUMB_SIZE:
                    ratio = min(THUMB_SIZE / w, THUMB_SIZE / h)
                    w = max(1, int(w * ratio))
                    h = max(1, int(h * ratio))
                img = img.resize((w, h), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self._thumb_image_refs.append(photo)
                cv.create_image(THUMB_SIZE // 2, THUMB_SIZE // 2, image=photo)
                return
            except Exception:
                pass
        draw_crosshair(
            cv, THUMB_SIZE // 2, THUMB_SIZE // 2,
            shape=preset.get("shape", "cross"), color=preset.get("color", "#39FF14"),
            outline_color=preset.get("outline_color", ""), outline_width=preset.get("outline_width", 0),
            size=preset.get("size", 10) * 0.55, thickness=max(1, round(preset.get("thickness", 2) * 0.75)),
            gap=preset.get("gap", 4) * 0.55,
        )

    def _apply_preset(self, preset):
        self.settings["mode"] = preset.get("mode", "shape")
        if preset.get("mode") == "image":
            self.settings["image_path"] = preset.get("image_path")
            self.settings["image_scale"] = preset.get("image_scale", 100)
        else:
            self.settings["shape"] = preset["shape"]
            self.settings["color"] = preset["color"]
            self.settings["outline_color"] = preset["outline_color"]
            self.settings["outline_width"] = preset["outline_width"]
            self.settings["size"] = preset["size"]
            self.settings["thickness"] = preset["thickness"]
            self.settings["gap"] = preset["gap"]
        self.mode_var.set(self.settings["mode"])
        self._load_from_settings()
        self._apply()

    def _save_as_preset(self):
        name = simpledialog.askstring(
            "Save Preset", "Name this crosshair:", parent=self.win,
            initialvalue=f"My Crosshair {len(self.custom_presets) + 1}",
        )
        if not name:
            return
        s = self.settings
        if s.get("mode") == "image" and s.get("image_path"):
            preset = {
                "name": name, "mode": "image",
                "image_path": s.get("image_path"), "image_scale": s.get("image_scale", 100),
            }
        else:
            preset = {
                "name": name, "mode": "shape",
                "shape": s.get("shape", "cross"), "color": s.get("color", "#39FF14"),
                "outline_color": s.get("outline_color", "#000000"),
                "outline_width": s.get("outline_width", 1),
                "size": s.get("size", 10), "thickness": s.get("thickness", 2), "gap": s.get("gap", 4),
            }
        self.custom_presets.append(preset)
        config.save_custom_presets(self.custom_presets)
        self._populate_presets_grid()
        self._show_page("presets")

    def _delete_custom_preset(self, preset):
        if not messagebox.askyesno("Delete Preset", f"Delete \"{preset.get('name', 'this preset')}\"?", parent=self.win):
            return
        try:
            self.custom_presets.remove(preset)
        except ValueError:
            pass
        config.save_custom_presets(self.custom_presets)
        self._populate_presets_grid()

    # ---------- Shape tab ----------

    def _build_shape_tab(self, parent):
        pad = {"padx": 14, "pady": 8}
        wrap = ttk.Frame(parent)
        wrap.pack(fill="both", expand=True)

        row = ttk.Frame(wrap)
        row.pack(fill="x", **pad)
        ttk.Label(row, text="Shape").pack(side="left")
        shape_combo = ttk.Combobox(
            row, textvariable=self.shape_var, state="readonly",
            values=[label for label, _ in SHAPES], width=16,
        )
        shape_combo.pack(side="right")
        shape_combo.bind("<<ComboboxSelected>>", lambda e: self._on_shape_field_change())
        self.shape_combo = shape_combo

        self.color_btn = self._color_row(wrap, "Color", "color")
        self.outline_btn = self._color_row(wrap, "Outline color", "outline_color")

        self.size_scale = self._slider_row(wrap, "Size", 2, 60, "size")
        self.thickness_scale = self._slider_row(wrap, "Thickness", 1, 12, "thickness")
        self.gap_scale = self._slider_row(wrap, "Gap", 0, 40, "gap")
        self.outline_w_scale = self._slider_row(wrap, "Outline width", 0, 6, "outline_width")

    def _on_shape_field_change(self):
        self.mode_var.set("shape")
        self._apply()

    # ---------- Image tab ----------

    def _build_image_tab(self, parent):
        pad = {"padx": 14, "pady": 8}
        wrap = ttk.Frame(parent)
        wrap.pack(fill="both", expand=True)

        ttk.Label(
            wrap, text="Upload a PNG with a transparent background for best results.",
            style="Muted.TLabel", wraplength=420,
        ).pack(anchor="w", **pad)

        btn_row = ttk.Frame(wrap)
        btn_row.pack(fill="x", padx=14, pady=(0, 8))
        ttk.Button(btn_row, text="Upload Image...", style="Accent.TButton",
                   command=self._upload_image).pack(side="left")
        self.image_name_lbl = ttk.Label(btn_row, text="(none)", style="Muted.TLabel")
        self.image_name_lbl.pack(side="left", padx=10)

        self.image_scale_scale = self._slider_row(wrap, "Image scale %", 10, 400, "image_scale",
                                                    on_change_mode="image")

    def _upload_image(self):
        path = filedialog.askopenfilename(
            title="Choose a crosshair image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All files", "*.*")],
        )
        if not path:
            return
        new_path = config.import_image(path)
        self.settings["image_path"] = new_path
        self.settings["mode"] = "image"
        self.mode_var.set("image")
        self.image_name_lbl.config(text=self._short_image_name())
        self._update_segmented()
        self._apply()

    # ---------- Display tab ----------

    def _build_display_tab(self, parent):
        pad = {"padx": 14, "pady": 8}
        wrap = ttk.Frame(parent)
        wrap.pack(fill="both", expand=True)

        self.opacity_scale = self._slider_row(
            wrap, "Opacity %", 5, 100, "opacity",
            transform_out=lambda v: v / 100.0,
            transform_in=lambda v: round(v * 100),
        )

        self.follow_cursor_var = tk.BooleanVar(value=self.settings.get("follow_cursor", True))
        ttk.Checkbutton(
            wrap, text="Follow mouse cursor (replaces the system cursor)",
            variable=self.follow_cursor_var, command=self._toggle_follow_cursor,
        ).pack(anchor="w", **pad)

        self.visible_var = tk.BooleanVar(value=self.settings.get("visible", True))
        ttk.Checkbutton(
            wrap, text="Crosshair visible", variable=self.visible_var,
            command=self._toggle_visible,
        ).pack(anchor="w", **pad)

        ttk.Label(
            wrap, text="Toggle visibility from the tray icon or the checkbox above "
                       "(no global hotkey, by design).",
            style="Muted.TLabel", wraplength=320,
        ).pack(anchor="w", padx=14, pady=(4, 0))

    def _toggle_follow_cursor(self):
        self.settings["follow_cursor"] = self.follow_cursor_var.get()
        self.overlay.refresh()
        self.on_change(self.settings)

    def _toggle_visible(self):
        if self.visible_var.get():
            self.overlay.show()
        else:
            self.overlay.hide()
        self.on_change(self.settings)

    # ---------- bottom bar ----------

    def _build_bottom(self):
        bottom = ttk.Frame(self.win)
        bottom.pack(fill="x", padx=14, pady=12, side="bottom")
        ttk.Button(bottom, text="Reset to Defaults", command=self._reset_defaults).pack(side="left")
        ttk.Button(bottom, text="Quit App", command=self.on_exit).pack(side="right")
        ttk.Button(bottom, text="Hide Panel", command=self.hide).pack(side="right", padx=6)

    # ---------- shared control builders ----------

    def _color_row(self, parent, label, key):
        row = ttk.Frame(parent)
        row.pack(fill="x", padx=14, pady=8)
        ttk.Label(row, text=label).pack(side="left")
        btn = tk.Button(row, text="   ", width=6, relief="flat", bd=0,
                         command=lambda: self._pick_color(key, btn))
        btn.pack(side="right")
        return btn

    def _slider_row(self, parent, label, lo, hi, key, transform_out=None, transform_in=None, on_change_mode=None):
        row = ttk.Frame(parent)
        row.pack(fill="x", padx=14, pady=8)
        ttk.Label(row, text=label, width=14).pack(side="left")
        var = tk.IntVar()
        scale = ttk.Scale(
            row, from_=lo, to=hi, orient="horizontal", variable=var,
            command=lambda v, k=key, tv=var, to=transform_out, m=on_change_mode: self._on_slider(k, tv, to, m),
        )
        scale.pack(side="left", fill="x", expand=True, padx=8)
        value_lbl = ttk.Label(row, text="", width=4, style="Muted.TLabel")
        value_lbl.pack(side="right")
        scale._var = var
        scale._value_lbl = value_lbl
        return scale

    # ---------- state sync ----------

    def _load_from_settings(self):
        s = self.settings
        self.mode_var.set(s.get("mode", "shape"))
        label = next((lbl for lbl, val in SHAPES if val == s.get("shape", "cross")), "Cross")
        self.shape_var.set(label)
        self._set_swatch(self.color_btn, s.get("color", "#39FF14"))
        self._set_swatch(self.outline_btn, s.get("outline_color", "#000000"))
        self._set_scale(self.size_scale, s.get("size", 10))
        self._set_scale(self.thickness_scale, s.get("thickness", 2))
        self._set_scale(self.gap_scale, s.get("gap", 4))
        self._set_scale(self.outline_w_scale, s.get("outline_width", 1))
        self._set_scale(self.image_scale_scale, s.get("image_scale", 100))
        self._set_scale(self.opacity_scale, round(s.get("opacity", 1.0) * 100))
        self.image_name_lbl.config(text=self._short_image_name())
        self._update_segmented()
        self._render_preview()

    def _set_scale(self, scale, value):
        scale._var.set(value)
        scale._value_lbl.config(text=str(value))

    def _set_swatch(self, btn, hex_color):
        btn.config(bg=hex_color, activebackground=hex_color)

    def _short_image_name(self):
        path = self.settings.get("image_path")
        if not path:
            return "(none)"
        return os.path.basename(path)

    # ---------- handlers ----------

    def _on_slider(self, key, var, transform_out, on_change_mode):
        raw = var.get()
        value = transform_out(raw) if transform_out else raw
        self.settings[key] = value
        for scale in (
            self.size_scale, self.thickness_scale, self.gap_scale,
            self.outline_w_scale, self.image_scale_scale, self.opacity_scale,
        ):
            if scale._var is var:
                scale._value_lbl.config(text=str(raw))
        if on_change_mode:
            self.mode_var.set(on_change_mode)
            self._update_segmented()
        self._apply()

    def _pick_color(self, key, btn):
        current = self.settings.get(key, "#000000")
        result = colorchooser.askcolor(color=current, title="Choose color")
        if result and result[1]:
            self.settings[key] = result[1]
            self._set_swatch(btn, result[1])
            self.mode_var.set("shape")
            self._update_segmented()
            self._apply()

    def _reset_defaults(self):
        self.settings.clear()
        self.settings.update(config.DEFAULTS)
        self.follow_cursor_var.set(self.settings.get("follow_cursor", True))
        self.visible_var.set(self.settings.get("visible", True))
        self._load_from_settings()
        self._apply()

    def _apply(self, save_only=False):
        selected_label = self.shape_var.get()
        shape_val = next((val for lbl, val in SHAPES if lbl == selected_label), "cross")
        self.settings["shape"] = shape_val
        self.settings["mode"] = self.mode_var.get()
        if not save_only:
            self.overlay.refresh()
        self._render_preview()
        self.on_change(self.settings)

    def _render_preview(self):
        self.preview_canvas.delete("all")
        c = PREVIEW_SIZE // 2
        s = self.settings
        if s.get("mode") == "image" and s.get("image_path"):
            try:
                img = Image.open(s["image_path"]).convert("RGBA")
                scale = max(1, s.get("image_scale", 100)) / 100.0
                w = max(1, int(img.width * scale))
                h = max(1, int(img.height * scale))
                if w > PREVIEW_SIZE or h > PREVIEW_SIZE:
                    ratio = min(PREVIEW_SIZE / w, PREVIEW_SIZE / h)
                    w = max(1, int(w * ratio))
                    h = max(1, int(h * ratio))
                img = img.resize((w, h), Image.LANCZOS)
                self._preview_img = ImageTk.PhotoImage(img)
                self.preview_canvas.create_image(c, c, image=self._preview_img)
                return
            except Exception:
                pass
        draw_crosshair(
            self.preview_canvas, c, c,
            shape=s.get("shape", "cross"), color=s.get("color", "#39FF14"),
            outline_color=s.get("outline_color", ""), outline_width=s.get("outline_width", 0),
            size=s.get("size", 10), thickness=s.get("thickness", 2), gap=s.get("gap", 4),
        )

    # ---------- window visibility ----------

    def show(self):
        self.win.deiconify()
        self.win.lift()

    def hide(self):
        self.win.withdraw()
