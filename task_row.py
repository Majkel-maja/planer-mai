
# task_row.py

import tkinter as tk
import tkinter.font as tkfont
from config import category_color

STAR_OFF = "☆"  # szara
STAR_ON  = "★"  # żółta

class TaskRow:
    def __init__(
        self,
        master,
        text,
        cat,
        on_change,
        c,
        s,
        row_color=None,
        on_delete=None,
        meta=None,
        on_star_toggle=None,
        star=False,
        is_repeat=False,
    ):
        self.master = master
        self.text = str(text)
        self.cat = str(cat or "Inne")
        self.on_change = on_change
        self.on_delete = on_delete
        self.on_star_toggle = on_star_toggle
        self.c = c
        self.s = s
        self.meta = meta                  # 'dd.mm' lub None
        self._starred = bool(star)        # stan gwiazdki
        self._is_repeat = bool(is_repeat) # czy to element serii powtórzeń
        self.var = tk.BooleanVar(value=False)
        self.row_bg = row_color or c["CARD"]
        self.anim_label = None

        # flaga czy widget już zniszczony
        self._destroyed = False

        # Wiersz (NAJWAŻNIEJSZA ZMIANA: nie pakujemy go od razu)
        self.frame = tk.Frame(
            master, bg=self.row_bg,
            highlightbackground=c["BORDER"], highlightcolor=c["BORDER"], highlightthickness=2
        )
        self._pack_opts = dict(fill="x", pady=5, padx=8)

        # Lewa część: checkbox + tekst
        main = tk.Frame(self.frame, bg=self.row_bg)
        main.pack(side="left", fill="x", expand=True, pady=8, padx=8)

        self.chk = tk.Checkbutton(
            main, variable=self.var, command=self._toggle,
            bg=self.row_bg, activebackground=self.row_bg, fg=self.c["TEXT"],
            selectcolor=self.c["CARD_2"], highlightthickness=0, cursor="hand2"
        )
        self.chk.grid(row=0, column=0, padx=(0, 8), sticky="nw")

        self.font_normal = tkfont.Font(family="Segoe UI", size=self.s["task"], weight="bold")
        self.font_done = tkfont.Font(family="Segoe UI", size=self.s["task"], weight="bold")
        self.font_done.configure(overstrike=1)

        self.label = tk.Label(
            main, text=self.text, font=self.font_normal,
            bg=self.row_bg, fg=self.c["TEXT"], anchor="w",
            wraplength=self.s["wrap"], justify="left"
        )
        self.label.grid(row=0, column=1, sticky="w")

        # Prawa część: ⭐ → badge → Usuń → data
        right = tk.Frame(self.frame, bg=self.row_bg)
        right.pack(side="right", padx=8)

        # ⭐
        self.star_btn = tk.Button(
            right,
            text=STAR_ON if self._starred else STAR_OFF,
            bd=0, padx=6, pady=2, cursor="hand2",
            bg=self.row_bg,
            fg=("#FFD54F" if self._starred else "#A0A0A0"),
            activebackground=self.row_bg,
            activeforeground=("#FFD54F" if self._starred else "#A0A0A0"),
            font=("Segoe UI", max(self.s["button"], 10), "bold"),
            command=self._toggle_star
        )
        self.star_btn.pack(side="left", padx=(0, 8))

        # badge kategorii
        self.badge = tk.Label(
            right, text=self.cat,
            bg="#0E0E10", fg="white",
            font=("Segoe UI", self.s["button"], "bold"),
            padx=12, pady=4, cursor="arrow",
            highlightthickness=2, highlightbackground=category_color(self.cat)
        )
        self.badge.pack(side="left", padx=(0, 8))

        # Usuń
        self.btn_del = tk.Button(
            right, text="Usuń", command=self.destroy,
            bg=self.c["CARD_2"], fg=self.c["TEXT"], bd=0, padx=10, pady=6, cursor="hand2",
            activebackground=self.c["CARD_2"], activeforeground=self.c["TEXT"]
        )
        self.btn_del.bind("<Enter>", lambda _e: self.btn_del.configure(bg=self.c["CARD"]))
        self.btn_del.bind("<Leave>", lambda _e: self.btn_del.configure(bg=self.c["CARD_2"]))
        self.btn_del.pack(side="left", padx=(0, 8))

        # Data
        self.date_label = tk.Label(
            right,
            text=(self.meta or ""),
            bg=self.row_bg,
            fg=self.c["MUTED"],
            font=("Segoe UI", max(self.s["button"] - 1, 8))
        )
        if self.meta:
            self.date_label.pack(side="left", padx=(0, 0))

    # Widoczność (dla filtrów)
    def show(self):
        # nie próbuj pakować jeśli już zniszczone albo nie istnieje
        if self._destroyed:
            return
        if not self.frame.winfo_exists():
            return
        if not self.frame.winfo_ismapped():
            # TERAZ dopiero pakujemy pierwszy raz
            self.frame.pack(**self._pack_opts)

    def hide(self):
        if self._destroyed:
            return
        if not self.frame.winfo_exists():
            return
        if self.frame.winfo_ismapped():
            self.frame.pack_forget()

    def set_visible(self, visible: bool):
        (self.show() if visible else self.hide())

    # Animacja po odhaczeniu
    def _show_animation(self):
        if self._destroyed:
            return
        if self.anim_label:
            self.anim_label.destroy()
        anim_texts = ["✨ Dobrze!", "🌟 Super!", "✅ Gotowe!", "⭐ Brawo!"]
        import random
        text = random.choice(anim_texts)
        self.anim_label = tk.Label(
            self.frame, text=text, fg=self.c["ACCENT"],
            bg=self.row_bg, font=("Segoe UI", self.s["task"], "bold")
        )
        self.anim_label.pack(side="right", padx=10)

        def blink(times=6):
            if self._destroyed or not self.anim_label:
                return
            if times <= 0:
                self.anim_label.destroy(); self.anim_label = None; return
            current = self.anim_label.cget("fg")
            new_color = self.c["TEXT"] if current == self.c["ACCENT"] else self.c["ACCENT"]
            self.anim_label.configure(fg=new_color)
            self.frame.after(120, blink, times - 1)
        blink()

    def _toggle(self):
        # kliknięcie checkboxa
        if self.var.get():
            self.label.configure(font=self.font_done, fg=self.c["MUTED"])
            self.badge.configure(bg="#151515", fg="#D0D0D0")
            self._show_animation()
        else:
            self.label.configure(font=self.font_normal, fg=self.c["TEXT"])
            self.badge.configure(bg="#0E0E10", fg="white")
            if self.anim_label:
                self.anim_label.destroy(); self.anim_label = None
        if self.on_change:
            self.on_change()

    # ⭐ logika
    def _toggle_star(self):
        self._starred = not self._starred
        self.star_btn.configure(
            text=(STAR_ON if self._starred else STAR_OFF),
            fg=("#FFD54F" if self._starred else "#A0A0A0"),
            activeforeground=("#FFD54F" if self._starred else "#A0A0A0"),
        )
        if self.on_star_toggle:
            self.on_star_toggle(self, self._starred)

    def get_starred(self) -> bool:
        return self._starred

    def get_is_repeat(self) -> bool:
        return self._is_repeat

    # Akcesory
    def is_done(self) -> bool:
        return bool(self.var.get())

    def get_text(self) -> str:
        return self.text

    def get_cat(self) -> str:
        return self.cat

    def get_meta(self):
        return self.meta

    def set_meta(self, meta: str | None):
        self.meta = meta
        if self._destroyed or not self.frame.winfo_exists():
            return
        if self.meta:
            self.date_label.configure(text=self.meta)
            if not self.date_label.winfo_ismapped():
                self.date_label.pack(side="left", padx=(0, 0))
        else:
            if self.date_label.winfo_ismapped():
                self.date_label.pack_forget()

    def set_done(self, value: bool, silent: bool = False):
        """Ustawia stan przy odtwarzaniu z pliku itp.
        silent=True = bez animacji."""
        self.var.set(bool(value))
        if bool(value):
            self.label.configure(font=self.font_done, fg=self.c["MUTED"])
            self.badge.configure(bg="#151515", fg="#D0D0D0")
            if not silent:
                self._show_animation()
        else:
            self.label.configure(font=self.font_normal, fg=self.c["TEXT"])
            self.badge.configure(bg="#0E0E10", fg="white")
            if self.anim_label:
                self.anim_label.destroy(); self.anim_label = None
        if self.on_change:
            self.on_change()

    def destroy(self):
        """Usuń wiersz poprawnie i daj znać aplikacji."""
        if self._destroyed:
            return
        self._destroyed = True

        # powiedz aplikacji żeby wyrzuciła mnie z listy
        if self.on_delete:
            self.on_delete(self)

        # spróbuj zniszczyć UI
        try:
            self.frame.destroy()
        finally:
            # zapisz zmiany po usunięciu
            if self.on_change:
                self.on_change()
