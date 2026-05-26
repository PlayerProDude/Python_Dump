# ============================================================
# Tello Drone Controller + Voice Command Recognition
#
# Install these libraries before running:
#   pip install djitellopy openai sounddevice numpy scipy
#
# Steps:
#   1. Connect your computer to the Tello drone's WiFi
#   2. Run this file: python drone_controller.py
#   3. Use the menu to fly manually, or choose option 12
#      to speak a command and have the drone execute it
# ============================================================


import time
import threading
import tempfile
import numpy as np
from openai import OpenAI
import sounddevice as sd
from scipy.io.wavfile import write as wav_write
from djitellopy import Tello


# ---- Settings ----------------------------------------------

MOVE_CM      = 30
ROTATE_DEG   = 90
RECORD_SECS  = 10
SAMPLE_RATE  = 16000

# ------------------------------------------------------------


# ---- OpenAI API Key ----------------------------------------



openai_key = "YOUR_API_KEY_HERE"



# ============================================================
# REAL DRONE SETUP
# ============================================================

drone = Tello()

print("Connecting to drone...")
drone.connect()
print("Connected!")
print("Battery:", drone.get_battery(), "%")


# ============================================================
# DRONE FUNCTIONS
# ============================================================

def takeoff():
    drone.takeoff()

def land():
    drone.land()

def move_forward():
    drone.move_forward(MOVE_CM)

def move_backward():
    drone.move_back(MOVE_CM)

def move_left():
    drone.move_left(MOVE_CM)

def move_right():
    drone.move_right(MOVE_CM)

def move_up():
    drone.move_up(MOVE_CM)

def move_down():
    drone.move_down(MOVE_CM)

def rotate_clockwise():
    drone.rotate_clockwise(ROTATE_DEG)

def rotate_counter_clockwise():
    drone.rotate_counter_clockwise(ROTATE_DEG)

def emergency_stop():
    drone.emergency()


# ============================================================
# VOICE COMMAND FUNCTIONS
# ============================================================

def record_and_transcribe():

    print("")
    print("Listening... speak your command now.")
    print(f"Press ENTER to stop early (max {RECORD_SECS} seconds).")

    recorded_chunks = []
    stop_recording = threading.Event()

    def record_audio():

        chunk_duration = 0.5
        samples_per_chunk = int(SAMPLE_RATE * chunk_duration)
        total_elapsed = 0.0

        while not stop_recording.is_set() and total_elapsed < RECORD_SECS:

            chunk = sd.rec(
                samples_per_chunk,
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="int16",
                blocking=True
            )

            recorded_chunks.append(chunk)
            total_elapsed += chunk_duration

        stop_recording.set()

    recording_thread = threading.Thread(
        target=record_audio,
        daemon=True
    )

    recording_thread.start()

    input()

    stop_recording.set()
    recording_thread.join(timeout=2)

    if len(recorded_chunks) == 0:
        print("Nothing was recorded.")
        return ""

    full_audio = np.concatenate(recorded_chunks, axis=0)

    temp_file = tempfile.NamedTemporaryFile(
        suffix=".wav",
        delete=False
    )

    wav_path = temp_file.name
    temp_file.close()

    wav_write(wav_path, SAMPLE_RATE, full_audio)

    print("Transcribing...")

    try:

        client = OpenAI(api_key=openai_key)

        audio_file = open(wav_path, "rb")

        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="en"
        )

        audio_file.close()

        transcript = result.text.strip().lower()

        print("You said:", transcript)

        return transcript

    except Exception as e:

        print("Transcription failed:", e)
        return ""


