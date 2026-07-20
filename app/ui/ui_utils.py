import re
import tkinter as tk
import calendar
from datetime import date, datetime
from tkinter import ttk, messagebox


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def valid_email(value):
    return not value or EMAIL_RE.match(value)


def valid_phone(value, required=False):
    if not value:
        return not required
    return value.isdigit() and len(value) >= 10


def valid_date(value, required=False):
    if not value:
        return not required
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def selected_id(value):
    if not value:
        return None
    try:
        return int(str(value).split(" - ", 1)[0])
    except ValueError:
        return None


def clear_entries(entries):
    for entry in entries.values():
        if isinstance(entry, ttk.Combobox):
            entry.set("")
        elif isinstance(entry, tk.Listbox):
            entry.selection_clear(0, tk.END)
            entry.delete(0, tk.END)
        else:
            entry.delete(0, tk.END)


def _palette(widget):
    root = widget.winfo_toplevel()
    return getattr(root, "palette", {}) if root is not None else {}


def attach_modern_scrollbar(parent, widget, orient="vertical"):
    style = "Vertical.TScrollbar" if orient == "vertical" else "Horizontal.TScrollbar"
    scrollbar = ttk.Scrollbar(parent, orient=orient, style=style, command=getattr(widget, "yview" if orient == "vertical" else "xview"))
    if orient == "vertical":
        widget.configure(yscrollcommand=scrollbar.set)
    else:
        widget.configure(xscrollcommand=scrollbar.set)
    return scrollbar


def bind_mousewheel(widget, scroll_target):
    def on_mousewheel(event):
        if event.delta:
            scroll_target.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif event.num == 4:
            scroll_target.yview_scroll(-1, "units")
        elif event.num == 5:
            scroll_target.yview_scroll(1, "units")

    widget.bind("<MouseWheel>", on_mousewheel)
    widget.bind("<Button-4>", on_mousewheel)
    widget.bind("<Button-5>", on_mousewheel)


def create_modern_listbox(parent, height=5, selectmode="extended"):
    palette = _palette(parent)
    container = ttk.Frame(parent)
    listbox = tk.Listbox(
        container,
        selectmode=selectmode,
        height=height,
        exportselection=False,
        bg=palette.get("entry", "#E2E8F0"),
        fg=palette.get("entry_text", "#0F172A"),
        selectbackground=palette.get("accent", "#2563EB"),
        selectforeground="#FFFFFF",
        activestyle="none",
        relief="flat",
        highlightthickness=1,
        highlightbackground=palette.get("panel", "#334155"),
        highlightcolor=palette.get("accent", "#2563EB"),
        font=("Segoe UI", 10),
    )
    scrollbar = attach_modern_scrollbar(container, listbox)
    listbox.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    bind_mousewheel(listbox, listbox)
    return container, listbox


def ask_delete():
    return messagebox.askyesno("Confirmation", "Voulez-vous vraiment supprimer cet element ?")


def show_pdf(path):
    if not path:
        return
    messagebox.showinfo("PDF genere", f"Fichier cree :\n{path}")


