import cv2
import numpy as np
import mediapipe as mp
import asyncio
from fastapi import APIRouter, WebSocket
from concurrent.futures import ThreadPoolExecutor

from model.head_pose_estimation import HeadPoseEstimator
from model.mouth_opening import MouthOpeningDetector
from model.eye_tracking import EyeGazeTracker

router = APIRouter()

# Initialize MediaPipe FaceMesh
face_mesh = mp.solutions.face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Create detector instances. Update the model path as needed.
estimator = HeadPoseEstimator(model_path="E:/main-project-code/model/model.pkl")
mouth_detector = MouthOpeningDetector()
eye_detector = EyeGazeTracker()

# Executor for running blocking tasks in separate threads.
executor = ThreadPoolExecutor(max_workers=3)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    loop = asyncio.get_running_loop()
    while True:
        try:
            # Receive the raw binary frame
            frame_data = await websocket.receive_bytes()
            nparr = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                continue

            # Convert frame to RGB for MediaPipe processing
            frame = cv2.resize(frame, None, fx=0.50, fy=0.50, interpolation=cv2.INTER_CUBIC)
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = face_mesh.process(rgb_frame)

            # Run both detectors concurrently in separate threads.
            head_future = loop.run_in_executor(executor, estimator.run, res, frame)
            mouth_future = loop.run_in_executor(executor, mouth_detector.run, res, frame)
            eye_future = loop.run_in_executor(executor, eye_detector.run, res, frame)
            
            alert_message = ""
            # Check each task as soon as it completes.
            for future in asyncio.as_completed([head_future, mouth_future, eye_future]):
                result = await future
                if result:  # If a non-empty alert is returned, use it.
                    alert_message = result
                    break

            if alert_message:
                await websocket.send_text(alert_message)
            else:
                await websocket.send_text("Frame processed")
        except Exception as e:
            print("Connection closed:", e)
            break


# from fastapi import FastAPI, WebSocket
# import cv2
# import numpy as np
# import mediapipe as mp
# from model.head_pose_estimation import HeadPoseEstimator  # Import your script
# from model.mouth_opening import MouthOpeningDetector
# from model.eye_tracking import EyeGazeTracker

# app = FastAPI()

# # Initialize MediaPipe FaceMesh
# face_mesh = mp.solutions.face_mesh.FaceMesh(
#     static_image_mode=False,
#     max_num_faces=1,
#     refine_landmarks=True,
#     min_detection_confidence=0.5,
#     min_tracking_confidence=0.5
# )

# # Initialize your head pose estimator (update the model path as necessary)
# #estimator = HeadPoseEstimator(model_path='path/to/your/model.pkl')
# eye_estimator=EyeGazeTracker()

# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     while True:
#         try:
#             # Receive raw binary data
#             frame_data = await websocket.receive_bytes()
#             nparr = np.frombuffer(frame_data, np.uint8)
#             frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
#             if frame is None:
#                 continue

#             # Process the frame with MediaPipe
#             frame = cv2.resize(frame, None, fx=0.50, fy=0.50, interpolation=cv2.INTER_CUBIC)
#             frame = cv2.flip(frame, 1)
#             rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#             res = face_mesh.process(rgb_frame)

#             # Get the alert message from the head pose estimator (if any)
#             alert_message = eye_estimator.run(res, frame)

#             # Send the alert message if produced; otherwise send a generic response.
#             if alert_message:
#                 await websocket.send_text(alert_message)
#             else:
#                 await websocket.send_text("Frame processed")
#         except Exception as e:
#             print(f"Connection closed: {e}")
#             break
