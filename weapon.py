from sprite_object import *
from collections import deque


class Weapon(AnimatedSprite):
    def __init__(self, game, scale=0.4, animation_time=90):
        # Start with shotgun sprite
        super().__init__(game=game, path='resources/sprites/weapon/shotgun/0.png', scale=scale, animation_time=animation_time)

        # Weapons dictionary
        self.weapons = {
            "shotgun": {
                "path": "resources/sprites/weapon/shotgun/",
                "scale": 0.4,
                "animation_time": 90,
                "damage": 70,
                "sound": "shotgun.wav",
                "range": 10.0,          # Long range
                "max_ammo": 100          # Start with 10 shells
            },
            "knife": {
                "path": "resources/sprites/weapon/knife/",
                "scale": 5.0,
                "animation_time": 60,
                "damage": 50,
                "sound": "knife.wav",
                "range": 2.0,           # Melee range
                "max_ammo": float('inf')  # Infinite for melee
            }
        }

        # 🔥 Track current ammo separately
        self.weapon_ammo = {
            "shotgun": self.weapons["shotgun"]["max_ammo"],
            "knife": self.weapons["knife"]["max_ammo"]
        }

        self.current_weapon = "shotgun"  # Start with shotgun
        self.load_weapon(self.current_weapon)
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
        self.ammo = self.weapon_ammo[weapon_name]  # 🔥 Load existing ammo count

    def switch_weapon(self, weapon_name):
        """Switch to a different weapon only if it's usable."""
        if weapon_name in self.weapons:
            # 🔥 Prevent switching to shotgun if out of ammo
            if weapon_name == "shotgun" and self.weapon_ammo["shotgun"] == 0:
                print("❌ Shotgun is out of ammo! Staying with current weapon.")
                return
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
        if not self.reloading and self.ammo > 0:
            # Play weapon sound
            sound = pg.mixer.Sound(self.game.sound.path + self.sound_file)
            sound.set_volume(0.4)
            sound.play()

            # Start reload animation
            self.reloading = True

            # 🔥 Reduce ammo globally
            if self.ammo != float('inf'):
                self.ammo -= 1
                self.weapon_ammo[self.current_weapon] = self.ammo

            # 🔥 Auto-switch to knife if out of shotgun ammo
            if self.ammo == 0 and self.current_weapon == "shotgun":
                print("🔄 Out of ammo! Switching to knife.")
                self.switch_weapon("knife")
        elif self.ammo == 0:
            # 🔥 Optional: Play empty click sound
            empty_sound = pg.mixer.Sound(self.game.sound.path + "empty_click.wav")
            empty_sound.set_volume(0.5)
            empty_sound.play()

    def draw(self):
        # Draw weapon sprite
        self.game.screen.blit(self.images[0], self.weapon_pos)

        # Draw ammo counter
        ammo_text = f"{self.ammo}" if self.ammo != float('inf') else "max"
        font = pg.font.Font(None, 36)
        ammo_surface = font.render(f"Ammo: {ammo_text}", True, (255, 255, 255))
        self.game.screen.blit(ammo_surface, (WIDTH - 180, HEIGHT - 50))

    def update(self):
        self.check_animation_time()
        self.animate_shot()
