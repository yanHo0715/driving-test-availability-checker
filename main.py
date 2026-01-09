import time
import platform
import threading
import pyautogui
from PIL import ImageGrab, ImageChops
import tkinter as tk
import pytesseract
import random
from datetime import datetime
import re
import requests
import queue

# --- CONFIG ---
WAIT_AFTER_CLICK = 1.5       # seconds after clicking button
# REFRESH_INTERVAL = 60      # seconds between checks
REFRESH_INTERVAL_MIN = 120   # 2 minutes
REFRESH_INTERVAL_MAX = 300   # 4 minutes
ALARM_REPEAT_INTERVAL = 1  # seconds between repeated beeps

NTFY_TOPIC = "dvsa-alert-8f2a9c87cls"
# initial_image = None

def stop_alarm():
    """Stop the current alarm."""
    alarm_stop_event.set()
    print(f"🔕 Alarm stopped")
    log(f"🔕 Alarm stopped")

def wake_up():
    print(f"⚡ Wake-up requested by user")
    log(f"⚡ Wake-up requested by user")
    wake_event.set()

def end_program():
    print(f"🛑 Ending program...")
    log(f"🛑 Ending program...")
    program_stop_event.set()
    alarm_stop_event.set()
    root.destroy()

# --- GUI for Stop Alarm button ---
root = tk.Tk()
root.withdraw()
root.title("DVSA Control Panel")
root.attributes("-topmost", True)

main_frame = tk.Frame(root)
main_frame.pack(padx=10, pady=10)

# --- LEFT: Log box ---
log_frame = tk.Frame(main_frame)
log_frame.pack(side="left", padx=10)

log_text = tk.Text(
    log_frame,
    width=70,
    height=18,
    state="disabled",
    wrap="word"
)
log_text.pack(side="left")

scrollbar = tk.Scrollbar(log_frame, command=log_text.yview)
scrollbar.pack(side="right", fill="y")
log_text.config(yscrollcommand=scrollbar.set)

# --- RIGHT: Buttons ---
button_frame = tk.Frame(main_frame)
button_frame.pack(side="right", padx=10)

tk.Button(
    button_frame,
    text="🔕 Stop Alarm",
    font=("Arial", 12),
    bg="orange",
    command=stop_alarm
).pack(fill="x", pady=5)

tk.Button(
    button_frame,
    text="⚡ Wake Up",
    font=("Arial", 12),
    bg="green",
    fg="white",
    command=wake_up
).pack(fill="x", pady=5)

tk.Button(
    button_frame,
    text="❌ End Program",
    font=("Arial", 12),
    bg="red",
    fg="white",
    command=end_program
).pack(fill="x", pady=5)

# --- Alarm control ---
alarm_stop_event = threading.Event()
alarm_thread = None  # to track the alarm thread

program_stop_event = threading.Event()
wake_event = threading.Event()

log_queue = queue.Queue()


def log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_queue.put(f"[{timestamp}] {message}")

def update_log_box():
    while not log_queue.empty():
        message = log_queue.get()
        log_text.config(state="normal")
        log_text.insert("end", message + "\n")
        log_text.see("end")
        log_text.config(state="disabled")
    root.after(200, update_log_box)

def hide_control_window():
    root.attributes("-topmost", False)
    root.withdraw()

def show_control_window():
    root.deiconify()
    root.attributes("-topmost", True)

def play_sound_alert():
    """Beep until alarm_stop_event is set."""
    if platform.system() == "Windows":
        import winsound
        duration = 1000
        freq = 1000
        while not alarm_stop_event.is_set():
            winsound.Beep(freq, duration)
            time.sleep(ALARM_REPEAT_INTERVAL)
    else:
        while not alarm_stop_event.is_set():
            print("\a")
            time.sleep(ALARM_REPEAT_INTERVAL)

def play_alarm_thread():
    """Start the alarm in a new thread if none is running."""
    global alarm_thread
    if alarm_thread is None or not alarm_thread.is_alive():
        alarm_stop_event.clear()
        alarm_thread = threading.Thread(target=play_sound_alert, daemon=True)
        alarm_thread.start()
        print(f"Alarm Started!")
        log(f"Alarm Started!")

def send_phone_alert(message):
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=message.encode("utf-8")
    )
    print(f"Alarm Sent!")
    log(f"Alarm Sent!")


# --- GUI for selecting areas ---
class RectSelector(tk.Tk):
    def __init__(self, title="Select area"):
        super().__init__()
        self.title(title)
        self.attributes("-alpha", 0.3)
        self.attributes("-fullscreen", True)
        self.canvas = tk.Canvas(self, cursor="cross")
        self.canvas.pack(fill="both", expand=True)
        self.start_x = self.start_y = 0
        self.rect = None
        self.selected_area = None

        self.canvas.bind("<Button-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.wait_window(self)

    def on_button_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red", width=2)

    def on_drag(self, event):
        curX, curY = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, curX, curY)

    def on_release(self, event):
        end_x, end_y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        self.selected_area = (int(self.start_x), int(self.start_y), int(end_x), int(end_y))
        self.destroy()

