import tkinter as tk
import pygame
import cv2
import mediapipe as mp
import threading
import time
import os
import sys
from PIL import Image, ImageTk #pip install pillow app

# --- Init Sound ---
pygame.mixer.init()
chords = {
    "Am": pygame.mixer.Sound(r"C:\Users\sachi\OneDrive\Attachments\Desktop\virtual Guitar\sounds\Am.wav"),
    "C": pygame.mixer.Sound(r"C:\Users\sachi\OneDrive\Attachments\Desktop\virtual Guitar\sounds\C.wav"),
    "D": pygame.mixer.Sound(r"C:\Users\sachi\OneDrive\Attachments\Desktop\virtual Guitar\sounds\D.wav"),
    "G": pygame.mixer.Sound(r"C:\Users\sachi\OneDrive\Attachments\Desktop\virtual Guitar\sounds\G.wav"),
          }
last_played = {chord: 0 for chord in chords}
chord_zones = {
    "Am": (50, 150),
    "C": (151, 250),
    "D": (251, 350),
    "G": (351, 480),
                }

# --- Recording ---
recording = True
chord_history = []

# --- GUI App ---
root = tk.Tk()
root.title(" Virtual Guitar")
root.geometry("910x720") # is windoow size
#root.config(bg="purple") this is for if want plain background


Image_path="guitarbg.png"
bg_img= Image.open(Image_path)
bg_img=bg_img.resize((906,718)) # resize to main frame
bg = ImageTk.PhotoImage(bg_img) 

# --- Place image as background ---
bg_label = tk.Label(root, image=bg)
bg_label.place(x=0, y=0, relwidth=1, relheight=1)


label = tk.Label(root, text="Virtual Guitar", font=("Arial", 25),fg="black",bg="white")
label.pack(pady=10)

feedback_label = tk.Label(root, text="Play a chord", font=("Arial", 14), fg="black",relief="groove", bg="lightgrey", bd=5)#activeforground="blue" = ->in button not in label
feedback_label.pack(pady=5)

record_status = tk.Label(root, text="Recording: ON", fg="black", font=("Arial", 14),relief="groove", bg="lightgrey" ,bd=5 )#bd -> border 
record_status.pack(pady=5)

history_box = tk.Text(root, height=10, width=40, bd=20, relief="sunken")#  Border style: flat, raised, sunken, groove, ridge
history_box.pack(pady=10)

# --- Function to play sound and log ---
def update_feedback(chord):
    timestamp = time.strftime("%H:%M:%S")
    feedback_label.config(text=f"Playing: {chord}")
    if recording:
        record_status.config(text="Recording: ON", fg="green")
        history_box.insert(tk.END, f"{timestamp} - {chord}\n")
        history_box.see(tk.END)
        chord_history.append(f"{timestamp} - {chord}")

def play_chord(chord_name):
    chords[chord_name].play()
    update_feedback(chord_name)

# --- Chord Buttons ---
for chord in chords:
    btn = tk.Button(root, text=chord, width=20, height=2,
                    command=lambda c=chord: play_chord(c))
    btn.pack(pady=5)

# --- Start/Stop Recording ---
def toggle_recording():
    global recording
    recording = not recording
    status = "ON" if recording else "OFF"
    color = "green" if recording else "red"
    record_status.config(text=f"Recording: {status}", fg=color)

record_btn = tk.Button(root, text="Start/Stop Recording", command=toggle_recording, bg="orange")
record_btn.pack(pady=10)


# --- Save to File ---
def save_history():
    with open("chord_history.txt", "w") as f:
        f.write("\n".join(chord_history))
    feedback_label.config(text="Saved to chord_history.txt")

save_btn = tk.Button(root, text=" Save History", command=save_history, bg="lightgreen")
save_btn.pack(pady=10)

# --- Proper Exit (close webcam on GUI exit) ---
exit_app = False

def on_closing():
    global exit_app
    exit_app = True
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# --- Hand Detection Thread ---
def hand_gesture_loop():
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.5)
    mp_draw = mp.solutions.drawing_utils
    cap = cv2.VideoCapture(0)

    while not exit_app:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        for chord, (y1, y2) in chord_zones.items():
            cv2.rectangle(frame, (0, y1), (w, y2), (255, 255, 255), 2)
            cv2.putText(frame, chord, (10, y1 + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                index_tip = hand_landmarks.landmark[8]
                x = int(index_tip.x * w)
                y = int(index_tip.y * h)
                cv2.circle(frame, (x, y), 10, (0, 0, 255), -1)

                for chord, (y1, y2) in chord_zones.items():
                    if y1 <= y <= y2:
                        if time.time() - last_played[chord] > 1:
                            chords[chord].play()
                            update_feedback(chord)
                            last_played[chord] = time.time()

        cv2.imshow(" Hand-Controlled Guitar", frame)
        if cv2.waitKey(1) & 0xFF == ord('q') or exit_app:
            break

    cap.release()
    cv2.destroyAllWindows()

threading.Thread(target=hand_gesture_loop, daemon=True).start()
root.mainloop()
