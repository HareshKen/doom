from sprite_object import *
from collections import deque


class Weapon(AnimatedSprite):
    def __init__(self, game, scale=0.4, animation_time=90):
        # Start with shotgun
        super().__init__(game=game, path='resources/sprites/weapon/shotgun/0.png', scale=scale, animation_time=animation_time)

        # Weapons dictionary
        self.weapons = {
            "shotgun": {
                "path": "resources/sprites/weapon/shotgun/",
                "scale": 0.4,
                "animation_time": 90,
                "damage": 70,
                "sound": "shotgun.wav",
                "range": 10.0  # Long range
            },
            "knife": {
                "path": "resources/sprites/weapon/knife/",
                "scale": 5.0,
                "animation_time": 60,
                "damage": 50,
                "sound": "knife.wav",
                "range": 2.0  # Short range - melee weapon
            }
        }

        self.current_weapon = "shotgun"  # Start with shotgun
        self.load_weapon(self.current_weapon)

        # Animation
        self.reloading = False
        self.frame_counter = 0

    def load_weapon(self, weapon_name):
        """Load textures and settings for the given weapon."""
        weapon = self.weapons[weapon_name]
        self.images = deque(
            [pg.transform.smoothscale(img, (img.get_width() * weapon["scale"], img.get_height() * weapon["scale"]))
             for img in self.get_images(weapon["path"])]
        )
        self.weapon_pos = (HALF_WIDTH - self.images[0].get_width() // 2,
                           HEIGHT - self.images[0].get_height())
        self.damage = weapon["damage"]
        self.range = weapon["range"]
        self.animation_time = weapon["animation_time"]
        self.sound_file = weapon["sound"]
        self.num_images = len(self.images)
        self.frame_counter = 0

    def switch_weapon(self, weapon_name):
        """Switch to a different weapon."""
        if weapon_name in self.weapons:
            self.current_weapon = weapon_name
            self.load_weapon(weapon_name)

    def animate_shot(self):
        if self.reloading:
            self.game.player.shot = False
            if self.animation_trigger:
                self.images.rotate(-1)
                self.image = self.images[0]
                self.frame_counter += 1
                if self.frame_counter == self.num_images:
                    self.reloading = False
                    self.frame_counter = 0

    def fire(self):
        """Player fires the current weapon."""
        if not self.reloading:  # Only fire if not already reloading
            # Play weapon sound
            sound = pg.mixer.Sound(self.game.sound.path + self.sound_file)
            sound.set_volume(0.4)
            sound.play()

            # Set reloading state
            self.reloading = True



    def draw(self):
        self.game.screen.blit(self.images[0], self.weapon_pos)

    def update(self):
        self.check_animation_time()
        self.animate_shot()
