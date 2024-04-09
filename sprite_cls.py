import pygame as pg
from pygame.image import load
from pygame.mouse import get_pos as mouse_pos
from pygame.mouse import get_pressed as mouse_pressed
from pygame import transform
from configs import *
import random
import os

pg.mixer.pre_init(44100, -16, 2, 512)


class Bg(pg.sprite.Sprite):

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.image = self.get_bg_image()
        self.rect = self.image.get_rect(topleft=(0, 0))

        self.tilemap = list()
        self.get_tileset()

        self.speed = SPEED

    def get_bg_image(self):
        bg_image = load("assets/deserttileset/BG.png")
        bg_image = transform.scale(bg_image, (WIDTH, HEIGHT))
        return bg_image

    def get_tileset(self):
        tileset = list()
        for i in range(2, 6, 3):
            image = load(f"assets/deserttileset/Tile/{i}.png")
            image = transform.scale(image, (TILE_SIZE, TILE_SIZE))
            tileset.append(image)

        for y in range(2):
            for x in range(WIDTH // TILE_SIZE + 2):
                image = tileset[1]
                if y == 0:
                    image = tileset[0]
                dx = x * TILE_SIZE
                dy = HEIGHT - (2 - y) * TILE_SIZE
                self.tilemap.append(
                    Tile(image, self, dx, dy)
                )
        self.tilemap = tuple(self.tilemap)

    def draw(self):
        self.app.screen.blit(self.image, self.rect)
        self.app.screen.blit(self.image, (self.rect.x + WIDTH, self.rect.y))

        for tile in self.tilemap:
            tile.draw()
            tile.update()

    def update(self):
        if not self.app.pause:
            if self.app.is_active:
                speed = self.speed / 4
                if self.app.dino.do_jump:
                    speed = (self.speed / 4) + JUMP_SPEED
                self.rect.x -= speed
                if self.rect.x < -WIDTH:
                    self.rect.x = 0


class Tile(pg.sprite.Sprite):
    def __init__(self, image: pg.Surface, bg: Bg, dx: int, dy: int):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(topleft=(dx, dy))
        self.bg = bg

    def draw(self):
        self.bg.app.screen.blit(self.image, self.rect)

    def update(self):
        if not self.bg.app.pause:
            if self.bg.app.is_active:
                speed = self.bg.speed
                if self.bg.app.dino.do_jump:
                    speed = self.bg.speed + JUMP_SPEED
                self.rect.x -= speed
                if self.rect.x <= - TILE_SIZE:
                    self.rect.x = WIDTH + 2 * TILE_SIZE + self.rect.x


class Dino(pg.sprite.Sprite):

    def __init__(self, app, x, y, width, height):
        pg.sprite.Sprite.__init__(self)
        self.app = app

        self.width: int = width
        self.height: int = height
        self.anim_speed = 6

        self.image_dict: dict = self.get_image_dict()
        self.state: str = "Idle"
        self.index: int = 0
        self.image = self.image_dict[self.state][self.index]
        self.rect: pg.Rect = self.image.get_rect(topleft=(x, y))

        self.JUMP_FORCE: int = JUMP_FORCE
        self.jump_delay: int = JUMP_DELAY
        self.jump_force: int = JUMP_FORCE
        self.sit_down: int = 0

        self.change_j_f = False
        self.alive: bool = True
        self.do_jump: bool = False

        self.fail_sound = pg.mixer.Sound('sounds/failing.mp3')
        self.jump_sound = pg.mixer.Sound('sounds/jumping.mp3')
        self.fail_sound.stop()

    def get_image_dict(self) -> dict:
        image_dict: dict = dict()
        dir_name: str = "assets/dino"
        for image_name in os.listdir(dir_name):
            key, _ = image_name.split(" ")
            data = image_dict.get(key, None)
            if data is None:
                image_dict[key] = list()
            image = load(f"{dir_name}/{image_name}")
            image = transform.scale(image, (self.width, self.height))
            image_dict[key].append(image)
        return image_dict

    def draw(self, screen):
        screen.blit(self.image, self.rect)
        # pg.draw.rect(screen, 'red', self.rect, 1)

    def update(self):
        if not self.app.pause:
            self.collision()
            self.animate()
            if self.do_jump:
                self.jump()
                if not self.do_jump and self.alive:
                    self.change_state(state="Run")

    def animate(self):
        if self.alive:
            if self.index < len(self.image_dict[self.state]) * self.anim_speed - 1:
                self.index += 1
            else:
                self.index = 0
        else:
            if self.index < len(self.image_dict[self.state]) * self.anim_speed - 1:
                self.index += 1
        self.image = self.image_dict[self.state][self.index // self.anim_speed]

    def change_state(self, state):
        self.state = state
        self.index = 0
        self.sit_down = 0
        if self.state == "Down":
            self.sit_down = 30
        elif self.state == "Dead":
            self.fail_sound.play()

    def jump(self):

        if self.jump_force > 0:
            self.rect.y -= (self.jump_force ** 2) // self.jump_delay
        else:
            self.rect.y += (self.jump_force ** 2) // self.jump_delay
        self.jump_force -= 1
        if abs(self.jump_force) == self.JUMP_FORCE + 1:
            self.do_jump = False
            self.jump_force = self.JUMP_FORCE

    def collision(self):
        if self.alive and self.app.timer > 20:
            # return
            for cactus in self.app.cactus_group:
                if cactus.rect.colliderect(self.rect.x, self.rect.y, self.rect.width // 2.5, self.rect.height / 1.2):
                    self.alive = False
                    self.app.game_over = True
                    self.app.bg.speed = 0
                    self.change_state(state="Dead")

            for hel in self.app.helicopter_group:
                if not hel.is_deleted:
                    if ((hel.rect.bottom >= self.rect.top + self.sit_down and (hel.rect.top < self.rect.bottom))
                            and hel.rect.left + 70 <= self.rect.right
                            and hel.rect.right - 100 >= self.rect.left):
                        self.alive = False
                        self.app.bg.speed = 0
                        self.app.game_over = True
                        self.change_state(state="Dead")


class Cactus(pg.sprite.Sprite):
    def __init__(self, app, x: int, y: int):
        super().__init__()
        self.app = app
        self.image = random.choice(self.get_image_list())
        self.rect = self.image.get_rect(topleft=(x, y))
        self.is_deleted = False

    def get_image_list(self) -> tuple:
        image_list = list()
        for i in range(1, 4, 2):
            image = load(f"assets/deserttileset/Objects/Cactus ({i}).png").convert_alpha()
            image = transform.scale(image, (40, 60))
            image_list.append(image)

        return tuple(image_list)

    def draw(self):
        self.app.screen.blit(self.image, self.rect)
        # pg.draw.rect(self.app.screen, 'blue', self.rect, 1)

    def update(self):
        if not self.app.pause:
            speed = self.app.bg.speed
            if self.app.dino.do_jump:
                speed = self.app.bg.speed + JUMP_SPEED
            self.rect.x -= speed
            if self.rect.x < -self.rect.width:
                self.is_deleted = True


class Helicopter(pg.sprite.Sprite):
    def __init__(self, app, x: int, y: int):
        super().__init__()
        self.app = app
        self.image_list = self.get_image_list()
        self.index = 0
        self.image = self.image_list[self.index]
        self.rect = self.image.get_rect(topleft=(x, y))
        self.is_deleted = False
        self.flying_sound = pg.mixer.Sound("sounds/helicopter.mp3")
        self.is_sound_playing = False

    def get_image_list(self) -> tuple:
        image_list = list()
        for i in range(1, 9):
            image = load(f"assets/separated_frames/helicopter_{i}.png").convert_alpha()
            image = transform.scale(image, (200, 66))
            image = transform.flip(image, True, False)
            image_list.append(image)
        image_list.extend(image_list)
        return tuple(image_list)

    def draw(self):
        self.app.screen.blit(self.image, self.rect)
        # pg.draw.rect(self.app.screen, 'blue', self.rect, 1)

    def update(self):
        if not self.app.pause:
            self.flying_sound.set_volume(1)
            self.animate(1)
            speed = self.app.bg.speed * 1.3
            if self.app.dino.do_jump:
                speed = self.app.bg.speed * 1.3 + JUMP_SPEED
            self.rect.x -= speed
            if self.rect.x < -self.rect.width:
                self.is_deleted = True
                self.flying_sound.stop()
        else:
            self.flying_sound.set_volume(0)

    def animate(self, anim_speed: int):
        self.index += 4
        if self.index > len(self.image_list) - 1:
            self.index = 0
        self.image = self.image_list[self.index]



class Button:
    def __init__(self, app, surf, width, height, x, y, color, text):
        self.app = app
        self.surf = surf
        self.rect = pg.Rect(x, y, width, height)
        self.color = color
        self.font_color = 'white'
        self.text = self.app.button_font.render(f'{text}', 1, self.font_color)

    def draw(self) -> bool:
        _click: bool = False
        pg.draw.rect(self.surf, self.color, self.rect)
        width = self.text.get_width()
        height = self.text.get_height()
        x = self.rect.x + (self.rect.width - width) // 2
        y = self.rect.y + (self.rect.height - height) // 2
        self.surf.blit(self.text, (x, y))
        if self.rect.x < mouse_pos()[0] < self.rect.x + self.rect.width and \
                self.rect.y < mouse_pos()[1] < self.rect.y + self.rect.height:
            if mouse_pressed()[0] == 1:
                _click = True
        return _click


class ImageButton(pg.sprite.Sprite):
    def __init__(self, class_, image_name, x, y, width, height, screen=None):
        super().__init__()
        self.app = class_
        self.image = self.get_image(image_name, width, height)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.screen = screen
        if not self.screen:
            self.screen = self.app.screen

    def get_image(self, image_name, width, height):
        image = load(f"assets/others/{image_name}.png")
        image = transform.scale(image, (width, height))
        return image

    def draw(self) -> bool:
        _click: bool = False
        width, height = self.rect.width, self.rect.height
        if self.rect.x < mouse_pos()[0] < self.rect.x + width and self.rect.y < mouse_pos()[1] < self.rect.y + height:
            if mouse_pressed()[0] == 1:
                _click = True
        self.screen.blit(self.image, self.rect)
        return _click
