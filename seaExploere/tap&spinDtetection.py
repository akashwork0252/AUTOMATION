import cv2
import numpy as np
import subprocess
import time

ADB = r"C:\adb\adb.exe"

# -------- TEMPLATES --------
TAP_PATH = r"D:\programs\seaExploere\assets\tap.png"
SPIN_TEXT_PATH = r"D:\programs\seaExploere\assets\spin.png"
SPIN_BTN_PATH = r"D:\programs\seaExploere\assets\spin_button.png"
SPIN_CUT_PATH = r"D:\programs\seaExploere\assets\spin_cut.png"

print("🚀 FINAL COMBINED BOT STARTED")

# -------- SCREENSHOT --------
def screenshot():
    p = subprocess.Popen(
        [ADB, "exec-out", "screencap", "-p"],
        stdout=subprocess.PIPE
    )
    img = np.frombuffer(p.stdout.read(), np.uint8)
    return cv2.imdecode(img, cv2.IMREAD_COLOR)

# -------- TAP --------
def tap(x, y):
    print(f"👉 TAP at ({x},{y})")
    subprocess.run([ADB, "shell", "input", "tap", str(x), str(y)])

# -------- LOAD TEMPLATE --------
def load_gray(path):
    img = cv2.imread(path)
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

tap_template = load_gray(TAP_PATH)
spin_text = load_gray(SPIN_TEXT_PATH)
spin_btn = load_gray(SPIN_BTN_PATH)
spin_cut = load_gray(SPIN_CUT_PATH)

th, tw = tap_template.shape[:2]

# -------- MATCH FUNCTION --------
def match(screen_gray, template):
    result = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    return max_val, max_loc

# -------- MAIN LOOP --------
while True:

    screen = screenshot()
    h, w = screen.shape[:2]
    gray_full = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)

    # =====================================================
    # 🔥 1. SPIN FLOW (HIGH PRIORITY)
    # =====================================================
    val_btn, loc_btn = match(gray_full, spin_btn)
    print("spin button detect:", round(val_btn, 2))

    if val_btn >= 0.7 and loc_btn[1] > int(h*0.5):
        print("🎰 SPIN SCREEN CONFIRMED")

        # ---- BUTTON FIND ----
        val_btn, loc_btn = match(gray_full, spin_btn)

        if val_btn >= 0.6:
            x = loc_btn[0] + spin_btn.shape[1] // 2
            y = loc_btn[1] + spin_btn.shape[0] // 2

            print("🔁 CLICKING SPIN BUTTON 6 TIMES")

            for i in range(6):
                tap(x, y)
                print(f"click {i+1}/5")
                time.sleep(4)

        else:
            print("❌ Spin button not found")

        # ---- CUT BUTTON ----
        time.sleep(2)
        screen = screenshot()
        gray_full = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)

        val_cut, loc_cut = match(gray_full, spin_cut)

        if val_cut >= 0.6:
            x = loc_cut[0] + spin_cut.shape[1] // 2
            y = loc_cut[1] + spin_cut.shape[0] // 2

            print("❌ CLOSING SPIN")
            tap(x, y)

        else:
            print("❌ Cut not found")

        continue  # 👉 IMPORTANT (tap logic skip karega)

    # =====================================================
    # 🔥 2. NORMAL TAP LOGIC (TERA ORIGINAL)
    # =====================================================
    zone = screen[int(h*0.45):int(h*0.75), int(w*0.1):int(w*0.9)]
    gray = cv2.cvtColor(zone, cv2.COLOR_BGR2GRAY)

    best_val = 0
    best_loc = None
    best_scale = 1

    for scale in np.linspace(0.8, 1.2, 5):
        resized = cv2.resize(tap_template, None, fx=scale, fy=scale)

        if resized.shape[0] > gray.shape[0] or resized.shape[1] > gray.shape[1]:
            continue

        result = cv2.matchTemplate(gray, resized, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val > best_val:
            best_val = max_val
            best_loc = max_loc
            best_scale = scale

    print("tap match:", round(best_val, 2))

    if best_val >= 0.65:
        th_scaled = int(th * best_scale)
        tw_scaled = int(tw * best_scale)

        x = best_loc[0] + int(w*0.1) + tw_scaled // 2
        y = best_loc[1] + int(h*0.45) + th_scaled // 2

        print("✅ TAP DETECTED")
        tap(x, y)

    else:
        print("❌ No tap match")

    time.sleep(1)