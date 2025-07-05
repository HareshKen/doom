import pygame as pg
import sys
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
from mouse import VirtualMouse  # Import the VirtualMouse class
from pause_menu import PauseMenu

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

        # Start the virtual mouse in a separate thread
        self.virtual_mouse = VirtualMouse()
        self.mouse_thread = threading.Thread(target=self.virtual_mouse.run, daemon=True)
        self.mouse_thread.start()

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
            # Hand gesture → Rotate player view
            if self.virtual_mouse.index_coords:
                dx = (self.virtual_mouse.index_coords[0] - self.virtual_mouse.prev_index_x) * 0.005
                self.player.angle += dx
                self.virtual_mouse.prev_index_x = self.virtual_mouse.index_coords[0]

            # Hand gesture → Fire weapon
            if self.virtual_mouse.fist_flag:
                if not self.player.shot and not self.weapon.reloading:
                    self.player.shot = True
                    self.weapon.fire()
            else:
                self.player.shot = False  # Reset shot flag when gesture ends

            self.player.update()
            self.raycasting.update()
            self.object_handler.update()
            self.weapon.update()
        
        pg.display.flip()
        self.delta_time = self.clock.tick(FPS)
        pg.display.set_caption(f'{self.clock.get_fps():.1f}')


    def draw(self):
        self.object_renderer.draw()
        self.weapon.draw()
        
        # Apply brightness overlay if needed
        self.pause_menu.apply_brightness(self.screen)
        
        # Draw pause menu if paused
        self.pause_menu.draw(self.screen)

    def check_events(self):
        self.global_trigger = False
        for event in pg.event.get():
            if event.type == pg.QUIT:
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
        while True:
            self.check_events()
            self.update()
            self.draw()


if __name__ == '__main__':
    game = Game()
    game.run()
