import subprocess
import os
import re
import tkinter as tk
from tkinter import messagebox, filedialog
import threading
from datetime import datetime

APP_VERSION = "1.0.0"
APP_AUTHOR  = "ვახტანგ ჯინჭარაძე"
APP_CONTACT = "544 555 008"

def run_battery_report():
    output = os.path.join(os.path.expanduser("~"), "Desktop", "batteryreport.html")
    subprocess.run(["powercfg", "/batteryreport", "/output", output], shell=True)
    return output

def parse_battery_info(html_path):
    try:
        with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except:
        return None
    info = {}
    m = re.search(r'DESIGN CAPACITY.*?(\d[\d,\s\xa0]+)\s*mWh', content, re.IGNORECASE | re.DOTALL)
    if m: info["design"] = int(re.sub(r'[\s,\xa0]+', '', m.group(1)))
    m = re.search(r'FULL CHARGE CAPACITY.*?(\d[\d,\s\xa0]+)\s*mWh', content, re.IGNORECASE | re.DOTALL)
    if m: info["full"] = int(re.sub(r'[\s,\xa0]+', '', m.group(1)))
    m = re.search(r'CYCLE COUNT.*?</td>\s*<td[^>]*>(.*?)</td>', content, re.IGNORECASE | re.DOTALL)
    if m:
        val = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        info["cycles"] = val if val and val != '-' else "—"
    m = re.search(r'MANUFACTURER.*?<td[^>]*>(.*?)</td>', content, re.IGNORECASE | re.DOTALL)
    if m: info["manufacturer"] = re.sub(r'<[^>]+>', '', m.group(1)).strip()
    m = re.search(r'CHEMISTRY.*?<td[^>]*>(.*?)</td>', content, re.IGNORECASE | re.DOTALL)
    if m: info["chemistry"] = re.sub(r'<[^>]+>', '', m.group(1)).strip()
    if "design" in info and "full" in info and info["design"] > 0:
        info["health"] = round((info["full"] / info["design"]) * 100, 1)
    return info

def get_health_color(health):
    if health >= 80: return "#4ade80"
    elif health >= 60: return "#facc15"
    else: return "#f87171"

def get_health_label(health):
    if health >= 80: return "საუკეთესო"
    elif health >= 60: return "საშუალო"
    else: return "ცუდი"

class BatteryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ელემენტის ჯანმრთელობის მონიტორი")
        self.root.geometry("520x630")
        self.root.resizable(False, False)
        self.root.configure(bg="#0f172a")
        self.html_path = None
        self.info = None
        self.build_menu()
        self.build_ui()
        self.start_scan()

    def build_menu(self):
        menubar = tk.Menu(self.root, bg="#1e293b", fg="#f1f5f9",
                          activebackground="#334155", activeforeground="#f1f5f9",
                          relief="flat", bd=0)
        app_menu = tk.Menu(menubar, tearoff=0, bg="#1e293b", fg="#f1f5f9",
                           activebackground="#334155", activeforeground="#f1f5f9")
        app_menu.add_command(label="🔄  მონაცემების განახლება", command=self.start_scan)
        app_menu.add_separator()
        app_menu.add_command(label="❌  გასვლა", command=self.root.quit)
        menubar.add_cascade(label="ფაილი", menu=app_menu)
        help_menu = tk.Menu(menubar, tearoff=0, bg="#1e293b", fg="#f1f5f9",
                            activebackground="#334155", activeforeground="#f1f5f9")
        help_menu.add_command(label="ℹ️  პროგრამის შესახებ", command=self.show_about)
        help_menu.add_command(label="👤  ავტორის შესახებ", command=self.show_author)
        menubar.add_cascade(label="ინფო", menu=help_menu)
        menubar.add_command(label="💖  დონაცია", command=self.show_donation)
        self.root.config(menu=menubar)

    def build_ui(self):
        header = tk.Frame(self.root, bg="#0f172a")
        header.pack(fill="x", padx=20, pady=(20, 0))
        tk.Label(header, text="⚡", font=("Segoe UI Emoji", 24),
                 bg="#0f172a", fg="#38bdf8").pack(side="left")
        tf = tk.Frame(header, bg="#0f172a")
        tf.pack(side="left", padx=15)
        tk.Label(tf, text="ელემენტის ჯანმრთელობა", font=("Segoe UI", 18, "bold"),
                 bg="#0f172a", fg="#f1f5f9").pack(anchor="w")
        tk.Label(tf, text="ელემენტის ჯანმრთელობა", font=("Segoe UI", 9),
                 bg="#0f172a", fg="#64748b").pack(anchor="w")

        tk.Frame(self.root, bg="#1e293b", height=1).pack(fill="x", padx=30, pady=18)

        self.canvas = tk.Canvas(self.root, width=180, height=180,
                                bg="#0f172a", highlightthickness=0)
        self.canvas.pack()

        self.health_label = tk.Label(self.root, text="", font=("Segoe UI", 12),
                                     bg="#0f172a", fg="#94a3b8")
        self.health_label.pack(pady=(6, 0))

        self.stats_frame = tk.Frame(self.root, bg="#0f172a")
        self.stats_frame.pack(fill="x", padx=30, pady=18)

        self.stat_widgets = {}
        stats = [
            ("საწყისი მოცულობა", "design_val"),
            ("მიმდინარე მოცულობა",   "full_val"),
            ("დამუხტვის ციკლები",      "cycles_val"),
            ("ელემენტის ტიპი",             "chem_val"),
        ]
        for i, (label_text, vk) in enumerate(stats):
            row, col = i // 2, i % 2
            card = tk.Frame(self.stats_frame, bg="#1e293b", padx=14, pady=12)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            self.stats_frame.columnconfigure(col, weight=1)
            tk.Label(card, text=label_text, font=("Segoe UI", 7, "bold"),
                     bg="#1e293b", fg="#475569").pack(anchor="w")
            val = tk.Label(card, text="—", font=("Segoe UI", 13, "bold"),
                           bg="#1e293b", fg="#e2e8f0")
            val.pack(anchor="w", pady=(4, 0))
            self.stat_widgets[vk] = val

        self.status_label = tk.Label(self.root, text="ანალიზის დაწყება...",
                                     font=("Segoe UI", 9), bg="#0f172a", fg="#64748b")
        self.status_label.pack(pady=(0, 8))

        btn_frame = tk.Frame(self.root, bg="#0f172a")
        btn_frame.pack(pady=(0, 20))

        self.open_btn = tk.Button(btn_frame, text="📄 სრული რეპორტი",
                                  font=("Segoe UI", 10, "bold"),
                                  bg="#0ea5e9", fg="white", relief="flat",
                                  padx=16, pady=8, cursor="hand2",
                                  command=self.open_report, state="disabled")
        self.open_btn.pack(side="left", padx=6)

        self.save_btn = tk.Button(btn_frame, text="💾 შედეგის შენახვა",
                                  font=("Segoe UI", 10, "bold"),
                                  bg="#6366f1", fg="white", relief="flat",
                                  padx=16, pady=8, cursor="hand2",
                                  command=self.save_result, state="disabled")
        self.save_btn.pack(side="left", padx=6)

    def draw_arc(self, health, color):
        self.canvas.delete("all")
        cx, cy, r = 90, 90, 72
        self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline="#1e293b", width=12)
        extent = health / 100 * 360
        self.canvas.create_arc(cx-r, cy-r, cx+r, cy+r,
                               start=90, extent=-extent,
                               outline=color, width=12, style="arc")
        self.canvas.create_text(cx, cy-10, text=f"{health}%",
                                font=("Segoe UI", 26, "bold"), fill=color)
        self.canvas.create_text(cx, cy+18, text="ჯანმრთელობა",
                                font=("Segoe UI", 9), fill="#475569")

    def start_scan(self):
        self.open_btn.config(state="disabled")
        self.save_btn.config(state="disabled")
        self.canvas.delete("all")
        self.health_label.config(text="")
        for v in self.stat_widgets.values():
            v.config(text="—")
        threading.Thread(target=self.scan, daemon=True).start()

    def scan(self):
        self.root.after(0, lambda: self.status_label.config(text="powercfg რეპორტის გენერაცია..."))
        path = run_battery_report()
        self.html_path = path
        info = parse_battery_info(path)
        self.info = info
        self.root.after(0, lambda: self.update_ui(info))

    def update_ui(self, info):
        if not info:
            self.status_label.config(text="მონაცემების მიღება ვერ მოხერხდა.")
            return
        if "health" in info:
            color = get_health_color(info["health"])
            label = get_health_label(info["health"])
            self.draw_arc(info["health"], color)
            self.health_label.config(text=f"მდგომარეობა: {label}", fg=color)
        if "design"    in info: self.stat_widgets["design_val"].config(text=f"{info['design']:,} mWh")
        if "full"      in info: self.stat_widgets["full_val"].config(text=f"{info['full']:,} mWh")
        if "cycles"    in info: self.stat_widgets["cycles_val"].config(text=info["cycles"])
        if "chemistry" in info: self.stat_widgets["chem_val"].config(text=info["chemistry"])
        self.status_label.config(text="რეპორტი შენახულია სამუშაო მაგიდაზე")
        self.open_btn.config(state="normal")
        self.save_btn.config(state="normal")

    def open_report(self):
        if self.html_path:
            os.startfile(self.html_path)

    def save_result(self):
        if not self.info:
            return
        i = self.info
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            "========================================",
            "        ელემენტის ჯანმრთელობის რეპორტი",
            f"        {now}",
            "========================================",
            f"  ელემენტის ჯანმრთელობა : {i.get('health', '—')}%",
            f"  მდგომარეობა        : {get_health_label(i['health']) if 'health' in i else '—'}",
            f"  საწყისი მოცულობა: {i['design']:,} mWh" if 'design' in i else "  საწყისი მოცულობა: —",
            f"  მიმდინარე მოცულობა: {i['full']:,} mWh"   if 'full'   in i else "  მიმდინარე მოცულობა: —",
            f"  ციკლები             : {i.get('cycles', '—')}",
            f"  ქიმია               : {i.get('chemistry', '—')}",
            f"  მწარმოებელი       : {i.get('manufacturer', '—')}",
            "========================================",
            f"  ელემენტის ჯანმრთელობის მონიტორი v{APP_VERSION}",
            f"  ავტორი: {APP_AUTHOR} — {APP_CONTACT}",
            "========================================",
        ]
        default_name = f"battery-result-{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("ტექსტური ფაილები", "*.txt"), ("ყველა ფაილი", "*.*")],
            initialfile=default_name,
            title="შედეგის შენახვა"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            messagebox.showinfo("შენახულია", f"შედეგი შენახულია:\n{path}")

    def show_about(self):
        win = tk.Toplevel(self.root)
        win.title("პროგრამის შესახებ")
        win.geometry("450x220")
        win.configure(bg="#0f172a")
        win.resizable(False, False)
        win.grab_set()
        tk.Label(win, text="⚡ ელემენტის ჯანმრთელობის მონიტორი", font=("Segoe UI", 14, "bold"),
                 bg="#0f172a", fg="#f1f5f9").pack(pady=(24, 4))
        tk.Label(win, text=f"ვერსია {APP_VERSION}", font=("Segoe UI", 10),
                 bg="#0f172a", fg="#64748b").pack()
        tk.Frame(win, bg="#1e293b", height=1).pack(fill="x", padx=30, pady=14)
        tk.Label(win, text="ელემენტის ჯანმრთელობის ანალიზი\npowercfg /batteryreport-ის საფუძველზე",
                 font=("Segoe UI", 9), bg="#0f172a", fg="#94a3b8", justify="center").pack()
        tk.Button(win, text="დახურვა", font=("Segoe UI", 9, "bold"),
                  bg="#334155", fg="white", relief="flat", padx=16, pady=6,
                  cursor="hand2", command=win.destroy).pack(pady=16)

    def show_author(self):
        win = tk.Toplevel(self.root)
        win.title("ავტორის შესახებ")
        win.geometry("320x230")
        win.configure(bg="#0f172a")
        win.resizable(False, False)
        win.grab_set()
        tk.Label(win, text="👤 ავტორის შესახებ", font=("Segoe UI", 14, "bold"),
                 bg="#0f172a", fg="#f1f5f9").pack(pady=(24, 4))
        tk.Frame(win, bg="#1e293b", height=1).pack(fill="x", padx=30, pady=12)
        info_frame = tk.Frame(win, bg="#0f172a")
        info_frame.pack()
        tk.Label(info_frame, text=APP_AUTHOR, font=("Segoe UI", 12, "bold"),
                 bg="#0f172a", fg="#e2e8f0").pack(pady=(0, 4))
        tk.Label(info_frame, text="ბექენდ დეველოპერი", font=("Segoe UI", 10),
                 bg="#0f172a", fg="#94a3b8").pack(pady=2)
        tk.Label(info_frame, text="სისტემური ადმინისტრატორი", font=("Segoe UI", 10),
                 bg="#0f172a", fg="#94a3b8").pack(pady=2)
        tk.Button(win, text="დახურვა", font=("Segoe UI", 9, "bold"),
                  bg="#334155", fg="white", relief="flat", padx=16, pady=6,
                  cursor="hand2", command=win.destroy).pack(pady=14)

    def show_donation(self):
        win = tk.Toplevel(self.root)
        win.title("დონაცია")
        win.geometry("340x270")
        win.configure(bg="#0f172a")
        win.resizable(False, False)
        win.grab_set()
        tk.Label(win, text="💖 დონაცია", font=("Segoe UI", 14, "bold"),
                 bg="#0f172a", fg="#f1f5f9").pack(pady=(24, 4))
        tk.Frame(win, bg="#1e293b", height=1).pack(fill="x", padx=30, pady=12)
        tk.Label(win, text="თუ მოგეწონათ პროგრამა,\nშეგიძლიათ მხარი დაუჭიროთ ავტორს:",
                 font=("Segoe UI", 9), bg="#0f172a", fg="#94a3b8", justify="center").pack()
        
        info_frame = tk.Frame(win, bg="#0f172a")
        info_frame.pack(pady=10)
        
        def copy_text(text):
            win.clipboard_clear()
            win.clipboard_append(text)

        def show_popup(event, text):
            m = tk.Menu(win, tearoff=0, bg="#1e293b", fg="#f1f5f9", activebackground="#334155", activeforeground="#f1f5f9")
            m.add_command(label="კოპირება", command=lambda: copy_text(text))
            m.tk_popup(event.x_root, event.y_root)
        
        for lbl, val in [
            ("ბანკი:", "საქართველოს ბანკი"),
            ("კოდი:", "BAGAGE22"),
            ("სახელი:", "ჯინჭარაძე ვახტანგ"),
            ("ანგარიში:", "GE50BG0000000345423700"),
        ]:
            row = tk.Frame(info_frame, bg="#0f172a")
            row.pack(anchor="w", pady=1)
            tk.Label(row, text=lbl, font=("Segoe UI", 9), bg="#0f172a", fg="#94a3b8", width=10, anchor="w").pack(side="left")
            entry = tk.Entry(row, font=("Segoe UI", 9, "bold"), bg="#0f172a", fg="#4ade80", 
                             bd=0, highlightthickness=0, readonlybackground="#0f172a", width=len(val) + 2)
            entry.insert(0, val)
            entry.config(state="readonly")
            entry.pack(side="left")
            entry.bind("<Button-3>", lambda e, text=val: show_popup(e, text))

        tk.Button(win, text="დახურვა", font=("Segoe UI", 9, "bold"),
                  bg="#334155", fg="white", relief="flat", padx=16, pady=6,
                  cursor="hand2", command=win.destroy).pack(pady=(5, 10))

if __name__ == "__main__":
    root = tk.Tk()
    app = BatteryApp(root)
    root.mainloop()