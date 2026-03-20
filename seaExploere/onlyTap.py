import cv2
import numpy as np
import subprocess
import time

ADB = r"C:\adb\adb.exe"
TEMPLATE_PATH = r"D:\programs\seaExploere\assets\tap.png"

print("🚀 Stable Bot Started")

def screenshot():
    p = subprocess.Popen(
        [ADB, "exec-out", "screencap", "-p"],
        stdout=subprocess.PIPE
    )
    img = np.frombuffer(p.stdout.read(), np.uint8)
    return cv2.imdecode(img, cv2.IMREAD_COLOR)

def tap(x, y):
    print(f"👉 TAP at ({x},{y})")
    subprocess.run([ADB, "shell", "input", "tap", str(x), str(y)])

template = cv2.imread(TEMPLATE_PATH)
template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
th, tw = template_gray.shape[:2]

while True:

    screen = screenshot()
    h, w = screen.shape[:2]

    zone = screen[int(h*0.45):int(h*0.75), int(w*0.1):int(w*0.9)]
    gray = cv2.cvtColor(zone, cv2.COLOR_BGR2GRAY)

    best_val = 0
    best_loc = None
    best_scale = 1

    for scale in np.linspace(0.8, 1.2, 5):
        resized = cv2.resize(template_gray, None, fx=scale, fy=scale)

        if resized.shape[0] > gray.shape[0] or resized.shape[1] > gray.shape[1]:
            continue

        result = cv2.matchTemplate(gray, resized, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val > best_val:
            best_val = max_val
            best_loc = max_loc
            best_scale = scale

    print("match:", round(best_val, 2))

    if best_val >= 0.65:
        th_scaled = int(th * best_scale)
        tw_scaled = int(tw * best_scale)

        x = best_loc[0] + int(w*0.1) + tw_scaled // 2
        y = best_loc[1] + int(h*0.45) + th_scaled // 2

        print("✅ REAL DETECT")
        tap(x, y)

    else:
        print("❌ No match")

    time.sleep(1)