# ⚡ Battery Health Monitor

პითონზე დაწერილი Windows-ის აპლიკაცია, რომელიც აჩვენებს ლეპტოპის აკუმულატორის მდგომარეობას გრაფიკული ინტერფეისით.

---

## 📋 ფუნქციები

- 🔋 აკუმულატორის ჯანმრთელობის პროცენტული მაჩვენებელი
- 📊 მრგვალი ინდიკატორი (მწვანე / ყვითელი / წითელი)
- 📁 საინფორმაციო ბარათები:
  - საპროექტო ტევადობა (Design Capacity)
  - მიმდინარე ტევადობა (Full Charge Capacity)
  - დამუხტვის ციკლების რაოდენობა
  - ბატარეის ტიპი
- 📄 სრული HTML ანგარიშის გახსნა პირდაპირ სამუშაო მაგიდიდან

---

## 🖥️ მოთხოვნები

- Windows 10 / 11
- Python 3.8+
- ადმინისტრატორის უფლებები (powercfg-ისთვის)

---

## 🚀 გაშვება

```bash
python BatteryInfo.py
```

---

## 📦 EXE-ად გადაქცევა

**1. დააყენე PyInstaller:**
```bash
python -m pip install pyinstaller
```

**2. შექმენი `.ico` ფაილი (Pillow-ით):**
```bash
python -m pip install Pillow
```
```python
from PIL import Image
img = Image.open("icon.png").convert("RGBA")
img.save("icon.ico", format="ICO", sizes=[
    (16,16),(32,32),(48,48),(64,64),(128,128),(256,256)
])
```

**3. ააგე EXE:**
```bash
python -m PyInstaller --onefile --noconsole --icon="icon.ico" BatteryInfo.py
```

მზა ფაილი იქნება `dist\BatteryInfo.exe`-ში.

---

## 🧠 როგორ მუშაობს

აპლიკაცია იყენებს Windows-ის ჩაშენებულ ბრძანებას:

```
powercfg /BatteryInfo
```

შემდეგ HTML ანგარიშიდან ამოიღებს მნიშვნელობებს და ითვლის:

```
ჯანმრთელობა = (Full Charge Capacity / Design Capacity) × 100%
```

---

## 📊 ჯანმრთელობის შეფასება

| პროცენტი | მდგომარეობა | ფერი |
|----------|-------------|------|
| 80% – 100% | შესანიშნავი | 🟢 მწვანე |
| 60% – 79% | დამაკმაყოფილებელი | 🟡 ყვითელი |
| 0% – 59% | ცუდი | 🔴 წითელი |

---

## 📁 პროექტის სტრუქტურა

```
battery-health-monitor/
├── battery_app.py   # მთავარი სკრიპტი
├── icon.png         # ხატულა (PNG)
├── icon.ico         # ხატულა (ICO)
└── README.md
```

---

## 📜 ლიცენზია

MIT License
