import cv2
import numpy as np
import subprocess
import time
import random

ADB = r"C:\adb\adb.exe"

PACKAGE_NAME = "com.RayGaming.SeaExplorer"
ad_counter = 0
AD_THRESHOLD = 4

# -------- PATHS --------
TAP_PATH = r"D:\programs\seaExploere\assets\tap.png"
SPIN_BTN_PATH = r"D:\programs\seaExploere\assets\spin_button.png"
SPIN_CUT_PATH = r"D:\programs\seaExploere\assets\spin_cut.png"
PRIZE_PATH = r"D:\programs\seaExploere\assets\prize.png"
BACK_PATH = r"D:\programs\seaExploere\assets\back.png"

GAME_OBJ_PATHS = [
    rf"D:\programs\seaExploere\gameObjects\gameObj{i}.png"
    for i in range(1,39)
]

print("\n😈 ADS SKIP DEAMON STARTING 😈\n")

# -------- STATE --------
swiping = False
wait_for_tap = False
last_swipe_time = 0
last_direction = None

# -------- SCREENSHOT --------
def screenshot():
    result = subprocess.run([ADB, "exec-out", "screencap", "-p"], stdout=subprocess.PIPE)
    img = np.frombuffer(result.stdout, np.uint8)
    return cv2.imdecode(img, cv2.IMREAD_COLOR)

# -------- TAP --------
def tap(x, y):
    print(f"👉 TAP ACTION at ({x},{y})")
    subprocess.run([ADB, "shell", "input", "tap", str(x), str(y)])

# -------- LOAD --------
def load_gray(path):
    img = cv2.imread(path)
    if img is None:
        print(f"❌ ERROR: Missing file -> {path}")
        exit()
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

tap_template = load_gray(TAP_PATH)
spin_btn = load_gray(SPIN_BTN_PATH)
spin_cut = load_gray(SPIN_CUT_PATH)
prize_tmp = load_gray(PRIZE_PATH)
back_tmp = load_gray(BACK_PATH)
reward_templates = [load_gray(p) for p in GAME_OBJ_PATHS]

th, tw = tap_template.shape[:2]

# -------- MATCH --------
def match(gray, template):
    result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
    _, val, _, loc = cv2.minMaxLoc(result)
    return val, loc

# -------- REWARD --------
def reward_score(gray):
    best = 0
    for temp in reward_templates:
        val, _ = match(gray, temp)
        best = max(best, val)
    return best

# -------- SWIPE --------
def smart_swipe(w, h):
    global last_direction

    y = int(h * 0.7)

    if last_direction == "left":
        direction = "right"
    elif last_direction == "right":
        direction = "left"
    else:
        direction = random.choice(["left", "right"])

    if direction == "left":
        x1, x2 = int(w*0.6), int(w*0.2)
    else:
        x1, x2 = int(w*0.4), int(w*0.8)

    print(f"👉 SWIPE {direction.upper()}")

    subprocess.run([ADB, "shell", "input", "swipe",
                    str(x1), str(y), str(x2), str(y), "120"])

    last_direction = direction

# -------- RESTART --------
def restart_game():
    print("🚨 AD DETECTED → CLOSING GAME")

    subprocess.run([ADB, "shell", "am", "force-stop", PACKAGE_NAME])
    print("⏳ Waiting after close...")
    time.sleep(2)

    print("🚀 Re-opening game...")
    subprocess.run([
        ADB, "shell", "monkey",
        "-p", PACKAGE_NAME,
        "-c", "android.intent.category.LAUNCHER", "1"
    ])

    print("⏳ Waiting for game to load...")
    time.sleep(9)

