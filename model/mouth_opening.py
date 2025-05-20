import cv2
import mediapipe as mp
import time
import sounddevice as sd
import numpy as np

class MouthOpeningDetector:
    def __init__(self):
        # Initialize state variables
        self.prev_pose = None
        self.transitions = 0
        self.start_time = time.time()

    def detect_sound(self, threshold=0.02, duration=0.5):
        """Capture audio and check if the sound exceeds the threshold.
           If an error occurs (e.g. no audio device), return False.
        """
        try:
            recording = sd.rec(int(duration * 44100), samplerate=44100, channels=1, dtype='float32')
            sd.wait()  # Wait until recording is finished
            amplitude = np.max(np.abs(recording))  # Get the max amplitude
            return amplitude > threshold  # Return True if sound exceeds threshold
        except Exception as e:
            print("Audio detection error:", e)
            return False

    def run(self, res, frame):
        """
        Process the frame and facial landmarks, and return an alert message if malpractice is detected.
        """
        alert_message = ""
        # Define landmark indices for upper and lower lip (as used in your original code)
        upper_lip = 0
        lower_lip = 14
        upper_loc = 0
        lower_loc = 0
        text = ''

        if res.multi_face_landmarks:
            frame_height, frame_width, _ = frame.shape
            # Extract facial landmarks for the first detected face
            landmarks = res.multi_face_landmarks[0].landmark
            for id, landmark in enumerate(landmarks):
                x, y = landmark.x, landmark.y
                x_on_frame = int(x * frame_width)
                y_on_frame = int(y * frame_height)

                # Capture the vertical positions for upper and lower lip landmarks
                if id == upper_lip:
                    upper_loc = y_on_frame
                elif id == lower_lip:
                    lower_loc = y_on_frame

            # Calculate lip distance and determine mouth status
            diff = int(lower_loc - upper_loc)
            #print(diff)
            text = "Mouth Open" if diff > 10 else "Mouth Closed"

            # Detect transitions between states
            if self.prev_pose and text != self.prev_pose:
                self.transitions += 1
                self.prev_pose = text
            elif not self.prev_pose:
                self.prev_pose = text

            current_time = time.time()
            # Check transitions within a 10-second window for frequent movements
            if current_time - self.start_time > 5:
                if self.transitions > 7:
                    alert_message = "Alert: Frequent mouth movement detected!"
                    print(alert_message)
                # Reset the state for the next window
                self.transitions = 0
                self.start_time = current_time

            # Check for speaking if the mouth is open
            # if text == "Mouth Open":
            #     if self.detect_sound():
            #         alert_message = "Alert: Malpractice suspected: Speaking detected!"
            #         print(alert_message)

        # Optionally, display the frame (for debugging; comment out in production)
        # cv2.imshow('img', frame)
        # cv2.waitKey(1)
        return alert_message
