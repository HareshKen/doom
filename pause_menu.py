import pygame as pg
import sys
from settings import *

class Button:
    def __init__(self, x, y, width, height, text, font_size=32, color=(255, 255, 255), hover_color=(200, 200, 200)):
        self.rect = pg.Rect(x, y, width, height)
        self.text = text
        self.font_size = font_size
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.font = pg.font.Font(None, font_size)
        
    def draw(self, screen):
        color = self.hover_color if self.is_hovered else self.color
        pg.draw.rect(screen, color, self.rect, 2)
        
        text_surface = self.font.render(self.text, True, color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def handle_event(self, event):
        if event.type == pg.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pg.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False

class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val, label):
        self.rect = pg.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.label = label
        self.is_dragging = False
        self.font = pg.font.Font(None, 24)
        
    def draw(self, screen):
        # Draw slider background
        pg.draw.rect(screen, (100, 100, 100), self.rect)
        
        # Draw slider handle
        handle_x = self.rect.x + (self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width
        handle_rect = pg.Rect(handle_x - 5, self.rect.y - 5, 10, self.rect.height + 10)
        pg.draw.rect(screen, (255, 255, 255), handle_rect)
        
        # Draw label and value
        if isinstance(self.value, float):
            value_text = f"{self.value:.2f}"
        else:
            value_text = f"{self.value}"
        label_surface = self.font.render(f"{self.label}: {value_text}", True, (255, 255, 255))
        screen.blit(label_surface, (self.rect.x, self.rect.y - 30))
        
    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.is_dragging = True
                # Update value immediately when clicking
                rel_x = event.pos[0] - self.rect.x
                self.value = self.min_val + (rel_x / self.rect.width) * (self.max_val - self.min_val)
                self.value = max(self.min_val, min(self.max_val, self.value))
                return True
        elif event.type == pg.MOUSEBUTTONUP:
            self.is_dragging = False
        elif event.type == pg.MOUSEMOTION and self.is_dragging:
            rel_x = event.pos[0] - self.rect.x
            self.value = self.min_val + (rel_x / self.rect.width) * (self.max_val - self.min_val)
            self.value = max(self.min_val, min(self.max_val, self.value))
            return True
        return False

class PauseMenu:
    def __init__(self, game):
        self.game = game
        self.is_paused = False
        self.current_menu = "main"  # "main", "options"
        
        # Main menu buttons
        button_width, button_height = 200, 50
        center_x = WIDTH // 2 - button_width // 2
        
        self.resume_button = Button(center_x, HEIGHT // 2 - 100, button_width, button_height, "Resume")
        self.options_button = Button(center_x, HEIGHT // 2 - 25, button_width, button_height, "Options")
        self.quit_button = Button(center_x, HEIGHT // 2 + 50, button_width, button_height, "Quit")
        
        # Options menu elements
        self.back_button = Button(center_x, HEIGHT // 2 + 150, button_width, button_height, "Back")
        
        # Sliders
        slider_width, slider_height = 300, 10
        slider_x = WIDTH // 2 - slider_width // 2
        
        self.sensitivity_slider = Slider(slider_x, HEIGHT // 2 - 80, slider_width, slider_height, 
                                        0.0001, 0.001, MOUSE_SENSITIVITY, "Mouse Sensitivity")
        self.brightness_slider = Slider(slider_x, HEIGHT // 2 - 10, slider_width, slider_height, 
                                       0.5, 2.0, 1.0, "Brightness")
        # Get current music volume
        current_music_volume = pg.mixer.music.get_volume()
        
        self.volume_slider = Slider(slider_x, HEIGHT // 2 + 60, slider_width, slider_height,
                                   0.0, 1.0, current_music_volume, "Volume")
        
        # Store original settings
        self.original_sensitivity = MOUSE_SENSITIVITY
        self.original_brightness = 1.0
        self.original_volume = current_music_volume
        
        # Create overlay surface for brightness
        self.brightness_overlay = pg.Surface(RES)
        self.brightness_overlay.fill((0, 0, 0))  # Black overlay
        self.brightness_overlay.set_alpha(0)
        
        # Store current sensitivity value
        self.current_sensitivity = MOUSE_SENSITIVITY
        self.current_volume = current_music_volume
        
    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            pg.mouse.set_visible(True)
            pg.event.set_grab(False)
        else:
            pg.mouse.set_visible(False)
            pg.event.set_grab(True)
            self.current_menu = "main"
    
    def handle_events(self, event):
        if not self.is_paused:
            return
            
        if self.current_menu == "main":
            if self.resume_button.handle_event(event):
                self.toggle_pause()
            elif self.options_button.handle_event(event):
                self.current_menu = "options"
            elif self.quit_button.handle_event(event):
                pg.quit()
                sys.exit()
        elif self.current_menu == "options":
            if self.back_button.handle_event(event):
                self.current_menu = "main"
            else:
                # Handle sliders
                if self.sensitivity_slider.handle_event(event):
                    # Update mouse sensitivity
                    self.current_sensitivity = self.sensitivity_slider.value
                if self.brightness_slider.handle_event(event):
                    # Update brightness overlay
                    # Lower brightness value = darker screen (higher alpha)
                    alpha = int((2.0 - self.brightness_slider.value) * 127.5)
                    alpha = max(0, min(255, alpha))
                    self.brightness_overlay.set_alpha(alpha)
                if self.volume_slider.handle_event(event):
                    # Update volume
                    self.current_volume = self.volume_slider.value
                    # Update music volume
                    pg.mixer.music.set_volume(self.current_volume)
                    # Update sound effects volume
                    for sound in [self.game.sound.shotgun, self.game.sound.knife, 
                                 self.game.sound.npc_pain, self.game.sound.npc_death, 
                                 self.game.sound.npc_shot, self.game.sound.player_pain]:
                        sound.set_volume(self.current_volume)
    
    def draw(self, screen):
        if not self.is_paused:
            return
            
        # Draw semi-transparent background
        overlay = pg.Surface(RES)
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # Draw title
        title_font = pg.font.Font(None, 64)
        title_surface = title_font.render("PAUSED", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 200))
        screen.blit(title_surface, title_rect)
        
        if self.current_menu == "main":
            self.resume_button.draw(screen)
            self.options_button.draw(screen)
            self.quit_button.draw(screen)
        elif self.current_menu == "options":
            # Draw options title
            options_font = pg.font.Font(None, 48)
            options_surface = options_font.render("OPTIONS", True, (255, 255, 255))
            options_rect = options_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 150))
            screen.blit(options_surface, options_rect)
            
            self.sensitivity_slider.draw(screen)
            self.brightness_slider.draw(screen)
            self.volume_slider.draw(screen)
            self.back_button.draw(screen)
    
    def apply_brightness(self, screen):
        """Apply brightness overlay to the screen"""
        if self.brightness_slider.value != 1.0:
            screen.blit(self.brightness_overlay, (0, 0))
    
    def get_sensitivity(self):
        """Get current mouse sensitivity value"""
        return self.current_sensitivity
