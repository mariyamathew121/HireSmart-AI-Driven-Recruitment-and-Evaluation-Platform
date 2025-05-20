import cv2
import mediapipe as mp
import numpy as np
import time

class EyeGazeTracker:
    def __init__(self):
        self.prev_gaze = None
        self.gaze_start_time = None
        self.alert_sent = False
        self.RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        self.LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]

    @staticmethod
    def landmark_detect(img, res, draw=False):
        height, width = img.shape[0], img.shape[1]
        mesh_coor = [(int(point.x * width), int(point.y * height)) 
                     for point in res.multi_face_landmarks[0].landmark]
        if draw:
            [cv2.circle(img, p, 2, (0, 255, 0), -1) for p in mesh_coor]
        return mesh_coor

    @staticmethod
    def eyes_extractor(img, right_eye_corr, left_eye_corr):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        mask = np.zeros(gray.shape, dtype=np.uint8)

        cv2.fillPoly(mask, [np.array(right_eye_corr, dtype=np.int32)], 255)
        cv2.fillPoly(mask, [np.array(left_eye_corr, dtype=np.int32)], 255)

        eyes = cv2.bitwise_and(gray, gray, mask=mask)
        # Optional: display the extracted eyes for debugging
        # cv2.imshow("Eye Draw", eyes)
        eyes[mask == 0] = 155

        r_min_x = min(right_eye_corr, key=lambda item: item[0])[0]
        r_max_x = max(right_eye_corr, key=lambda item: item[0])[0]
        r_min_y = min(right_eye_corr, key=lambda item: item[1])[1]
        r_max_y = max(right_eye_corr, key=lambda item: item[1])[1]

        l_min_x = min(left_eye_corr, key=lambda item: item[0])[0]
        l_max_x = max(left_eye_corr, key=lambda item: item[0])[0]
        l_min_y = min(left_eye_corr, key=lambda item: item[1])[1]
        l_max_y = max(left_eye_corr, key=lambda item: item[1])[1]

        cropped_right = eyes[r_min_y:r_max_y, r_min_x:r_max_x]
        cropped_left = eyes[l_min_y:l_max_y, l_min_x:l_max_x]

        return cropped_right, cropped_left

    @staticmethod
    def pos_estimation(cropped_eye):
        # Check if the cropped eye image is valid
        if cropped_eye is None or cropped_eye.size == 0:
            return "CENTER"
        h, w = cropped_eye.shape
        if w == 0 or h == 0:
            return "CENTER"

        # Optionally, you might want to blur the image to reduce noise:
        # gaussian_blur = cv2.GaussianBlur(cropped_eye, (9, 9), 0)
        # median_blur = cv2.medianBlur(gaussian_blur, 3)

        # Use adaptive thresholding to isolate the iris (black pixels)
        thres_eye = cv2.adaptiveThreshold(cropped_eye, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                          cv2.THRESH_BINARY, 33, 0)

        piece = int(w / 3)
        right_piece = thres_eye[0:h, 0:piece]
        center_piece = thres_eye[0:h, piece:piece + piece]
        left_piece = thres_eye[0:h, piece + piece:w]

        right_part = np.sum(right_piece == 0)
        center_part = np.sum(center_piece == 0)
        left_part = np.sum(left_piece == 0)

        # Sensitivity thresholds for detecting gaze direction
        left_threshold = 0.44
        right_threshold = 0.78
        center_tolerance = 0.8

        if left_part > left_threshold * center_part:
            return "LEFT"
        elif right_part > right_threshold * center_part:
            return "RIGHT"
        elif abs(left_part - right_part) < center_tolerance * center_part:
            return "CENTER"
        else:
            return "CENTER"

    def run(self, res, frame):
        """
        Process the frame for eye tracking and return an alert message if the user is
        looking in a non-central direction for too long.
        """
        alert_message = ""
        if res.multi_face_landmarks:
            # Get facial landmarks and extract eye regions
            mesh_coor = self.landmark_detect(frame, res, draw=False)
            right_corr = [mesh_coor[p] for p in self.RIGHT_EYE]
            left_corr = [mesh_coor[p] for p in self.LEFT_EYE]
            
            # Optionally, draw outlines around the eyes for debugging:
            # cv2.polylines(frame, [np.array(right_corr, dtype=np.int32)], isClosed=True, color=(0, 255, 0), thickness=2)
            # cv2.polylines(frame, [np.array(left_corr, dtype=np.int32)], isClosed=True, color=(0, 255, 0), thickness=2)
        
            crop_right, crop_left = self.eyes_extractor(frame, right_corr, left_corr)
            # Use one eye (here the right eye) for gaze estimation
            eye_pos = self.pos_estimation(crop_right)
            
            current_time = time.time()
            # Check if gaze remains non-central (LEFT or RIGHT) for more than 2 seconds
            if eye_pos == self.prev_gaze and eye_pos != "CENTER":
                if self.gaze_start_time is None:
                    self.gaze_start_time = current_time
                elif current_time - self.gaze_start_time > 3:
                    if not self.alert_sent:
                        alert_message = f"Alert: Eyes focused too long in the '{eye_pos.lower()}' direction!"
                        print(alert_message)
                        self.alert_sent = True
            else:
                self.prev_gaze = eye_pos
                self.gaze_start_time = current_time
                self.alert_sent = False

        # Optionally, display the frame for debugging (comment out in production)
        # cv2.imshow("Image", frame)
        # cv2.waitKey(1)
        return alert_message
