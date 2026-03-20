import cv2
import numpy as np
import subprocess
import time

ADB = r"C:\adb\adb.exe"

PACKAGE_NAME = "com.RayGaming.SeaExplorer"
ad_counter = 0
AD_THRESHOLD = 4

# -------- PATHS --------
TAP_PATH = r"D:\programs\seaExploere\assets\tap.png"
SPIN_BTN_PATH = r"D:\programs\seaExploere\assets\spin_button.png"
PRIZE_PATH = r"D:\programs\seaExploere\assets\prize.png"
BACK_PATH = r"D:\programs\seaExploere\assets\back.png"

ENEMY_PATHS = [
    r"D:\programs\seaExploere\assets\shrimp.png",
    r"D:\programs\seaExploere\assets\shrimp2.png"
]

REWARD_AI_PATHS = [
    rf"D:\programs\seaExploere\assets\reward{i}.png"
    for i in range(1,31)
]

print("\n😈 STABLE BOT STARTED 😈\n")

# -------- STATE --------
swiping = False
last_direction = None

# -------- SAFE SCREENSHOT --------
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
        print(f"Missing {path}")
        exit()
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

tap_template = load_gray(TAP_PATH)
spin_btn = load_gray(SPIN_BTN_PATH)
prize_tmp = load_gray(PRIZE_PATH)
back_tmp = load_gray(BACK_PATH)

enemy_templates = [load_gray(p) for p in ENEMY_PATHS]
reward_ai_templates = [load_gray(p) for p in REWARD_AI_PATHS]

# -------- MATCH --------
def match(gray, template):
    result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
    _, val, _, loc = cv2.minMaxLoc(result)
    return val, loc

# -------- DETECT FAST --------
def detect_fast(gray, templates):
    best_val = 0
    best_loc = None
    for temp in templates:
        val, loc = match(gray, temp)
        if val > best_val:
            best_val = val
            best_loc = loc
    return best_val, best_loc

# ================= LOOP =================
while True:

    start = time.time()
    action = "IDLE"

    screen = screenshot()
    if screen is None:
        continue

    h, w = screen.shape[:2]

    # -------- FULL SCREEN --------
    gray_full = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)

    val_spin, loc_spin = match(gray_full, spin_btn)
    val_prize, loc_prize = match(gray_full, prize_tmp)
    val_back, loc_back = match(gray_full, back_tmp)

    result = cv2.matchTemplate(gray_full, tap_template, cv2.TM_CCOEFF_NORMED)
    _, tap_val, _, tap_loc = cv2.minMaxLoc(result)

    # -------- ROI --------
    roi = screen[int(h*0.25):int(h*0.75), int(w*0.15):int(w*0.85)]
    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    offset_x = int(w*0.15)
    offset_y = int(h*0.25)

    reward_visible = val_prize > 0.7

    # -------- AD --------
    is_game = reward_visible or tap_val > 0.7 or val_spin > 0.85

    if not is_game:
        ad_counter += 1
    else:
        ad_counter = max(0, ad_counter - 1)

    if ad_counter >= AD_THRESHOLD:
        action = "RESTART"
        subprocess.run([ADB, "shell", "am", "force-stop", PACKAGE_NAME])
        time.sleep(2)
        ad_counter = 0
        continue

    # -------- SPIN --------
    if val_spin > 0.85:
        action = "SPIN"
        for _ in range(6):
            tap(loc_spin[0], loc_spin[1])
            time.sleep(2)
        continue

    # -------- PRIZE --------
    if val_prize > 0.75:
        action = "PRIZE"
        if val_back > 0.6:
            tap(loc_back[0], loc_back[1])
        continue

    # -------- TAP --------
    if tap_val > 0.7:
        action = "TAP"
        tap(tap_loc[0], tap_loc[1])
        swiping = True
        continue

    # -------- AI SWIPE --------
    if reward_visible:

        enemy_val, enemy_loc = detect_fast(gray_roi, enemy_templates)
        reward_val, reward_loc = detect_fast(gray_roi, reward_ai_templates)

        center_x = gray_roi.shape[1] // 2

        if enemy_val > 0.6:
            decision = "right" if enemy_loc[0] < center_x else "left"
            action = f"ENEMY {decision}"

        elif reward_val > 0.65:
            decision = "left" if reward_loc[0] < center_x else "right"
            action = f"REWARD {decision}"

        else:
            decision = "left" if last_direction != "left" else "right"
            action = "SEARCH"

        y = int(h * 0.7)

        if decision == "left":
            x1, x2 = int(w*0.6), int(w*0.2)
        else:
            x1, x2 = int(w*0.4), int(w*0.8)

        subprocess.run([ADB, "shell", "input", "swipe",
                        str(x1), str(y), str(x2), str(y), "60"])

        last_direction = decision

    # -------- LOG --------
    loop_time = round((time.time() - start)*1000,1)
    print(f"[{loop_time}ms] s:{round(val_spin,2)} p:{round(val_prize,2)} t:{round(tap_val,2)} | {action}")

    time.sleep(0.02)