# ================= LOOP =================
while True:

    loop_start = time.time()

    screen = screenshot()
    if screen is None:
        continue

    h, w = screen.shape[:2]
    gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)

    print("\n==============================")

    # -------- DETECTIONS --------
    val_spin, loc_spin = match(gray, spin_btn)
    val_spin_cut, _ = match(gray, spin_cut)
    val_prize, loc_prize = match(gray, prize_tmp)

    zone = screen[int(h*0.45):int(h*0.75), int(w*0.1):int(w*0.9)]
    gray_zone = cv2.cvtColor(zone, cv2.COLOR_BGR2GRAY)

    result = cv2.matchTemplate(gray_zone, tap_template, cv2.TM_CCOEFF_NORMED)
    _, tap_val, _, tap_loc = cv2.minMaxLoc(result)

    reward_val = reward_score(gray)
    reward_visible = reward_val > 0.65

    # -------- CLEAN SINGLE LINE LOG --------
    loop_time = round((time.time()-loop_start)*1000,2)

    print(
        f"⏱{loop_time}ms | "
        f"spin:{round(val_spin,2)} cut:{round(val_spin_cut,2)} | "
        f"prize:{round(val_prize,2)} tap:{round(tap_val,2)} | "
        f"reward:{round(reward_val,2)}"
    )

    # -------- ORIGINAL GAME LOGIC (UNCHANGED) --------
    game_confidence = max(val_spin, val_prize, tap_val)

    is_game = (
        reward_visible or
        tap_val > 0.65 or
        val_spin > 0.85 or
        val_prize > 0.75
    )

    # -------- AD DETECTION (UNCHANGED) --------
    if not is_game:
        ad_counter += 1
        print(f"🚨 AD ({ad_counter}/{AD_THRESHOLD}) conf:{round(game_confidence,2)}")
    else:
        if ad_counter > 0:
            ad_counter -= 1
            print(f"🟢 GAME BACK (counter↓ {ad_counter})")

    # -------- RESTART --------
    if ad_counter >= AD_THRESHOLD:
        restart_game()
        ad_counter = 0
        swiping = False
        wait_for_tap = False
        continue

    # -------- ACTION --------
    action = "IDLE"

    # -------- SPIN --------
    if val_spin > 0.85:
        action = "SPIN"
        print("🎰 SPIN")

        swiping = False
        wait_for_tap = True

        x = loc_spin[0] + spin_btn.shape[1] // 2
        y = loc_spin[1] + spin_btn.shape[0] // 2

        for i in range(6):
            tap(x, y)
            print(f"   ↻ {i+1}/6")
            time.sleep(3)

        print("   🔍 CUT SEARCH")

        for i in range(5):
            screen = screenshot()
            gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)

            val_cut, loc_cut = match(gray, spin_cut)
            print(f"   cut:{round(val_cut,2)}")

            if val_cut > 0.6:
                cx = loc_cut[0] + spin_cut.shape[1] // 2
                cy = loc_cut[1] + spin_cut.shape[0] // 2
                tap(cx, cy)
                print("   ✅ CLOSED")
                break

            time.sleep(0.5)

        continue

    # -------- PRIZE --------
    if val_prize > 0.7:
        action = "PRIZE"
        print("🎁 PRIZE")

        swiping = False
        wait_for_tap = True

        val_back, loc_back = match(gray, back_tmp)

        if val_back > 0.6:
            tap(loc_back[0], loc_back[1])
            print("   🔙 BACK")

        time.sleep(1)
        continue

    # -------- TAP --------
    if tap_val > 0.65:
        action = "TAP"
        print("👆 TAP")

        x = tap_loc[0] + int(w*0.1) + (tw // 2)
        y = tap_loc[1] + int(h*0.45) + (th // 2)

        tap(x, y)

        swiping = True
        wait_for_tap = False
        continue

    # -------- REWARD --------
    if reward_visible and not wait_for_tap:
        action = "SWIPE"
        print("🎮 SWIPE ENABLE")
        swiping = True
    else:
        print("⛔ SWIPE OFF")
        swiping = False

    # -------- SWIPE --------
    if swiping:
        if time.time() - last_swipe_time > 0.3:
            smart_swipe(w, h)
            last_swipe_time = time.time()

    print(f"➡️ ACTION: {action}")

    time.sleep(0.05)