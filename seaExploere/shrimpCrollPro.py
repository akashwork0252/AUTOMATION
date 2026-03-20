import cv2
import numpy as np
import subprocess
import time

ADB = r"C:\adb\adb.exe"

# -------- PATHS --------
TAP_PATH = r"D:\programs\seaExploere\assets\tap.png"
SPIN_BTN_PATH = r"D:\programs\seaExploere\assets\spin_button.png"
SPIN_CUT_PATH = r"D:\programs\seaExploere\assets\spin_cut.png"
SHRIMP1_PATH = r"D:\programs\seaExploere\assets\shrimp.png"
SHRIMP2_PATH = r"D:\programs\seaExploere\assets\shrimp2.png"

print("🚀 FINAL AI BOT STARTED")

# -------- GLOBAL --------
diver_x = None
last_move_time = 0
MOVE_DELAY = 0.3
spin_confirm = 0

# -------- SCREENSHOT --------
def screenshot():
    result = subprocess.run(
        [ADB, "exec-out", "screencap", "-p"],
        stdout=subprocess.PIPE
    )
    img = np.frombuffer(result.stdout, np.uint8)
    return cv2.imdecode(img, cv2.IMREAD_COLOR)

# -------- TAP --------
def tap(x, y):
    subprocess.run([ADB, "shell", "input", "tap", str(x), str(y)])

# -------- LOAD TEMPLATE --------
def load_gray(path):
    img = cv2.imread(path)
    if img is None:
        print(f"❌ Missing file: {path}")
        exit()
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

tap_template = load_gray(TAP_PATH)
spin_btn = load_gray(SPIN_BTN_PATH)
spin_cut = load_gray(SPIN_CUT_PATH)
shrimp1 = load_gray(SHRIMP1_PATH)
shrimp2 = load_gray(SHRIMP2_PATH)

th, tw = tap_template.shape[:2]

# -------- MULTI MATCH (ENEMY ONLY) --------
def multi_match(gray, template):
    best_val = 0
    best_loc = None

    for scale in np.linspace(0.7, 1.3, 6):
        resized = cv2.resize(template, None, fx=scale, fy=scale)

        if resized.shape[0] > gray.shape[0] or resized.shape[1] > gray.shape[1]:
            continue

        result = cv2.matchTemplate(gray, resized, cv2.TM_CCOEFF_NORMED)
        _, val, _, loc = cv2.minMaxLoc(result)

        if val > best_val:
            best_val = val
            best_loc = loc

    return best_val, best_loc

# -------- SIMPLE MATCH --------
def match(gray, template):
    result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
    _, val, _, loc = cv2.minMaxLoc(result)
    return val, loc

# -------- SWIPE --------
def swipe_left(w, h):
    global diver_x, last_move_time

    if time.time() - last_move_time < MOVE_DELAY:
        return

    y = int(h * 0.7)
    subprocess.run([ADB, "shell", "input", "swipe",
                    str(int(w*0.7)), str(y), str(int(w*0.3)), str(y), "300"])

    print("⬅️ LEFT SWIPE")
    diver_x -= int(w * 0.2)
    diver_x = max(0, diver_x)
    last_move_time = time.time()


def swipe_right(w, h):
    global diver_x, last_move_time

    if time.time() - last_move_time < MOVE_DELAY:
        return

    y = int(h * 0.7)
    subprocess.run([ADB, "shell", "input", "swipe",
                    str(int(w*0.3)), str(y), str(int(w*0.7)), str(y), "300"])

    print("➡️ RIGHT SWIPE")
    diver_x += int(w * 0.2)
    diver_x = min(w, diver_x)
    last_move_time = time.time()

    

# -------- MAIN LOOP --------
while True:

    screen = screenshot()
    if screen is None:
        continue

    h, w = screen.shape[:2]

    roi = screen[int(h*0.2):int(h*0.9), :]
    gray_full = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    if diver_x is None:
        diver_x = w // 2

    print("\n-----------------------------")

    # =====================================================
    # 🐙 ENEMY AI
    # =====================================================
    val1, loc1 = multi_match(gray_full, shrimp1)
    val2, loc2 = multi_match(gray_full, shrimp2)

    if val1 > val2:
        val_enemy = val1
        loc_enemy = loc1
    else:
        val_enemy = val2
        loc_enemy = loc2

    print(f"🎯 ENEMY MATCH: {round(val_enemy,2)}")

    if val_enemy >= 0.6:

        enemy_x = loc_enemy[0] + shrimp1.shape[1] // 2
        enemy_y = loc_enemy[1] + int(h * 0.2)

        print(f"🚨 Enemy {enemy_x} | Diver {diver_x}")

        if enemy_y > int(h * 0.3):

            if abs(enemy_x - diver_x) < int(w * 0.25):

                if enemy_x < diver_x:
                    swipe_right(w, h)
                else:
                    swipe_left(w, h)

                continue
    else:
        print("✅ SAFE")

    # =====================================================
    # 🎰 SPIN (FIXED)
    # =====================================================
    val_btn, loc_btn = match(gray_full, spin_btn)

    print(f"🎰 SPIN MATCH: {round(val_btn,2)}")

    if val_btn >= 0.75 and loc_btn[1] > int(gray_full.shape[0] * 0.5):
        spin_confirm += 1
    else:
        spin_confirm = 0

    if spin_confirm >= 2:
        print("🎰 REAL SPIN DETECTED")

        x = loc_btn[0] + spin_btn.shape[1] // 2
        y = loc_btn[1] + spin_btn.shape[0] // 2 + int(h*0.2)

        for i in range(5):
            tap(x, y)
            print(f"spin {i+1}/5")
            time.sleep(2)

        screen = screenshot()
        gray_full = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)

        val_cut, loc_cut = match(gray_full, spin_cut)

        if val_cut >= 0.6:
            x = loc_cut[0] + spin_cut.shape[1] // 2
            y = loc_cut[1] + spin_cut.shape[0] // 2
            tap(x, y)

        spin_confirm = 0
        continue

    # =====================================================
    # 👇 TAP
    # =====================================================
    zone = screen[int(h*0.45):int(h*0.75), int(w*0.1):int(w*0.9)]
    gray = cv2.cvtColor(zone, cv2.COLOR_BGR2GRAY)

    best_val = 0
    best_loc = None

    for scale in np.linspace(0.8, 1.2, 5):
        resized = cv2.resize(tap_template, None, fx=scale, fy=scale)

        if resized.shape[0] > gray.shape[0] or resized.shape[1] > gray.shape[1]:
            continue

        result = cv2.matchTemplate(gray, resized, cv2.TM_CCOEFF_NORMED)
        _, val, _, loc = cv2.minMaxLoc(result)

        if val > best_val:
            best_val = val
            best_loc = loc

    print(f"🎯 TAP MATCH: {round(best_val,2)}")

    if best_val >= 0.65:
        x = best_loc[0] + int(w*0.1) + (tw // 2)
        y = best_loc[1] + int(h*0.45) + (th // 2)
        tap(x, y)

    time.sleep(0.1)