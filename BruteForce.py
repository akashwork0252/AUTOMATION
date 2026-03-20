import cv2
import numpy as np
import subprocess
import time
import random

ADB = r"C:\adb\adb.exe"

# -------- PATHS --------
TAP_PATH = r"D:\programs\seaExploere\assets\tap.png"
SPIN_BTN_PATH = r"D:\programs\seaExploere\assets\spin_button.png"
SPIN_CUT_PATH = r"D:\programs\seaExploere\assets\spin_cut.png"

DEFAULT_PATH = r"D:\programs\seaExploere\assets\default.png"
PRIZE_PATH = r"D:\programs\seaExploere\assets\prize.png"
BACK_PATH = r"D:\programs\seaExploere\assets\back.png"

# -------- REWARD TEMPLATES --------
REWARD_PATHS = [
    r"D:\programs\seaExploere\assets\reward1.png",
    r"D:\programs\seaExploere\assets\reward2.png",
    r"D:\programs\seaExploere\assets\reward3.png",
    r"D:\programs\seaExploere\assets\reward4.png",
    r"D:\programs\seaExploere\assets\reward5.png",
    r"D:\programs\seaExploere\assets\reward6.png",
    r"D:\programs\seaExploere\assets\reward7.png",
    r"D:\programs\seaExploere\assets\reward8.png",
    r"D:\programs\seaExploere\assets\reward9.png",
    r"D:\programs\seaExploere\assets\reward10.png",
    r"D:\programs\seaExploere\assets\reward11.png",
    r"D:\programs\seaExploere\assets\reward12.png"
]

print("🚀 BOT STARTED")

# -------- GLOBAL --------
swiping = False
spin_confirm = 0
last_swipe_time = 0
last_direction = None

# -------- SCREENSHOT --------
def screenshot():
    result = subprocess.run([ADB, "exec-out", "screencap", "-p"], stdout=subprocess.PIPE)
    img = np.frombuffer(result.stdout, np.uint8)
    return cv2.imdecode(img, cv2.IMREAD_COLOR)

# -------- TAP --------
def tap(x, y):
    subprocess.run([ADB, "shell", "input", "tap", str(x), str(y)])

# -------- LOAD --------
def load_gray(path):
    img = cv2.imread(path)
    if img is None:
        print(f"❌ Missing: {path}")
        exit()
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

tap_template = load_gray(TAP_PATH)
spin_btn = load_gray(SPIN_BTN_PATH)
spin_cut = load_gray(SPIN_CUT_PATH)
default_tmp = load_gray(DEFAULT_PATH)
prize_tmp = load_gray(PRIZE_PATH)
back_tmp = load_gray(BACK_PATH)

# load rewards
game_templates = [load_gray(p) for p in REWARD_PATHS]

th, tw = tap_template.shape[:2]

# -------- MATCH --------
def match(gray, template):
    result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
    _, val, _, loc = cv2.minMaxLoc(result)
    return val, loc

# -------- GAME CHECK --------
def is_game_screen(gray):
    best_val = 0

    for i, temp in enumerate(game_templates):
        val, _ = match(gray, temp)
        if val > best_val:
            best_val = val

    print(f"🎮 GAME SCORE: {round(best_val,2)}")

    return best_val > 0.55

# -------- SMART RANDOM SWIPE --------
def smart_swipe(w, h):
    global last_direction

    y = int(h * 0.7)

    if last_direction == "left":
        choices = ["right", "mid"]
    elif last_direction == "right":
        choices = ["left", "mid"]
    else:
        choices = ["left", "right"]

    direction = random.choice(choices)

    if direction == "left":
        subprocess.run([ADB, "shell", "input", "swipe",
                        str(int(w*0.6)), str(y), str(int(w*0.2)), str(y), "120"])
    elif direction == "right":
        subprocess.run([ADB, "shell", "input", "swipe",
                        str(int(w*0.4)), str(y), str(int(w*0.8)), str(y), "120"])
    else:
        subprocess.run([ADB, "shell", "input", "swipe",
                        str(int(w*0.5)), str(y), str(int(w*0.52)), str(y), "80"])

    print(f"👉 SWIPE: {direction}")
    last_direction = direction

# -------- MAIN LOOP --------
while True:

    screen = screenshot()
    if screen is None:
        continue

    h, w = screen.shape[:2]
    gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)

    print("\n=============================")

    # ---------- DEFAULT ----------
    val_default, _ = match(gray, default_tmp)
    default_visible = val_default > 0.6
    print(f"🎮 DEFAULT: {default_visible} ({round(val_default,2)})")

    # ---------- GAME CHECK ----------
    game_visible = is_game_screen(gray)

    # ---------- PRIZE ----------
    val_prize, _ = match(gray, prize_tmp)
    if val_prize > 0.7:
        print("🎁 PRIZE DETECTED → SWIPE OFF")
        swiping = False

        val_back, loc_back = match(gray, back_tmp)
        if val_back > 0.6:
            tap(loc_back[0], loc_back[1])
            print("🔙 BACK TAP")
            time.sleep(1)

        continue

    # ---------- SPIN ----------
    val_spin, loc_spin = match(gray, spin_btn)

    if val_spin > 0.75:
        spin_confirm += 1
    else:
        spin_confirm = 0

    if spin_confirm >= 2:
        print("🎰 SPIN DETECTED → SWIPE OFF")
        swiping = False

        x = loc_spin[0] + spin_btn.shape[1] // 2
        y = loc_spin[1] + spin_btn.shape[0] // 2

        for i in range(6):
            tap(x, y)
            print(f"spin {i+1}/6")
            time.sleep(3)

        print("🔍 searching spin cut...")
        time.sleep(1)

        for attempt in range(5):
            screen = screenshot()
            gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)

            val_cut, loc_cut = match(gray, spin_cut)
            print(f"spin_cut match: {round(val_cut,2)}")

            if val_cut > 0.6:
                cx = loc_cut[0] + spin_cut.shape[1] // 2
                cy = loc_cut[1] + spin_cut.shape[0] // 2
                tap(cx, cy)
                print(f"✅ spin closed (attempt {attempt+1})")
                break

            time.sleep(0.5)

        spin_confirm = 0
        continue

    # ---------- TAP ----------
    zone = screen[int(h*0.45):int(h*0.75), int(w*0.1):int(w*0.9)]
    gray_zone = cv2.cvtColor(zone, cv2.COLOR_BGR2GRAY)

    result = cv2.matchTemplate(gray_zone, tap_template, cv2.TM_CCOEFF_NORMED)
    _, best_val, _, best_loc = cv2.minMaxLoc(result)

    print(f"🎯 TAP: {round(best_val,2)}")

    if best_val > 0.65:
        print("👆 TAP DETECTED → SWIPE ON")
        swiping = True

        x = best_loc[0] + int(w*0.1) + (tw // 2)
        y = best_loc[1] + int(h*0.45) + (th // 2)
        tap(x, y)

    # ---------- SWIPE ----------
    if swiping and default_visible and game_visible:
        if time.time() - last_swipe_time > 0.3:
            smart_swipe(w, h)
            last_swipe_time = time.time()
    else:
        print("⏸️ SWIPE OFF (reason: default/game/spin/prize)")

    time.sleep(0.05)