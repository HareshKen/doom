import cv2
import pyautogui
import sys
import os
import time
import pygame as pg

# Add hand-tracking folder to Python path
sys.path.append(os.path.abspath('../hand-tracking'))
from cvzone.HandTrackingModule import HandDetector

class DualHandController:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.detector = HandDetector(maxHands=2, detectionCon=0.7, modelComplexity=0, minTrackCon=0.7)
        self.screen_width, self.screen_height = pyautogui.size()
        
        # Right hand controls (camera movement and shooting)
        self.right_hand_coords = None
        self.prev_right_x = 0
        self.gun_flag = False
        self.weapon_flag = False
        self.weapon_switch = False

        # Weapon switching cooldown - simplified
        self.last_weapon_switch_time = 0
        self.weapon_switch_delay = 0.5  # 500ms cooldown in seconds
        self.weapon_gesture_detected = False
        
        # Left hand controls (movement and weapon switch)
        self.left_hand_present = False
        self.move_forward = False    # Middle finger bent -> W
        self.move_left = False       # Ring finger bent -> A
        self.move_backward = False   # Pinky finger bent -> S
        self.move_right = False      # Index finger bent -> D
        
        
        # Sensitivity settings
        self.movement_sensitivity = 0.003
        self.deadzone = 30  # Minimum movement threshold
        
        # Debugging
        self.debug_mode = True
        
    def detect_finger_bend(self, hand, finger_index):
        """
        Detect if a specific finger is bent based on landmark positions.
        Returns True if finger is bent/closed, False if extended.
        """
        lmList = hand['lmList']
        
        # Finger tip and joint positions for each finger
        finger_tips = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky
        finger_joints = [3, 6, 10, 14, 18]  # Corresponding joints
        
        if finger_index == 0:  # Thumb (special case)
            # For thumb, check if tip is closer to palm than joint
            thumb_tip = lmList[finger_tips[0]]
            thumb_joint = lmList[finger_joints[0]]
            wrist = lmList[0]
            
            # Distance from tip to wrist vs joint to wrist
            tip_to_wrist = ((thumb_tip[0] - wrist[0])**2 + (thumb_tip[1] - wrist[1])**2)**0.5
            joint_to_wrist = ((thumb_joint[0] - wrist[0])**2 + (thumb_joint[1] - wrist[1])**2)**0.5
            
            return tip_to_wrist < joint_to_wrist
        else:
            # For other fingers, check if tip is below the joint (bent down)
            finger_tip = lmList[finger_tips[finger_index]]
            finger_joint = lmList[finger_joints[finger_index]]
            
            # Finger is bent if tip Y is greater than joint Y (lower on screen)
            return finger_tip[1] > finger_joint[1]
    
    
    def process_left_hand(self, hand):
        """Process left hand for movement controls (W,A,S,D) and weapon switching (F)"""
        self.left_hand_present = True
        
        
        # Check individual finger bends for movement (only if not making fist)
        # Updated finger mapping:
        # Middle finger (index 2) -> W (forward)
        # Ring finger (index 3) -> A (left)
        # Index finger (index 1) -> D (right)
        # Pinky finger (index 4) -> S (backward)
        self.move_forward = self.detect_finger_bend(hand, 2)     # Middle -> W
        self.move_left = self.detect_finger_bend(hand, 3)        # Ring -> A
        self.move_right = self.detect_finger_bend(hand, 1)       # Index -> D
        self.move_backward = self.detect_finger_bend(hand, 4)    # Pinky -> S
        
        if self.debug_mode:
            controls = []
            if self.move_forward: controls.append("W (Middle)")
            if self.move_left: controls.append("A (Ring)")
            if self.move_right: controls.append("D (Index)")
            if self.move_backward: controls.append("S (Pinky)")
            if controls:
                print(f"Left hand controls: {', '.join(controls)}")
    
    def process_right_hand(self, hand):
        """Process right hand for camera movement and shooting"""
        lmList = hand['lmList']

        # Get index finger tip position for camera control
        frame_h, frame_w = self.cap.get(4), self.cap.get(3)
        index_x = int((lmList[8][0] / frame_w) * self.screen_width)
        index_y = int((lmList[8][1] / frame_h) * self.screen_height)
        self.right_hand_coords = (index_x, index_y)

        # Check for gun gesture (thumb and index up, others down)
        fingers = self.detector.fingersUp(hand)
        self.gun_flag = (fingers == [1, 1, 0, 0, 0])

        # Check for weapon switch gesture (thumb and pinky up, others down)
        current_weapon_gesture = (fingers == [1, 0, 0, 0, 1])
        current_time = time.time()

        # Weapon switching logic with cooldown
        if current_weapon_gesture:
            if not self.weapon_gesture_detected:
                # Gesture just started, check cooldown
                if current_time - self.last_weapon_switch_time >= 5:
                    # Trigger weapon switch
                    self.weapon_switch = True
                    self.last_weapon_switch_time = current_time
                    if self.debug_mode:
                        print("Weapon switch activated! (F key)")
                else:
                    if self.debug_mode:
                        print("Weapon switch cooldown active...")
                # Lock gesture detection while gesture is held
                self.weapon_gesture_detected = True
            else:
                # Gesture is still being held, do nothing
                self.weapon_switch = False
        else:
            # Gesture released, reset detection flag
            self.weapon_gesture_detected = False
            self.weapon_switch = False

        # Set weapon_flag for other uses
        self.weapon_flag = current_weapon_gesture

        if self.debug_mode and self.gun_flag:
            print("Gun gesture detected!")

    
    def get_movement_keys(self):
        """Return currently pressed movement keys based on left hand"""
        keys = []
        if self.move_forward:
            keys.append(pg.K_w)
        if self.move_left:
            keys.append(pg.K_a)
        if self.move_backward:
            keys.append(pg.K_s)
        if self.move_right:
            keys.append(pg.K_d)
        if self.weapon_switch:
            keys.append(pg.K_f)
        return keys
    
    def get_camera_movement(self):
        """Return camera movement delta based on right hand"""
        if not self.right_hand_coords:
            return 0
        
        current_x = self.right_hand_coords[0]
        
        # Initialize previous position if not set
        if self.prev_right_x == 0:
            self.prev_right_x = current_x
            return 0
        
        # Calculate movement delta
        dx = current_x - self.prev_right_x
        
        # Reduce deadzone for more responsive movement
        if abs(dx) < 5:  # Much smaller deadzone
            dx = 0
        
        # Enhanced sensitivity with smoothing
        base_sensitivity = 0.008  # Increased base sensitivity
        
        # Add acceleration for larger movements
        if abs(dx) > 50:
            movement = dx * base_sensitivity * 1.5  # Boost for fast movements
        elif abs(dx) > 20:
            movement = dx * base_sensitivity * 1.2  # Slight boost for medium movements
        else:
            movement = dx * base_sensitivity
        
        # Smooth the movement to prevent jitter
        movement = max(-0.15, min(0.15, movement))  # Clamp to prevent too fast rotation
        
        # Update previous position
        self.prev_right_x = current_x
        
        return movement
    
    def run(self):
        """Main loop for hand detection"""
        while True:
            ret, frame = self.cap.read()
            if not ret:
                continue
                
            hands, frame = self.detector.findHands(frame, draw=self.debug_mode)
            
            # Reset states (except weapon_switch which has its own logic)
            self.left_hand_present = False
            self.move_forward = False
            self.move_left = False
            self.move_backward = False
            self.move_right = False
            self.gun_flag = False
            self.weapon_flag = False
            self.right_hand_coords = None
            
            if hands:
                for hand in hands:
                    hand_type = hand['type']
                    
                    if hand_type == 'Left':
                        self.process_left_hand(hand)
                    elif hand_type == 'Right':
                        self.process_right_hand(hand)
            else:
                # No hands detected, reset weapon switch
                self.weapon_switch = False
                self.weapon_gesture_detected = False
            
            # # Display debug window
            # if self.debug_mode:
            #     cv2.imshow("Hand Tracking Debug", frame)
            #     if cv2.waitKey(1) & 0xFF == ord('q'):
            #         break
    
    def cleanup(self):
        """Clean up resources"""
        self.cap.release()
        cv2.destroyAllWindows()

# Example usage
if __name__ == "__main__":
    controller = DualHandController()
    try:
        controller.run()
    except KeyboardInterrupt:
        print("Stopping hand controller...")
    finally:
        controller.cleanup()