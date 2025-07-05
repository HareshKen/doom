import cv2
import mediapipe as mp
import pyautogui
import time

class VirtualMouse:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.hands = mp.solutions.hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)
        self.drawing_utils = mp.solutions.drawing_utils
        self.screen_width, self.screen_height = pyautogui.size()
        self.index_coords = None
        self.prev_index_x = 0
        # self.left_click_flag = False
        self.fist_flag = False  # 👈 Add this for closed hand gesture

    def run(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                continue
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            output = self.hands.process(rgb_frame)
            hands = output.multi_hand_landmarks

            if hands:
                for hand in hands:
                    landmarks = hand.landmark
                    index_x = int(landmarks[8].x * self.screen_width)
                    index_y = int(landmarks[8].y * self.screen_height)
                    thumb_x = int(landmarks[4].x * self.screen_width)
                    thumb_y = int(landmarks[4].y * self.screen_height)

                    self.index_coords = (index_x, index_y)

                    # # Detect left click (Index tip close to Thumb tip)
                    # if abs(index_y - thumb_y) < 60:
                    #     if not self.left_click_flag:
                    #         self.left_click_flag = True
                    # else:
                    #     self.left_click_flag = False

                    # 👊 Detect fist: all finger tips below their PIP joints
                    fingers_closed = all(
                        landmarks[tip].y > landmarks[tip - 2].y  # Tip below PIP joint
                        for tip in [8, 12, 16, 20]
                    )
                    self.fist_flag = fingers_closed
            else:
                self.fist_flag = False

