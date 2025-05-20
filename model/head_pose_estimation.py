import pickle
import pandas as pd
import cv2
import mediapipe as mp
import numpy as np
import time


class HeadPoseEstimator:
    def __init__(self, model_path='./model.pkl'):
        self.model = pickle.load(open(model_path, 'rb'))  # Load the prediction model
        self.cols = []
        for pos in ['nose_', 'forehead_', 'left_eye_', 'mouth_left_', 'chin_', 'right_eye_', 'mouth_right_']:
            for dim in ('x', 'y'):
                self.cols.append(pos + dim)

        # State management variables
        self.prev_direction = None
        self.gaze_start_time = None
        self.alert_sent = False

    def extract_features_from_res(self, res):
        """Extract face landmarks from the res object."""
        NOSE = 1
        FOREHEAD = 10
        LEFT_EYE = 33
        MOUTH_LEFT = 61
        CHIN = 199
        RIGHT_EYE = 263
        MOUTH_RIGHT = 291

        face_features = []
        if res.multi_face_landmarks:
            for face_landmarks in res.multi_face_landmarks:
                for idx, lm in enumerate(face_landmarks.landmark):
                    if idx in [FOREHEAD, NOSE, MOUTH_LEFT, MOUTH_RIGHT, CHIN, LEFT_EYE, RIGHT_EYE]:
                        face_features.append(lm.x)
                        face_features.append(lm.y)

        return face_features

    def normalize(self, poses_df):
        normalized_df = poses_df.copy()
        for dim in ['x', 'y']:
            # Center around the nose
            for feature in ['forehead_' + dim, 'nose_' + dim, 'mouth_left_' + dim, 'mouth_right_' + dim,
                            'left_eye_' + dim, 'chin_' + dim, 'right_eye_' + dim]:
                normalized_df[feature] = poses_df[feature] - poses_df['nose_' + dim]

            # Scaling
            diff = normalized_df['mouth_right_' + dim] - normalized_df['left_eye_' + dim]
            for feature in ['forehead_' + dim, 'nose_' + dim, 'mouth_left_' + dim, 'mouth_right_' + dim,
                            'left_eye_' + dim, 'chin_' + dim, 'right_eye_' + dim]:
                normalized_df[feature] = normalized_df[feature] / diff

        return normalized_df

    # @staticmethod
    # def draw_axes(img, pitch, yaw, roll, tx, ty, size=50):
    #     yaw = -yaw
    #     rotation_matrix = cv2.Rodrigues(np.array([pitch, yaw, roll]))[0].astype(np.float64)
    #     axes_points = np.array([
    #         [1, 0, 0, 0],
    #         [0, 1, 0, 0],
    #         [0, 0, 1, 0]
    #     ], dtype=np.float64)
    #     axes_points = rotation_matrix @ axes_points
    #     axes_points = (axes_points[:2, :] * size).astype(int)
    #     axes_points[0, :] = axes_points[0, :] + tx
    #     axes_points[1, :] = axes_points[1, :] + ty

    #     new_img = img.copy()
    #     cv2.line(new_img, tuple(axes_points[:, 3].ravel()), tuple(axes_points[:, 0].ravel()), (255, 0, 0), 3)
    #     cv2.line(new_img, tuple(axes_points[:, 3].ravel()), tuple(axes_points[:, 1].ravel()), (0, 255, 0), 3)
    #     cv2.line(new_img, tuple(axes_points[:, 3].ravel()), tuple(axes_points[:, 2].ravel()), (0, 0, 255), 3)
    #     return new_img

    def run(self, res, frame):
        alert_message = ""
        face_features = self.extract_features_from_res(res)
        if len(face_features) > 0:
            # Normalize features
            face_features_df = pd.DataFrame([face_features], columns=self.cols)
            face_features_normalized = self.normalize(face_features_df)
            pitch_pred, yaw_pred, roll_pred = self.model.predict(face_features_normalized).ravel()

            # Determine head direction
            text = ''
            if pitch_pred > 0.3:
                text = 'Top'
                if yaw_pred > 0.3:
                    text = 'Top Left'
                elif yaw_pred < -0.3:
                    text = 'Top Right'
            elif pitch_pred < -0.3:
                text = 'Bottom'
                if yaw_pred > 0.3:
                    text = 'Bottom Left'
                elif yaw_pred < -0.3:
                    text = 'Bottom Right'
            elif yaw_pred > 0.3:
                text = 'Left'
            elif yaw_pred < -0.3:
                text = 'Right'
            else:
                text = 'Forward'

            # Track how long the user is looking in a specific direction
            current_time = time.time()
            if text == self.prev_direction and text != "Forward":
                if self.gaze_start_time is None:
                    self.gaze_start_time = current_time
                elif current_time - self.gaze_start_time > 5:  # More than 5 seconds
                    if not self.alert_sent:
                        alert_message = f"Alert: Head turned '{text}' for an extended period!"
                        print(alert_message)
                        self.alert_sent = True
            else:
                self.prev_direction = text
                self.gaze_start_time = current_time
                self.alert_sent = False

        return alert_message


        #     # Display detected direction on the frame
        #     cv2.putText(frame, text, (25, 75), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        # cv2.imshow('Head Pose Estimation', frame)
