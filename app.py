import json
import os
import sys
import ctypes
from pathlib import Path
from datetime import date, timedelta
import tkinter as tk
from tkinter import messagebox

from config import PLIK, PALETA, CATEGORIES, sizes, style_button
from task_row import TaskRow
import db  # baza SQLite
from powtarzanie import (
    REPEAT_OPTIONS,
    fmt_ddmm,
    meta_to_ddmm_date,
    generate_repeats,
)


class TodoApp:
    def __init__(self, root):
        self.root = root
        self.c = PALETA
        self.zoomed = False  # tylko wpływa na rozmiary fontów
        self.tasks = []
        self._row_toggle = False
        self.filter_mode = "all"  # all | today | tomorrow
        self._seq = 0             # kolejność tworzenia

        # fullscreen state (nasz własny fullscreen bez ramek)
        self._fullscreen = False
        self._last_geometry = None

        # -- Tytuł i ikona aplikacji --
        root.title("Planer Maji")
        self._setup_app_icon()

        # startowy rozmiar okna: 800x700 i lekko od góry
        root.geometry("800x700+50+10")

        # Skróty klawiszowe do fullscreen
        root.bind("<F11>", self._on_f11)
        root.bind("<Escape>", self._on_escape)

        # Inicjalizacja bazy SQLite
        db.init_db()  # tworzy bazę/tabelę, jeśli ich nie ma

        self._build_ui()
        try:
            self.load(silent=True)
        except Exception:
            pass

    def _setup_app_icon(self):
        """
        Ustaw ikonę aplikacji (pasek tytułu + pasek zadań na Windows).
        Główny plik: 'ikona.ico' obok plików .py. Fallback: 'ikona.png' (jeśli jest).
        Na Windows ustawia też AppUserModelID, żeby pasek zadań użył naszej ikony.
        """
        try:
            base_dir = Path(__file__).resolve().parent
            ico_path = base_dir / "ikona.ico"
            png_path = base_dir / "ikona.png"

            if sys.platform.startswith("win"):
                try:
                    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("MajaPlanner.PlanerMaji")
                except Exception:
                    pass

            if ico_path.exists():
                try:
                    self.root.iconbitmap(str(ico_path))
                    return
                except Exception:
                    pass

            if png_path.exists():
                try:
                    img = tk.PhotoImage(file=str(png_path))
                    self.root.iconphoto(True, img)
                    self._icon_ref = img  # trzymaj referencję
                    return
                except Exception:
                    pass
        except Exception:
            pass  # brak ikony nie blokuje działania

    # ================== FULLSCREEN ==================
    def _on_f11(self, _e=None):
        self.toggle_fullscreen()

    def _on_escape(self, _e=None):
        if self._fullscreen:
            self.toggle_fullscreen(force_off=True)

    def toggle_fullscreen(self, force_off: bool = False):
        if force_off:
            if self._fullscreen:
                self.root.attributes("-fullscreen", False)
                if self._last_geometry:
                    self.root.geometry(self._last_geometry)
                self._fullscreen = False
                if hasattr(self, "btn_fullscreen"):
                    self.btn_fullscreen.configure(text="Pełny ekran")
            return

        if not self._fullscreen:
            self._last_geometry = self.root.winfo_geometry()
            self.root.attributes("-fullscreen", True)
            self._fullscreen = True
            if hasattr(self, "btn_fullscreen"):
                self.btn_fullscreen.configure(text="Okno")
        else:
            self.root.attributes("-fullscreen", False)
            if self._last_geometry:
                self.root.geometry(self._last_geometry)
            self._fullscreen = False
            if hasattr(self, "btn_fullscreen"):
                self.btn_fullscreen.configure(text="Pełny ekran")

    # ================== UI ==================
    def _build_ui(self):
        c = self.c
        s = sizes(self.zoomed)
        self.root.configure(bg=c["BG"])
        for w in self.root.winfo_children():
            w.destroy()

        # Pasek tytułu
        ribbon = tk.Frame(self.root, bg=c["RIBBON"])
        ribbon.pack(fill="x")
        tk.Label(
            ribbon,
            text="Planer Maji",
            bg=c["RIBBON"],
            fg="white",
            font=("Segoe UI", s["title"], "bold")
        ).pack(padx=12, pady=(10, 2))
        tk.Label(
            ribbon,
            text="Planuj i odhaczaj",
            bg=c["RIBBON"],
            fg="#D8D9E6",
            font=("Segoe UI", s["subtitle"])
        ).pack(padx=12, pady=(0, 10))

        # Karta dodawania
        card_add = tk.Frame(
            self.root,
            bg=c["CARD"],
            highlightbackground=c["BORDER"],
            highlightcolor=c["BORDER"],
            highlightthickness=2
        )
        card_add.pack(fill="x", padx=14, pady=8)

        tk.Label(
            card_add,
            text="Nowe zadanie:",
            bg=c["CARD"],
            fg=c["TEXT"],
            font=("Segoe UI", s["task"], "bold")
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))

        self.entry = tk.Entry(
            card_add,
            bg=c["ENTRY_BG"],
            fg=c["TEXT"],
            insertbackground=c["TEXT"],
            relief="flat",
            highlightthickness=2,
            highlightbackground=c["BORDER"],
            highlightcolor=c["ACCENT"],
            font=("Segoe UI", s["entry"])
        )
        self.entry.grid(
            row=1, column=0, columnspan=6, sticky="ew",
            padx=10, pady=8, ipady=(9 if self.zoomed else 7)
        )
        card_add.columnconfigure(0, weight=1)
        self.entry.bind("<Return>", self._add_from_enter)

        tk.Label(
            card_add,
            text="Kategoria:",
            bg=c["CARD"], fg=c["TEXT"],
            font=("Segoe UI", s["subtitle"], "bold")
        ).grid(row=2, column=0, sticky="w", padx=10)
        self.cat_var = tk.StringVar(value=CATEGORIES[0])
        self.cat_menu = tk.OptionMenu(card_add, self.cat_var, *CATEGORIES)
        self.cat_menu.configure(
            bg=c["CARD_2"], fg=c["TEXT"], activebackground=c["CARD"],
            bd=0, highlightthickness=0
        )
        self.cat_menu.grid(row=2, column=1, sticky="w", padx=(6, 12), pady=(0, 8))

        tk.Label(
            card_add,
            text="Powtarzanie:",
            bg=c["CARD"], fg=c["TEXT"],
            font=("Segoe UI", s["subtitle"], "bold")
        ).grid(row=2, column=2, sticky="e")
        self.repeat_var = tk.StringVar(value=REPEAT_OPTIONS[0])
        self.repeat_menu = tk.OptionMenu(card_add, self.repeat_var, *REPEAT_OPTIONS)
        self.repeat_menu.configure(
            bg=c["CARD_2"], fg=c["TEXT"], activebackground=c["CARD"],
            bd=0, highlightthickness=0
        )
        self.repeat_menu.grid(row=2, column=3, sticky="w", padx=(6, 12), pady=(0, 8))

        # Pasek przycisku "Dodaj"
        btn_row = tk.Frame(self.root, bg=c["CARD"])
        btn_row.pack(fill="x", padx=24, pady=(0, 10))
        self.btn_add = tk.Button(btn_row, text="Dodaj", command=self.add_task)
        style_button(self.btn_add, c, primary=True, fsize=s["button"])
        self.btn_add.pack(side="left")

        # Filtry
        filter_row = tk.Frame(self.root, bg=c["CARD"])
        filter_row.pack(fill="x", padx=14, pady=(0, 8))
        self.btn_all = tk.Button(filter_row, text="Wszystkie", command=lambda: self._filter_click("all"))
        style_button(self.btn_all, c, primary=False, fsize=s["button"])
        self.btn_all.pack(side="left")
        self.btn_today = tk.Button(filter_row, text="Dzisiaj", command=lambda: self._filter_click("today"))
        style_button(self.btn_today, c, primary=False, fsize=s["button"])
        self.btn_today.pack(side="left", padx=6)
        self.btn_tomorrow = tk.Button(filter_row, text="Jutro", command=lambda: self._filter_click("tomorrow"))
        style_button(self.btn_tomorrow, c, primary=False, fsize=s["button"])
        self.btn_tomorrow.pack(side="left", padx=6)

        # Scrollowana lista zadań
        card_list = tk.Frame(
            self.root, bg=c["CARD_2"],
            highlightbackground=c["BORDER"], highlightcolor=c["BORDER"], highlightthickness=2
        )
        card_list.pack(fill="both", expand=True, padx=14, pady=8)

        self.list_title = tk.Label(
            card_list, text="Twoja lista zadań:",
            bg=c["CARD_2"], fg=c["TEXT"], font=("Segoe UI", s["task"], "bold")
        )
        self.list_title.pack(anchor="w", padx=10, pady=(10, 6))

        scroll_wrap = tk.Frame(card_list, bg=c["CARD_2"])
        scroll_wrap.pack(fill="both", expand=True, padx=6, pady=(0, 10))

        self.canvas = tk.Canvas(scroll_wrap, bg=c["CARD_2"], highlightthickness=0)
        vbar = tk.Scrollbar(scroll_wrap, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        vbar.pack(side="right", fill="y")

        self.list_frame = tk.Frame(self.canvas, bg=c["CARD_2"])
        self._list_window = self.canvas.create_window((0, 0), window=self.list_frame, anchor="nw")

        self.list_frame.bind("<Configure>", lambda _e: self._update_scrollregion())
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self._list_window, width=e.width))
        self._enable_mousewheel(self.canvas)

        # Dół z przyciskami akcji
        bottom = tk.Frame(self.root, bg=c["BG"])
        bottom.pack(fill="x", padx=14, pady=10)

        self.btn_remove_done = tk.Button(bottom, text="Usuń zaznaczone", command=self.remove_done)
        style_button(self.btn_remove_done, c, primary=False, fsize=s["button"])
        self.btn_remove_done.pack(side="left")

        self.btn_clear_all = tk.Button(bottom, text="Usuń wszystko", command=self.clear_all)
        style_button(self.btn_clear_all, c, primary=False, fsize=s["button"])
        self.btn_clear_all.pack(side="left", padx=6)

        self.btn_fullscreen = tk.Button(bottom, text="Pełny ekran", command=self.toggle_fullscreen)
        style_button(self.btn_fullscreen, c, primary=False, fsize=s["button"])
        self.btn_fullscreen.pack(side="left", padx=6)

        self.btn_exit = tk.Button(bottom, text="Wyjdź", command=self.exit_app)
        style_button(self.btn_exit, c, primary=False, fsize=s["button"])
        self.btn_exit.pack(side="left", padx=6)

        # Przywrócenie zadań po rebuildzie UI
        if hasattr(self, "_pending_tasks"):
            for item in self._pending_tasks:
                self._add_row(
                    item["text"], done=item["done"], cat=item.get("cat", "Inne"),
                    meta=item.get("meta"), star=item.get("star", False),
                    created_seq=item.get("created_seq"), is_repeat=item.get("rep", False),
                )
            self._pending_tasks = None

        self.apply_filter(self.filter_mode, update_title=True)

    # ================== Scroll i filtr ==================
    def _update_scrollregion(self):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_mousewheel(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-3, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(3, "units")
        else:
            step = -1 if event.delta > 0 else 1
            self.canvas.yview_scroll(step * 3, "units")
        return "break"

    def _enable_mousewheel(self, widget):
        widget.bind("<Enter>", lambda _e: widget.focus_set())
        widget.bind("<MouseWheel>", self._on_mousewheel)
        widget.bind("<Button-4>", self._on_mousewheel)
        widget.bind("<Button-5>", self._on_mousewheel)

    # Klik filtra
    def _filter_click(self, mode: str):
        self.root.focus_set()
        self.apply_filter(mode, update_title=True)

    # ================== Dodawanie zadań ==================
    def add_task(self):
        base_text = self.entry.get().strip()
        if not base_text:
            messagebox.showinfo("Uwaga", "Wpisz treść zadania.")
            return

        cat = self.cat_var.get()
        pattern = self.repeat_var.get()
        today = date.today()

        base_date_for_main = today
        series_start_date = today

        # główne zadanie (zawsze dzisiaj)
        self._add_row(
            base_text, done=False, cat=cat,
            meta=fmt_ddmm(base_date_for_main), is_repeat=False
        )

        # automatyczne powtórzenia (też od dzisiaj)
        for d in generate_repeats(pattern, series_start_date):
            self._add_row(
                base_text, done=False, cat=cat,
                meta=fmt_ddmm(d), is_repeat=True
            )

        self.entry.delete(0, tk.END)
        self.save(silent=True)
        self._refresh_view()

    # Enter w polu tekstowym dodaje zadanie
    def _add_from_enter(self, _event=None):
        self.add_task()

    # ================== Widok / filtry ==================
    def _matches_filter(self, row, mode=None):
        if mode is None:
            mode = self.filter_mode

        today = date.today()
        tomorrow = today + timedelta(days=1)
        md = meta_to_ddmm_date(row.get_meta())

        if mode == "all":
            return True
        if mode == "today":
            return md == today
        if mode == "tomorrow":
            return md == tomorrow
        return True

    def _refresh_view(self):
        for r in self.tasks:
            r.hide()
        for r in sorted(self.tasks, key=lambda r: (not r.get_starred(), r.created_seq)):
            if self._matches_filter(r):
                r.show()
        self.root.after(10, self._update_scrollregion)

    def apply_filter(self, mode, update_title=True):
        self.filter_mode = mode
        self._refresh_view()

        if update_title:
            today_str = fmt_ddmm(date.today())
            tomorrow_str = fmt_ddmm(date.today() + timedelta(days=1))
            if mode == "all":
                title = "Wszystkie zadania"
            elif mode == "today":
                title = f"Dzisiejsze zadania ({today_str})"
            else:
                title = f"Jutrzejsze zadania ({tomorrow_str})"
            self.list_title.configure(text=title)

    # ================== Operacje na wierszach ==================
    def _add_row(self, text, done=False, cat="Inne", meta=None, star=False, created_seq=None, is_repeat=False):
        s = sizes(self.zoomed)
        row_color = self.c["CARD"] if self._row_toggle else self.c["CARD_2"]
        self._row_toggle = not self._row_toggle

        if created_seq is None:
            created_seq = self._seq
            self._seq += 1

        row = TaskRow(
            self.list_frame, text, cat,
            on_change=self.on_task_change, c=self.c, s=s,
            row_color=row_color, meta=meta, star=star, is_repeat=is_repeat,
            on_delete=self._on_row_deleted, on_star_toggle=self._on_star_toggled
        )
        row.created_seq = created_seq
        row.set_done(done)
        self.tasks.append(row)

        if self._matches_filter(row):
            row.show()
        else:
            row.hide()

    def _on_row_deleted(self, row):
        try:
            self.tasks.remove(row)
        except ValueError:
            pass
        self.save(silent=True)
        self._refresh_view()

    def _on_star_toggled(self, _row, _state):
        self.save(silent=True)
        self._refresh_view()

    def on_task_change(self):
        self.save(silent=True)

    def remove_done(self):
        for r in list(self.tasks):
            if r.is_done():
                r.destroy()  # TaskRow.destroy wywoła _on_row_deleted
        self.save(silent=True)
        self._refresh_view()

    def clear_all(self):
        for r in list(self.tasks):
            r.destroy()
        self.tasks.clear()
        self.save(silent=True)
        self._refresh_view()

    # ================== Zapis / wczytanie ==================
    def save(self, silent=True):
        """
        ZBIERA dane z TaskRow i:
          1) zapisuje je do bazy SQLite (db.save_all)
          2) dodatkowo zapisuje JSON (PLIK) jako backup (tak jak wcześniej)
        """
        data = [{
            "text": r.get_text(),
            "done": r.is_done(),
            "cat": r.get_cat(),
            "meta": r.get_meta(),
            "star": r.get_starred(),
            "created_seq": r.created_seq,
            "rep": r.get_is_repeat(),
        } for r in self.tasks]

        # zapis do SQLite
        db.save_all(data)

        # dodatkowy zapis do JSON – żebyś miała kopię tak jak wcześniej
        tmp = PLIK + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, PLIK)

    def load(self, silent=False):
        """
        Próbuje wczytać z bazy SQLite.
        Jeśli w bazie nie ma jeszcze zadań – próbuje wczytać z JSON (PLIK),
        a potem przy następnym zapisie dane trafią już do bazy.
        """
        # 1) Najpierw spróbuj z bazy
        data = db.load_all()

        # 2) Jeśli w bazie pusto – spróbuj z JSON (stara wersja)
        if not data:
            try:
                with open(PLIK, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = []

        if not data:
            return

        for r in list(self.tasks):
            r.destroy()
        self.tasks.clear()

        max_seq = -1
        for item in data:
            created_seq = item.get("created_seq")
            if isinstance(created_seq, int):
                max_seq = max(max_seq, created_seq)
            self._add_row(
                item.get("text", ""),
                done=bool(item.get("done", False)),
                cat=item.get("cat", "Inne"),
                meta=item.get("meta"),
                star=bool(item.get("star", False)),
                created_seq=created_seq,
                is_repeat=bool(item.get("rep", False)),
            )
        self._seq = max_seq + 1 if max_seq >= 0 else len(self.tasks)
        self._refresh_view()

    def exit_app(self):
        self.save()
        self.root.destroy()
