import pygame as pg
import sys
import os
import threading
from settings import *
from map import *
from player import *
from raycasting import *
from object_renderer import *
from sprite_object import *
from object_handler import *
from weapon import *
from sound import *
from pathfinding import *
from dual_hand_mouse import DualHandController  # Import the new dual hand controller
from pause_menu import PauseMenu

sys.path.append(os.path.abspath('..'))
from cvzone.HandTrackingModule import HandDetector

class Game:
    def __init__(self):
        pg.init()
        pg.mouse.set_visible(False)
        self.screen = pg.display.set_mode(RES)
        pg.event.set_grab(True)
        self.clock = pg.time.Clock()
        self.delta_time = 1
        self.global_trigger = False
        self.global_event = pg.USEREVENT + 0
        pg.time.set_timer(self.global_event, 40)

        # Start the dual hand controller in a separate thread
        self.hand_controller = DualHandController()
        self.hand_thread = threading.Thread(target=self.hand_controller.run, daemon=True)
        self.hand_thread.start()

        self.new_game()

    def new_game(self):
        self.map = Map(self)
        self.player = Player(self)
        self.object_renderer = ObjectRenderer(self)
        self.raycasting = RayCasting(self)
        self.object_handler = ObjectHandler(self)
        self.weapon = Weapon(self)
        self.sound = Sound(self)
        self.pathfinding = PathFinding(self)
        self.pause_menu = PauseMenu(self)
        pg.mixer.music.play(-1)

    def update(self):
        # Only update game if not paused
        if not self.pause_menu.is_paused:
            # Right hand gesture → Rotate player view
            camera_movement = self.hand_controller.get_camera_movement()
            if camera_movement != 0:
                self.player.angle -= camera_movement  # Apply camera rotation

            # Right hand gesture → Fire weapon
            if self.hand_controller.gun_flag:
                if not self.player.shot and not self.weapon.reloading:
                    self.player.shot = True
                    self.weapon.fire()
            else:
                self.player.shot = False  # Reset shot flag when gesture ends

            # Left hand gestures → Movement and weapon switching
            self.handle_hand_movement()

            self.player.update()
            self.raycasting.update()
            self.object_handler.update()
            self.weapon.update()
            
            pg.display.flip()
        self.delta_time = self.clock.tick(FPS)
        pg.display.set_caption(f'{self.clock.get_fps():.1f}')

    def handle_hand_movement(self):
        """Handle movement and weapon switching based on left hand gestures"""
        # Apply movement based on finger bending
        sin_a = math.sin(self.player.angle)
        cos_a = math.cos(self.player.angle)
        dx, dy = 0, 0
        speed = PLAYER_SPEED * self.delta_time
        speed_sin = speed * sin_a
        speed_cos = speed * cos_a

        num_key_pressed = 0
        
        # Movement controls via left hand finger bending
        if self.hand_controller.move_forward:  # Thumb bent -> W
            num_key_pressed += 1
            dx += speed_cos
            dy += speed_sin
        if self.hand_controller.move_backward:  # Middle finger bent -> S
            num_key_pressed += 1
            dx += -speed_cos
            dy += -speed_sin
        if self.hand_controller.move_left:  # Index finger bent -> A
            num_key_pressed += 1
            dx += speed_sin
            dy += -speed_cos
        if self.hand_controller.move_right:  # Ring finger bent -> D
            num_key_pressed += 1
            dx += -speed_sin
            dy += speed_cos

        # Apply diagonal movement correction
        if num_key_pressed > 0:
            dx *= self.player.diag_move_corr
            dy *= self.player.diag_move_corr
            
        # Weapon switching via left hand fist gesture (F key equivalent)
        if self.hand_controller.weapon_switch:
            self.weapon.toggle_weapon()
        
        # Apply movement if there's any
        if dx != 0 or dy != 0:
            self.player.check_wall_collision(dx, dy)
        
        self.player.angle %= math.tau

    def draw(self):
        self.object_renderer.draw()
        self.weapon.draw()
        
        # Draw hand tracking status
        self.draw_hand_status()
        
        # Apply brightness overlay if needed
        self.pause_menu.apply_brightness(self.screen)
        
        # Draw pause menu if paused
        self.pause_menu.draw(self.screen)

    def draw_hand_status(self):
        """Draw hand tracking status and active controls below the health digits"""
        font = pg.font.Font(None, 24)
        
        # Place directly below health digits
        base_x = 0  # Same X as health
        base_y = self.object_renderer.digit_size + 10  # Below health digits with 10px gap

        # Left hand status
        if self.hand_controller.left_hand_present:
            left_status = "LEFT HAND: "
            active_controls = []
            if self.hand_controller.move_forward: active_controls.append("W")
            if self.hand_controller.move_left: active_controls.append("A")
            if self.hand_controller.move_backward: active_controls.append("S")
            if self.hand_controller.move_right: active_controls.append("D")
            if self.hand_controller.weapon_switch: active_controls.append("1")
            
            if active_controls:
                left_status += ", ".join(active_controls)
            else:
                left_status += "READY"
            
            left_surface = font.render(left_status, True, (0, 255, 0))
            self.screen.blit(left_surface, (base_x, base_y))
        else:
            left_surface = font.render("LEFT HAND: NOT DETECTED", True, (255, 0, 0))
            self.screen.blit(left_surface, (base_x, base_y))
        
        # Right hand status (below left hand status)
        base_y += 30  # Stack under left hand text
        if self.hand_controller.right_hand_coords:
            right_status = "RIGHT HAND: "
            if self.hand_controller.gun_flag:
                right_status += "FIRING 🔫"
            else:
                right_status += "AIMING"
            
            right_surface = font.render(right_status, True, (0, 255, 0))
            self.screen.blit(right_surface, (base_x, base_y))
        else:
            right_surface = font.render("RIGHT HAND: NOT DETECTED", True, (255, 0, 0))
            self.screen.blit(right_surface, (base_x, base_y))



    def check_events(self):
        self.global_trigger = False
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.hand_controller.cleanup()
                pg.quit()
                sys.exit()
            elif event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                self.pause_menu.toggle_pause()
            elif event.type == self.global_event:
                self.global_trigger = True
                        
            # Handle pause menu events
            self.pause_menu.handle_events(event)
                        
            # Only handle player events if not paused
            if not self.pause_menu.is_paused:
                self.player.single_fire_event(event)

    def run(self):
        try:
            while True:
                self.check_events()
                self.update()
                self.draw()
                pg.display.flip()
        except KeyboardInterrupt:
            self.hand_controller.cleanup()
            pg.quit()
            sys.exit()

if __name__ == '__main__':
    game = Game()
    game.run()