# --- Select button area ---
print(f"Select the button area to click:")
# button_selector = RectSelector("Select Button Area")
# button_area = button_selector.selected_area
log("Please select the button area")
button_selector = RectSelector("Select Button Area")
button_area = button_selector.selected_area

if button_area is None:
    print("No button selected. Exiting.")
    exit()
btn_left, btn_top, btn_right, btn_bottom = button_area
btn_center_x = (btn_left + btn_right) // 2
btn_center_y = (btn_top + btn_bottom) // 2
print(f"Button center: {btn_center_x}, {btn_center_y}")

# --- Select message area ---
print("Select the message area to monitor:")
# msg_selector = RectSelector("Select Message Area")
# msg_area = msg_selector.selected_area
log("Please select the message area")
msg_selector = RectSelector("Select Message Area")
msg_area = msg_selector.selected_area

show_control_window()

if msg_area is None:
    print("No message area selected. Exiting.")
    exit()
left, top, right, bottom = msg_area
print(f"Message area: {left}, {top}, {right}, {bottom}")

# --- Helper function to detect changes ---
def images_are_different(img1, img2):
    diff = ImageChops.difference(img1, img2)
    return diff.getbbox() is not None

def extract_text(img):
    text = pytesseract.image_to_string(img)
    print(f"Detected text:", text)
    log(text)
    return text

# --- Randomization ---
def random_sleep(min_s, max_s):
    delay = random.uniform(min_s, max_s)
    print(f"⏳ Sleeping {delay:.1f}s\n")
    log(f"⏳ Sleeping {delay:.1f}s\n")
    # time.sleep(delay)
    # print(f"⏳ Sleeping {delay:.1f}s {reason} (click Wake to skip)")
    interruptible_sleep(delay)

def interruptible_sleep(seconds):
    """Sleep for up to `seconds`, but wake immediately if wake_event is set."""
    wake_event.clear()
    wake_event.wait(timeout=seconds)

def random_click_in_area(left, top, right, bottom):
    x = random.randint(left + 5, right - 5)
    y = random.randint(top + 5, bottom - 5)
    pyautogui.moveTo(x, y, duration=random.uniform(0.2, 0.6))
    pyautogui.click(x, y)
    return x, y



# --- Monitoring loop ---
initial_image = None

def monitoring_loop():
    global initial_image
    c = 0

    while not program_stop_event.is_set():
        try:
            c += 1
            print("NO. ", c, ", Time: ", f"{datetime.now().strftime('%H:%M:%S')}")
            log(c)
            # Save the current cursor position
            original_pos = pyautogui.position()

            # Click the marked button
            # pyautogui.click(btn_center_x, btn_center_y)
            hide_control_window()
            random_click_in_area(btn_left, btn_top, btn_right, btn_bottom)
            print(f"Clicked button at marked position.")
            log(f"Clicked button at marked position.")

            # Move cursor back to original position
            pyautogui.moveTo(original_pos, duration=random.uniform(0.15, 0.3))

            time.sleep(WAIT_AFTER_CLICK)

            # Capture message area
            screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
            show_control_window()

            text = extract_text(screenshot)
            match = re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b", text)
            # send_phone_alert(f"🚗 DVSA testing: {text}")

            if match:
                date_str = match.group().replace("-", "/")
                date_obj = datetime.strptime(date_str, "%d/%m/%Y")
                if date_obj.month in (1, 2, 3, 4):
                    print(f"🎉 Found preferred month: {date_str}")
                    log(f"🎉 Found preferred month: {date_str}")
                    send_phone_alert(f"🚗 Found preferred month: {date_str}")
                    play_alarm_thread()
                else:
                    print(f"Found date but not preferred month: {date_str}")
                    log(f"Found date but not preferred month: {date_str}")
                    send_phone_alert(f"🚗 Found date but not preferred month: {date_str}")
            elif "no tests found" in text.lower():
                pass
            else:
                print(f"⚠️Error: Manual controls needed")
                log(f"⚠️Error: Manual controls needed")
                send_phone_alert(f"⚠️Error: Manual controls needed")
                play_alarm_thread()

            random_sleep(REFRESH_INTERVAL_MIN,REFRESH_INTERVAL_MAX)
        except Exception as e:
            print("⚠️ Error:", e)
            log("⚠️ Error:", e)
            play_alarm_thread()
            # random_sleep(REFRESH_INTERVAL_MIN,REFRESH_INTERVAL_MAX)


# --- Start log updater ---
update_log_box()

# --- Start monitoring in a separate thread ---
threading.Thread(target=monitoring_loop, daemon=True).start()

# --- Start GUI ---
root.mainloop()