class FormTableFrame(ttk.Frame):
    """Reusable layout for CRUD tabs."""

    def __init__(self, parent, title):
        super().__init__(parent, padding=22, style="App.TFrame")
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        ttk.Label(self, text=title, style="PageTitle.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
        self.form = ttk.LabelFrame(self, text="Formulaire", padding=14, style="Panel.TLabelframe")
        self.form.grid(row=1, column=0, sticky="nsew", pady=18, padx=(0, 14))
        self.right = ttk.Frame(self, style="App.TFrame")
        self.right.grid(row=1, column=1, sticky="nsew", pady=12)
        self.right.rowconfigure(1, weight=1)
        self.right.columnconfigure(0, weight=1)

    def add_search(self, command, print_command=None, print_text="Imprimer"):
        bar = ttk.Frame(self.right, style="App.TFrame")
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        bar.columnconfigure(0, weight=1)
        self.search_var = tk.StringVar()
        ttk.Entry(bar, textvariable=self.search_var).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(bar, text="🔍 Rechercher", command=command).grid(row=0, column=1, padx=3)
        ttk.Button(bar, text="Afficher tout", command=lambda: command(show_all=True)).grid(row=0, column=2, padx=3)
        if print_command:
            ttk.Button(bar, text=print_text, command=print_command).grid(row=0, column=3, padx=3)

    def add_tree(self, columns, headings, widths):
        container = ttk.Frame(self.right, style="App.TFrame")
        container.grid(row=1, column=0, sticky="nsew")
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(container, columns=columns, show="headings", height=16, selectmode="extended")
        for col, heading, width in zip(columns, headings, widths):
            self.tree.heading(col, text=heading, command=lambda c=col: self.sort_tree(c, False))
            self.tree.column(col, width=width, anchor="w")
        root = self.winfo_toplevel()
        palette = getattr(root, "palette", {}) if root is not None else {}
        odd_bg = palette.get("tree", "#172033")
        even_bg = palette.get("tree_alt", "#1E293B")
        self.tree.tag_configure("odd", background=odd_bg)
        self.tree.tag_configure("even", background=even_bg)
        self.tree.tag_configure("green", foreground="#22C55E")
        self.tree.tag_configure("red", foreground="#EF4444")
        self.tree.tag_configure("yellow", foreground="#FACC15")
        self.tree.tag_configure("blue", foreground="#38BDF8")
        scroll_y = attach_modern_scrollbar(container, self.tree, orient="vertical")
        scroll_x = attach_modern_scrollbar(container, self.tree, orient="horizontal")
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        bind_mousewheel(self.tree, self.tree)
        return self.tree

    def button_row(self, row, buttons):
        frame = ttk.Frame(self.form)
        frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        for text, command in buttons:
            icon = {"Ajouter": "+ ", "Modifier": "✎ ", "Supprimer": "× "}.get(text, "")
            ttk.Button(frame, text=f"{icon}{text}", command=command).pack(side="left", padx=3, pady=2)

    def sort_tree(self, column, reverse):
        data = [(self.tree.set(item, column), item) for item in self.tree.get_children("")]
        try:
            data.sort(key=lambda item: float(item[0]), reverse=reverse)
        except ValueError:
            data.sort(key=lambda item: item[0].lower(), reverse=reverse)
        for index, (_value, item) in enumerate(data):
            self.tree.move(item, "", index)
        self.tree.heading(column, command=lambda: self.sort_tree(column, not reverse))

    def insert_row(self, values, tags=()):
        index = len(self.tree.get_children())
        base_tag = "even" if index % 2 == 0 else "odd"
        return self.tree.insert("", tk.END, values=values, tags=(base_tag, *tags))


class DateTimeEntry(ttk.Frame):
    """Entry with a small built-in calendar popup and optional time selector."""

    def __init__(self, parent, include_time=True, width=22):
        super().__init__(parent)
        self.include_time = include_time
        self.value = tk.StringVar()
        self.selected_date = date.today()
        self.hour_var = tk.StringVar(value=f"{datetime.now().hour:02d}")
        self.minute_var = tk.StringVar(value=f"{datetime.now().minute:02d}")
        self.month = self.selected_date.month
        self.year = self.selected_date.year
        self.entry = ttk.Entry(self, textvariable=self.value, width=width, state="normal")
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<Return>", self._on_focus_out)
        ttk.Button(self, text="...", width=3, command=self.open_calendar).pack(side="left", padx=(4, 0))
        self.set_now()

    def get(self):
        return self.value.get()

    def set(self, value):
        value = str(value).strip()
        if not value:
            self.set_now()
            return
        try:
            if self.include_time:
                parsed = datetime.strptime(value, "%Y-%m-%d %H:%M")
                self.selected_date = parsed.date()
                self.hour_var.set(f"{parsed.hour:02d}")
                self.minute_var.set(f"{parsed.minute:02d}")
            else:
                self.selected_date = datetime.strptime(value, "%Y-%m-%d").date()
            self.month = self.selected_date.month
            self.year = self.selected_date.year
            self._update_text()
        except ValueError:
            self.value.set(value)

    def set_now(self):
        now = datetime.now()
        self.selected_date = now.date()
        self.month = now.month
        self.year = now.year
        if self.include_time:
            self.hour_var.set(f"{now.hour:02d}")
            self.minute_var.set(f"{now.minute:02d}")
        self._update_text()

    def delete(self, *_args):
        self.value.set("")

    def insert(self, _index, value):
        self.set(value)

    def _update_text(self):
        if self.include_time:
            self.value.set(f"{self.selected_date.isoformat()} {self.hour_var.get()}:{self.minute_var.get()}")
        else:
            self.value.set(self.selected_date.isoformat())

    def open_calendar(self):
        self.popup = tk.Toplevel(self)
        self.popup.title("Calendrier")
        self.popup.resizable(False, False)
        self.popup.transient(self.winfo_toplevel())
        self.popup.grab_set()

        self.header = ttk.Frame(self.popup, padding=8)
        self.header.pack(fill="x")
        ttk.Button(self.header, text="<", width=3, command=lambda: self.change_month(-1)).pack(side="left")
        self.title_var = tk.StringVar()
        ttk.Label(self.header, textvariable=self.title_var, width=18, anchor="center").pack(side="left", expand=True)
        ttk.Button(self.header, text=">", width=3, command=lambda: self.change_month(1)).pack(side="left")

        self.days_frame = ttk.Frame(self.popup, padding=(8, 0, 8, 8))
        self.days_frame.pack()

        if self.include_time:
            time_frame = ttk.Frame(self.popup, padding=(8, 0, 8, 8))
            time_frame.pack(fill="x")
            ttk.Label(time_frame, text="Heure").pack(side="left")
            ttk.Spinbox(time_frame, from_=0, to=23, width=4, format="%02.0f", textvariable=self.hour_var).pack(side="left", padx=5)
            ttk.Label(time_frame, text="Minute").pack(side="left")
            ttk.Spinbox(time_frame, from_=0, to=59, width=4, format="%02.0f", textvariable=self.minute_var).pack(side="left", padx=5)

        actions = ttk.Frame(self.popup, padding=(8, 0, 8, 8))
        actions.pack(fill="x")
        ttk.Button(actions, text="Aujourd'hui", command=self.choose_today).pack(side="left")
        ttk.Button(actions, text="Valider", command=self.confirm).pack(side="right")
        self.render_calendar()

    def change_month(self, delta):
        self.month += delta
        if self.month < 1:
            self.month = 12
            self.year -= 1
        elif self.month > 12:
            self.month = 1
            self.year += 1
        self.render_calendar()

    def render_calendar(self):
        for child in self.days_frame.winfo_children():
            child.destroy()
        self.title_var.set(f"{calendar.month_name[self.month]} {self.year}")
        for col, name in enumerate(("Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim")):
            ttk.Label(self.days_frame, text=name, width=5, anchor="center").grid(row=0, column=col, pady=2)
        for row, week in enumerate(calendar.monthcalendar(self.year, self.month), start=1):
            for col, day in enumerate(week):
                if day == 0:
                    ttk.Label(self.days_frame, text="", width=5).grid(row=row, column=col, padx=1, pady=1)
                    continue
                ttk.Button(
                    self.days_frame,
                    text=str(day),
                    width=4,
                    command=lambda d=day: self.choose_day(d),
                ).grid(row=row, column=col, padx=1, pady=1)

    def choose_day(self, day):
        self.selected_date = date(self.year, self.month, day)
        self._update_text()

    def choose_today(self):
        self.set_now()
        self.confirm()

    def _on_focus_out(self, event=None):
        value = self.value.get().strip()
        if not value:
            return
        fmt = "%Y-%m-%d %H:%M" if self.include_time else "%Y-%m-%d"
        try:
            datetime.strptime(value, fmt)
        except ValueError:
            messagebox.showwarning(
                "Format de date",
                f"Le format de date doit etre {'AAAA-MM-JJ HH:MM' if self.include_time else 'AAAA-MM-JJ'}.",
            )
            self.entry.focus_set()

    def confirm(self):
        self._update_text()
        self.popup.destroy()


class DateEntry(DateTimeEntry):
    def __init__(self, parent, width=14):
        super().__init__(parent, include_time=False, width=width)
