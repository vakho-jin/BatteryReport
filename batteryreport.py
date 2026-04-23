import subprocess
import os
import re
import tkinter as tk
from tkinter import ttk
import threading

def run_battery_report():
    output = os.path.join(os.path.expanduser("~"), "Desktop", "battery.html")
    subprocess.run(["powercfg", "/batteryreport", "/output", output], shell=True)
    return output

def parse_battery_info(html_path):
    try:
        with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except:
        return None

    info = {}

    # საწყისი მოცულობა
    m = re.search(r'DESIGN CAPACITY.*?(\d[\d,]+)\s*mWh', content, re.IGNORECASE | re.DOTALL)
    if m:
        info["design"] = int(m.group(1).replace(",", ""))

    # სრულად დატენილი მოცულობა
    m = re.search(r'FULL CHARGE CAPACITY.*?(\d[\d,]+)\s*mWh', content, re.IGNORECASE | re.DOTALL)
    if m:
        info["full"] = int(m.group(1).replace(",", ""))

    # დატენვის ციკლები
    m = re.search(r'CYCLE COUNT.*?(\d+)', content, re.IGNORECASE | re.DOTALL)
    if m:
        info["cycles"] = m.group(1)

    # ბატარეის სახელი/მწარმოებელი
    m = re.search(r'MANUFACTURER.*?<td[^>]*>(.*?)</td>', content, re.IGNORECASE | re.DOTALL)
    if m:
        info["manufacturer"] = re.sub(r'<[^>]+>', '', m.group(1)).strip()

    # ქიმია
    m = re.search(r'CHEMISTRY.*?<td[^>]*>(.*?)</td>', content, re.IGNORECASE | re.DOTALL)
    if m:
        info["chemistry"] = re.sub(r'<[^>]+>', '', m.group(1)).strip()

    if "design" in info and "full" in info and info["design"] > 0:
        info["health"] = round((info["full"] / info["design"]) * 100, 1)

    return info

def get_health_color(health):
    if health >= 80:
        return "#4ade80", "#166534"   # green
    elif health >= 60:
        return "#facc15", "#713f12"   # yellow
    else:
        return "#f87171", "#7f1d1d"   # red

def get_health_label(health):
    if health >= 80:
        return "კარგი"
    elif health >= 60:
        return "დამაკმაყოფილებელი"
    else:
        return "ცუდი"

class BatteryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ელემენტის სიცოცხლე")
        self.root.geometry("480x560")
        self.root.resizable(False, False)
        self.root.configure(bg="#0f172a")

        self.html_path = None
        self.build_ui()
        self.start_scan()

    def build_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#0f172a")
        header.pack(fill="x", padx=30, pady=(28, 0))

        tk.Label(header, text="⚡", font=("Segoe UI Emoji", 28), bg="#0f172a", fg="#38bdf8").pack(side="left")
        title_frame = tk.Frame(header, bg="#0f172a")
        title_frame.pack(side="left", padx=10)
        tk.Label(title_frame, text="ელემენტის სიცოცხლე", font=("Segoe UI", 18, "bold"),
                 bg="#0f172a", fg="#f1f5f9").pack(anchor="w")
        tk.Label(title_frame, text="აკუმულატორის მდგომარეობის ანალიზი", font=("Segoe UI", 9),
                 bg="#0f172a", fg="#64748b").pack(anchor="w")

        # Divider
        tk.Frame(self.root, bg="#1e293b", height=1).pack(fill="x", padx=30, pady=20)

        # Health circle area
        self.canvas_frame = tk.Frame(self.root, bg="#0f172a")
        self.canvas_frame.pack()

        self.canvas = tk.Canvas(self.canvas_frame, width=180, height=180,
                                bg="#0f172a", highlightthickness=0)
        self.canvas.pack()

        self.health_label = tk.Label(self.root, text="", font=("Segoe UI", 12),
                                     bg="#0f172a", fg="#94a3b8")
        self.health_label.pack(pady=(6, 0))

        # Stats grid
        self.stats_frame = tk.Frame(self.root, bg="#0f172a")
        self.stats_frame.pack(fill="x", padx=30, pady=20)

        self.stat_widgets = {}
        stats = [
            ("design_lbl", "ქარხნული მოცულობა", "design_val"),
            ("full_lbl", "მიმდინარე მოცულობა", "full_val"),
            ("cycles_lbl", "დატენვის ციკლები", "cycles_val"),
            ("chem_lbl", "ქიმია", "chem_val"),
        ]

        for i, (lk, label_text, vk) in enumerate(stats):
            row = i // 2
            col = i % 2
            card = tk.Frame(self.stats_frame, bg="#1e293b", padx=14, pady=12)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            self.stats_frame.columnconfigure(col, weight=1)

            tk.Label(card, text=label_text, font=("Segoe UI", 7, "bold"),
                     bg="#1e293b", fg="#475569").pack(anchor="w")
            val = tk.Label(card, text="—", font=("Segoe UI", 13, "bold"),
                           bg="#1e293b", fg="#e2e8f0")
            val.pack(anchor="w", pady=(4, 0))
            self.stat_widgets[vk] = val

        # Status / button
        self.status_label = tk.Label(self.root, text="ანალიზის დაწყება...",
                                     font=("Segoe UI", 9), bg="#0f172a", fg="#64748b")
        self.status_label.pack(pady=(0, 8))

        self.open_btn = tk.Button(self.root, text="სრული რეპორტის გახსნა",
                                  font=("Segoe UI", 10, "bold"),
                                  bg="#0ea5e9", fg="white", relief="flat",
                                  padx=20, pady=8, cursor="hand2",
                                  command=self.open_report, state="disabled")
        self.open_btn.pack(pady=(0, 20))

    def draw_arc(self, health, color):
        self.canvas.delete("all")
        cx, cy, r = 90, 90, 72
        # Background circle
        self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r,
                                outline="#1e293b", width=12)
        # Arc
        extent = health / 100 * 360
        self.canvas.create_arc(cx-r, cy-r, cx+r, cy+r,
                               start=90, extent=-extent,
                               outline=color, width=12, style="arc")
        # Text
        self.canvas.create_text(cx, cy-10, text=f"{health}%",
                                font=("Segoe UI", 26, "bold"), fill=color)
        self.canvas.create_text(cx, cy+18, text="სიცოცხლე",
                                font=("Segoe UI", 9), fill="#475569")

    def start_scan(self):
        threading.Thread(target=self.scan, daemon=True).start()

    def scan(self):
        self.root.after(0, lambda: self.status_label.config(text="powercfg რეპორტის გენერაცია..."))
        path = run_battery_report()
        self.html_path = path
        info = parse_battery_info(path)
        self.root.after(0, lambda: self.update_ui(info))

    def update_ui(self, info):
        if not info:
            self.status_label.config(text="ვერ მოხერხდა მონაცემების მიღება.")
            return

        if "health" in info:
            color, _ = get_health_color(info["health"])
            label = get_health_label(info["health"])
            self.draw_arc(info["health"], color)
            self.health_label.config(text=f"მდგომარეობა: {label}", fg=color)

        if "design" in info:
            self.stat_widgets["design_val"].config(text=f"{info['design']:,} mWh")
        if "full" in info:
            self.stat_widgets["full_val"].config(text=f"{info['full']:,} mWh")
        if "cycles" in info:
            self.stat_widgets["cycles_val"].config(text=info["cycles"])
        if "chemistry" in info:
            self.stat_widgets["chem_val"].config(text=info.get("chemistry", "—"))

        self.status_label.config(text="რეპორტი შენახულია სამუშაო მაგიდაზე")
        self.open_btn.config(state="normal")

    def open_report(self):
        if self.html_path:
            os.startfile(self.html_path)

if __name__ == "__main__":
    root = tk.Tk()
    app = BatteryApp(root)
    root.mainloop()