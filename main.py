import threading
import time
import keyboard
from grabScreen import grab_screen
import cv2
import pytesseract
import queue
from tkinter import *
import re

prev_KPH = 0.0
target_speed = 60
prev_speed_error = 0.0
delta = 0.55
accu_speed_error = 0.0
Kp = 0.5
Kd = 0.04
Ki = 0.002

cur_time = 0

def countdown(num, toPrint=True):
    for i in list(range(num))[::-1]:
        value = '0' + str(i + 1)
        value = value[-2:]
        if toPrint:
            print(f"{value}")
        time.sleep(1)

def pid(img):
    # cur_time = time.now()
    global prev_speed_error, delta, accu_speed_error, prev_KPH
    # cv2.imshow("Image", img)
    # cv2.waitKey(1)
    pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
    custom_config = r'-l eng --oem 3 --psm 6' 
    out_below = pytesseract.image_to_string(img,config=custom_config)
    out_below = re.sub("[^0-9]", "", out_below)
    out_below.replace("\n", "")
    # print(out_below)
    try:
        KPH = float(out_below) / 10
    except:
        KPH = prev_KPH + 5
    
    # print(f"PID Speed: {KPH}, {type(KPH)}")

    kph_error = (target_speed - 5) - KPH
    speed_error_der = (kph_error - prev_speed_error) / delta
    prev_speed_error = kph_error
    accu_speed_error += kph_error * delta
    pid_value = (Kp * kph_error) + (Kd * speed_error_der) + (Ki * accu_speed_error)
    # delta = delta + 1
    prev_KPH = KPH
    
    speed_label.config(text=f"Speed: {KPH} KPH")
    pid_label.config(text=f"PID: {pid_value} KPH")
    root.update()

    # print(f"PID Value: {pid_value}", flush=True)
    if (pid_value >= 1):
        return "W"
    elif(pid_value <= -1):
        return "S"
    return "N"

def getRadar(image):
    img = image.copy()
    startX = 28
    startY = 873
    endX = 300
    endY = 1045

    img = img[startY:endY, startX:endX]

    for j, y in enumerate(img):
        for i, x in enumerate(y):
            if x[0] == 243 and x[1] == 84 and x[2] == 168:
                img[j][i] = 255
            else:
                img[j][i] = 0

    img = cv2.resize(img, (128, 128))
    return img


def getSpeed(image):
    img = image.copy()
    startX = 125
    startY = 843
    endX = 173
    endY = 869

    img = img[startY:endY, startX:endX]

    img = cv2.resize(img, (256, 128))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    # for j, y in enumerate(img):
    #     for i, x in enumerate(y):
    #         if x > 150:
    #             img[j][i] = 255
    #         else:
    #             img[j][i] = 0

    # img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    return img

# Placeholder for your TensorFlow model function
def process_image_and_get_values(img1, img2, img3):
    startX = 20
    startY = 839
    endX = 300
    endY = 1060
    img1[startY:endY, startX:endX] = [0, 0, 0]
    img1 = cv2.resize(img1, (256, 256))

    # Replace this with your actual TensorFlow model code
    throttleVal, throttleFlag, steeringVal, steeringFlag = 1, 1, 1, 0
    if throttleFlag:
        if throttleVal == 1:
            start = time.time()
            throttleVal = pid(img3)
            # if throttleVal == "N":
            #     throttleFlag = 0
        else:
            throttleVal = 'S'
    
    if steeringFlag:
        if steeringVal == 1:
            steeringVal = 'A'
        else:
            steeringVal = 'D'

    return throttleVal, throttleFlag, steeringVal, steeringFlag

def capture_screenshot():
    countdown(10, True)
    global throttle_queue, steering_queue, cur_time, throttle_change
    print("Capture Screenshot Thread Started")
    while True:
        try:
            screen = grab_screen(region=(0, 0, 1920, 1080))
            img = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
            img1 = getRadar(img)
            img2 = getSpeed(img)

            throttleVal, throttleFlag, steeringVal, steeringFlag = process_image_and_get_values(img, img1, img2)
            pid_time.config(text=f"PID Time: {str(time.time() - cur_time)}")
            cur_time = time.time()
            if throttleFlag:
                # throttle_queue.put(throttleVal)
                throttle_queue = throttleVal
                throttle_change = 1
            if steeringFlag:
                # steering_queue.put(steeringVal)
                steering_queue = steeringVal
        except:
            pass
    print("Closing Scr")

def control_throttle():
    countdown(12, False)
    global throttle_queue, throttle_change
    print("Control Throttle Thread Started")
    while True:
        if (throttle_change):
            try:
                throttle_change = 0
                throttle_value = throttle_queue
                # print(throttle_value)
                if throttle_value == "W":
                    keyboard.release("S")
                    keyboard.press("W")
                    time.sleep(0.5)
                    keyboard.release("W")
                elif throttle_value == "S":
                    keyboard.release("W")
                    keyboard.press_and_release("S")
                    time.sleep(0.4)
                    keyboard.press("W")
                    time.sleep(0.3)
                    keyboard.release("W")
                else:
                    keyboard.release("W")
                    keyboard.release("S")
                    # time.sleep(0.2)
                # keyboard.press_and_release(throttle_value)
                throttle_label.config(text=f"Throttle: {throttle_value}")
                root.update()
            # time.sleep(0.1)
            except:
                pass
        time.sleep(0.1)
    print("Closing Th")


def control_steering():
    countdown(12, False)
    print("Control Steering Thread Started")
    while True:
        # try:
        #     steering_value = steering_queue.get()
        #     keyboard.press_and_release(steering_value)
        #     steering_label.config(text=f"Steering: {steering_value}")
        #     root.update()
        # except queue.Empty:
        #     pass
        time.sleep(0.1)
    print("Closing St")


# Create Tkinter window
root = Tk()
root.title("Car Controller GUI")

# Create labels for displaying throttle, steering, and speed values
throttle_label = Label(root, text="Throttle: N/A")
throttle_label.pack()

steering_label = Label(root, text="Steering: N/A")
steering_label.pack()

speed_label = Label(root, text="Speed: N/A")
speed_label.pack()

pid_label = Label(root, text="PID: N/A")
pid_label.pack()

pid_time = Label(root, text="PID Time: N/A")
pid_time.pack()

# Create queues for inter-thread communication
throttle_queue = "W"
steering_queue = "N"
throttle_change = 1

# Create threads
throttle_thread = threading.Thread(target=control_throttle)
steering_thread = threading.Thread(target=control_steering)
screenshot_thread = threading.Thread(target=capture_screenshot)

# Start threads
throttle_thread.start()
steering_thread.start()
screenshot_thread.start()

root.mainloop()
# Wait for threads to finish (you might want to add an exit condition)
# screenshot_thread.join()
# throttle_thread.join()
# steering_thread.join()
