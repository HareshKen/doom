import pygame as pg
import sys
import math
from settings import *


class Button:
    def __init__(self, x, y, width, height, text, font_size=48,
                 color=(255, 50, 0), hover_color=(255, 120, 50)):
        self.rect = pg.Rect(x, y, width, height)
        self.text = text
        self.font_size = font_size
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.font = pg.font.Font(None, font_size)

    def draw(self, screen):
        # Glow background if hovered
        bg_color = (100, 0, 0, 150) if self.is_hovered else (50, 0, 0, 100)
        bg_surface = pg.Surface((self.rect.width, self.rect.height), pg.SRCALPHA)
        pg.draw.rect(bg_surface, bg_color, bg_surface.get_rect(), border_radius=12)
        screen.blit(bg_surface, self.rect.topleft)

        # Text with red glow
        color = self.hover_color if self.is_hovered else self.color
        glow_surface = self.font.render(self.text, True, (color[0], color[1], color[2]))
        glow_rect = glow_surface.get_rect(center=self.rect.center)

        # Draw outer glow effect
        for glow_size in range(4, 0, -1):
            glow = self.font.render(self.text, True, (color[0], 0, 0))
            glow.set_alpha(50)
            glow = pg.transform.scale(glow, (int(glow_rect.width * 1.05), int(glow_rect.height * 1.05)))
            glow_rect2 = glow.get_rect(center=self.rect.center)
            screen.blit(glow, glow_rect2)

        # Draw actual text
        screen.blit(glow_surface, glow_rect)

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
        self.font = pg.font.Font(None, 36)

    def draw(self, screen):
        # Draw slider track
        track_color = (150, 0, 0)
        pg.draw.rect(screen, track_color, self.rect, border_radius=5)

        # Draw glowing handle
        handle_x = self.rect.x + (self.value - self.min_val) / (self.max_val - self.min_val) * self.rect.width
        handle_radius = 10
        glow_color = (255, 50, 0, 180)
        glow_surface = pg.Surface((handle_radius * 4, handle_radius * 4), pg.SRCALPHA)
        pg.draw.circle(glow_surface, glow_color, (handle_radius * 2, handle_radius * 2), handle_radius * 2)
        screen.blit(glow_surface, (handle_x - handle_radius * 2, self.rect.centery - handle_radius * 2),
                    special_flags=pg.BLEND_RGBA_ADD)

        pg.draw.circle(screen, (255, 120, 50), (int(handle_x), self.rect.centery), handle_radius)

        # Draw label and value
        value_text = f"{self.value:.2f}" if isinstance(self.value, float) else f"{self.value}"
        label_surface = self.font.render(f"{self.label}: {value_text}", True, (255, 50, 0))
        screen.blit(label_surface, (self.rect.x, self.rect.y - 40))

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.is_dragging = True
                self.update_value(event.pos[0])
                return True
        elif event.type == pg.MOUSEBUTTONUP:
            self.is_dragging = False
        elif event.type == pg.MOUSEMOTION and self.is_dragging:
            self.update_value(event.pos[0])
            return True
        return False

    def update_value(self, x_pos):
        rel_x = x_pos - self.rect.x
        self.value = self.min_val + (rel_x / self.rect.width) * (self.max_val - self.min_val)
        self.value = max(self.min_val, min(self.max_val, self.value))


class PauseMenu:
    def __init__(self, game):
        self.game = game
        self.is_paused = False
        self.current_menu = "main"  # "main", "options"

        # Buttons
        button_width, button_height = 300, 60
        center_x = WIDTH // 2 - button_width // 2
        self.resume_button = Button(center_x, HEIGHT // 2 - 100, button_width, button_height, "RESUME")
        self.options_button = Button(center_x, HEIGHT // 2, button_width, button_height, "OPTIONS")
        self.quit_button = Button(center_x, HEIGHT // 2 + 100, button_width, button_height, "QUIT")
        self.back_button = Button(center_x, HEIGHT // 2 + 180, button_width, button_height, "BACK")

        # Sliders
        slider_width, slider_height = 400, 10
        slider_x = WIDTH // 2 - slider_width // 2
        self.brightness_slider = Slider(slider_x, HEIGHT // 2 - 20, slider_width, slider_height,
                                        0.5, 2.0, 1.0, "BRIGHTNESS")
        self.volume_slider = Slider(slider_x, HEIGHT // 2 + 60, slider_width, slider_height,
                                    0.0, 1.0, pg.mixer.music.get_volume(), "VOLUME")

        # Brightness overlay
        self.brightness_overlay = pg.Surface(RES)
        self.brightness_overlay.fill((0, 0, 0))
        self.brightness_overlay.set_alpha(0)

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        pg.mouse.set_visible(self.is_paused)
        pg.event.set_grab(not self.is_paused)
        if not self.is_paused:
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
                if self.brightness_slider.handle_event(event):
                    alpha = int((2.0 - self.brightness_slider.value) * 127.5)
                    alpha = max(0, min(255, alpha))
                    self.brightness_overlay.set_alpha(alpha)
                if self.volume_slider.handle_event(event):
                    pg.mixer.music.set_volume(self.volume_slider.value)
                    for sound in [self.game.sound.shotgun, self.game.sound.knife,
                                  self.game.sound.npc_pain, self.game.sound.npc_death,
                                  self.game.sound.npc_shot, self.game.sound.player_pain]:
                        sound.set_volume(self.volume_slider.value)

    def draw(self, screen):
        if not self.is_paused:
            return

        # Dark overlay with slight red tint
        overlay = pg.Surface(RES, pg.SRCALPHA)
        overlay.fill((50, 0, 0, 200))
        screen.blit(overlay, (0, 0))

        # Pulsing DOOM title
        t = pg.time.get_ticks() / 300
        pulse_scale = 1.0 + 0.05 * math.sin(t)
        title_font = pg.font.Font(None, int(96 * pulse_scale))
        title_surface = title_font.render("PAUSED", True, (255, 0, 0))
        title_rect = title_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 200))
        screen.blit(title_surface, title_rect)

        if self.current_menu == "main":
            self.resume_button.draw(screen)
            self.options_button.draw(screen)
            self.quit_button.draw(screen)
        elif self.current_menu == "options":
            options_font = pg.font.Font(None, 64)
            options_surface = options_font.render("OPTIONS", True, (255, 50, 0))
            options_rect = options_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 150))
            screen.blit(options_surface, options_rect)

            self.brightness_slider.draw(screen)
            self.volume_slider.draw(screen)
            self.back_button.draw(screen)

    def apply_brightness(self, screen):
        if self.brightness_slider.value != 1.0:
            screen.blit(self.brightness_overlay, (0, 0))
