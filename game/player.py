from settings import *
import pygame as pg
import math
import glm

class Player:
    def __init__(self, game):
        self.game = game
        self.x, self.y = PLAYER_POS
        self.angle = PLAYER_ANGLE
        self.shot = False
        self.health = PLAYER_MAX_HEALTH
        self.score = 0  # 🪙 Add score counter
        self.rel = 0
        self.health_recovery_delay = 30
        self.time_prev = pg.time.get_ticks()
        self.diag_move_corr = 1 / math.sqrt(2)
        
        # Hand tracking integration flags
        self.use_hand_tracking = True
        self.hand_movement_enabled = True
        
        # Weapon switching cooldown to prevent rapid switching
        self.weapon_switch_cooldown = 0
        self.weapon_switch_delay = 300  # 300ms cooldown

    def recover_health(self):
        if self.check_health_recovery_delay() and self.health < PLAYER_MAX_HEALTH:
            self.health += 1

    def check_health_recovery_delay(self):
        time_now = pg.time.get_ticks()
        if time_now - self.time_prev > self.health_recovery_delay:
            self.time_prev = time_now
            return True

    def check_game_over(self):
        if self.health < 1:
            # Show Game Over screen and final score
            self.game.object_renderer.game_over()
            self.game.object_renderer.draw_final_score(self.score)
            pg.display.flip()

            # Wait for player input to restart
            waiting = True
            while waiting:
                for event in pg.event.get():
                    if event.type == pg.KEYDOWN:
                        if event.key == pg.K_RETURN or event.key == pg.K_r:  # Press Enter or R to restart
                            waiting = False
                pg.time.delay(100)  # Small delay to avoid CPU overuse

            self.game.new_game()

    def get_damage(self, damage):
        self.health -= damage
        self.game.object_renderer.player_damage()
        self.game.sound.player_pain.play()
        self.check_game_over()

    def add_score(self, points):
        """🏆 Add points to the score"""
        self.score += points

    def single_fire_event(self, event):
        """Handle mouse/keyboard firing events and weapon switching"""
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1 and not self.shot and not self.game.weapon.reloading:
                self.shot = True
                self.game.weapon.fire()  # Fire currently equipped weapon
        
        elif event.type == pg.KEYDOWN:
            # Handle F key for weapon switching
            if event.key == pg.K_f:
                current_time = pg.time.get_ticks()
                if current_time - self.weapon_switch_cooldown > self.weapon_switch_delay:
                    self.game.weapon.toggle_weapon()
                    self.weapon_switch_cooldown = current_time

    def keyboard_movement(self):
        """Fallback keyboard movement when hand tracking is not available"""
        sin_a = math.sin(self.angle)
        cos_a = math.cos(self.angle)
        dx, dy = 0, 0
        speed = PLAYER_SPEED * self.game.delta_time
        speed_sin = speed * sin_a
        speed_cos = speed * cos_a

        keys = pg.key.get_pressed()
        num_key_pressed = 0
        
        if keys[pg.K_w]:
            num_key_pressed += 1
            dx += speed_cos
            dy += speed_sin
        if keys[pg.K_s]:
            num_key_pressed += 1
            dx += -speed_cos
            dy += -speed_sin
        if keys[pg.K_a]:
            num_key_pressed += 1
            dx += speed_sin
            dy += -speed_cos
        if keys[pg.K_d]:
            num_key_pressed += 1
            dx += -speed_sin
            dy += speed_cos

        if num_key_pressed > 0:
            dx *= self.diag_move_corr
            dy *= self.diag_move_corr

        # Handle F key for weapon switching (continuous press check)
        if keys[pg.K_f]:
            current_time = pg.time.get_ticks()
            if current_time - self.weapon_switch_cooldown > self.weapon_switch_delay:
                self.game.weapon.toggle_weapon()
                self.weapon_switch_cooldown = current_time

        self.check_wall_collision(dx, dy)

    def movement(self):
        """Main movement function - uses hand tracking or falls back to keyboard"""
        # Check if hand tracking is available and left hand is detected
        if (self.use_hand_tracking and 
            hasattr(self.game, 'hand_controller') and 
            self.game.hand_controller.left_hand_present):
            
            # Hand tracking movement is handled in main.py's handle_hand_movement()
            # This function only handles keyboard fallback
            pass
        else:
            # Fallback to keyboard controls
            self.keyboard_movement()
        
        self.angle %= math.tau

    def check_wall(self, x, y):
        return (x, y) not in self.game.map.world_map

    def check_wall_collision(self, dx, dy):
        scale = PLAYER_SIZE_SCALE / self.game.delta_time
        if self.check_wall(int(self.x + dx * scale), int(self.y)):
            self.x += dx
        if self.check_wall(int(self.x), int(self.y + dy * scale)):
            self.y += dy

    def mouse_control(self):
        """Handle mouse control for camera rotation (fallback when hand tracking fails)"""
        # Check if hand tracking is available and right hand is detected
        if (self.use_hand_tracking and 
            hasattr(self.game, 'hand_controller') and 
            self.game.hand_controller.right_hand_coords):
            
            # Hand tracking camera control is handled in main.py
            return
        
        # Fallback to mouse control
        mx, my = pg.mouse.get_pos()
        if mx < MOUSE_BORDER_LEFT or mx > MOUSE_BORDER_RIGHT:
            pg.mouse.set_pos([HALF_WIDTH, HALF_HEIGHT])
        self.rel = pg.mouse.get_rel()[0]
        self.rel = max(-MOUSE_MAX_REL, min(MOUSE_MAX_REL, self.rel))
        self.angle += self.rel * MOUSE_SENSITIVITY * self.game.delta_time

    def update(self):
        self.movement()
        self.mouse_control()
        self.recover_health()

    @property
    def pos(self):
        return self.x, self.y

    @property
    def map_pos(self):
        return int(self.x), int(self.y)