def match_and_execute(transcript):

    words = [w.strip(".,!?;:'\"") for w in transcript.split()]

    # Emergency
    if "emergency stop" in transcript:
        print("Command matched: emergency stop")
        emergency_stop()
        return True

    # Takeoff
    if "takeoff" in transcript or "take off" in transcript:
        print("Command matched: takeoff")
        takeoff()
        return True

    # Land
    if "land" in words or "landing" in words:
        print("Command matched: land")
        land()
        return True

    # Counter clockwise
    if (
        "counter clockwise" in transcript
        or "counterclockwise" in transcript
        or "anticlockwise" in transcript
    ):
        print("Command matched: rotate counter-clockwise")
        rotate_counter_clockwise()
        return True

    # Clockwise
    if "clockwise" in transcript or "spin" in words:
        print("Command matched: rotate clockwise")
        rotate_clockwise()
        return True

    # Forward
    if "forward" in words or "ahead" in words:
        print("Command matched: move forward")
        move_forward()
        return True

    # Backward
    if (
        "backward" in words
        or "backwards" in words
        or "reverse" in words
    ):
        print("Command matched: move backward")
        move_backward()
        return True

    # Left
    if "left" in words:
        print("Command matched: move left")
        move_left()
        return True

    # Right
    if "right" in words:
        print("Command matched: move right")
        move_right()
        return True

    # Up
    if (
        "up" in words
        or "rise" in words
        or "higher" in words
    ):
        print("Command matched: move up")
        move_up()
        return True

    # Down
    if (
        "down" in words
        or "lower" in words
    ):
        print("Command matched: move down")
        move_down()
        return True

    return False


def ask_chatgpt(message):
    try:
        client = OpenAI(api_key=openai_key)
        response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "system", "content": "You are a smart and helpful assistant, happy to help the user with whatever they please."}, {"role": "user", "content": message}])
        reply = response.choices[0].message.content
        return reply
    except Exception as e:
        print("GPT Error:")
        print(e)



def listen_for_command():

    if openai_key == "":
        print("No API key entered.")
        return

    transcript = record_and_transcribe()

    if transcript == "":
        print("No speech detected.")
        return

    matched = match_and_execute(transcript)

    if not matched:
        response = ask_chatgpt(transcript)
        print(" ")
        print("ChatGPT says: ")
        print(response)
        time.sleep(4)

def drone_nod():
    for i in range(2):
        drone.move_up(20)
        drone.move_down(20)

def drone_shake():
    drone.rotate_counter_clockwise(30)
    drone.rotate_clockwise(60)
    drone.rotate_counter_clockwise(60)
    drone.rotate_clockwise(30)

def yes_or_no(message):
    message = input("Enter a yes or no question: ")
    try:
        client = OpenAI(api_key=openai_key)
        response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "system", "content": "You are a dumb assistant that can only answer by saying 'yes' or 'no', no matter what the question. Do not capatilise your yes or no."}, {"role": "user", "content": message}])
        reply = response.choices[0].message.content
        if reply == "yes":
            drone_nod()
        elif reply == "no":
            drone_shake()
    except Exception as e:            
        print("GPT Error:")
        print(e)



# ============================================================
# MAIN MENU LOOP
# ============================================================

while True:

    print("")
    print("----------------------------------")
    print("   VOICE COMMAND TEST MENU")
    print("----------------------------------")
    print("   1  Takeoff")
    print("   2  Land")
    print("   3  Move Forward")
    print("   4  Move Backward")
    print("   5  Move Left")
    print("   6  Move Right")
    print("   7  Move Up")
    print("   8  Move Down")
    print("   9  Rotate Clockwise")
    print("  10  Rotate Counter-Clockwise")
    print("  11  Emergency Stop")
    print("  12  Speak a Voice Command")
    print("  13  Ask a yes or no question")
    print("   0  Quit")
    print("----------------------------------")
    

    choice = input("Enter number: ").strip()

    if choice == "0":
        print("Goodbye.")
        drone.end()
        break

    elif choice == "1":
        takeoff()

    elif choice == "2":
        land()

    elif choice == "3":
        move_forward()

    elif choice == "4":
        move_backward()

    elif choice == "5":
        move_left()

    elif choice == "6":
        move_right()

    elif choice == "7":
        move_up()

    elif choice == "8":
        move_down()

    elif choice == "9":
        rotate_clockwise()

    elif choice == "10":
        rotate_counter_clockwise()

    elif choice == "11":
        emergency_stop()

    elif choice == "12":
        listen_for_command()

    elif choice == "13":
        yes_or_no("")

    else:
        print("Invalid option.")

    time.sleep(0.3)