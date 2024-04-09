from sprite_cls import *
import sqlite3 as sql
import random
import json

pg.init()


class App:
    class Feed:
        def __init__(self, _class):
            self.app = _class
            self.rect = pg.Rect(0, -HEIGHT, WIDTH, HEIGHT)
            self.surf = pg.Surface((WIDTH, HEIGHT))
            self.surf.fill('black')
            self.alpha = 220
            self.surf.set_alpha(self.alpha)
            self.rect = self.surf.get_rect(topleft=(0, -HEIGHT))

            self.quit_btn = Button(
                app=self.app,
                surf=self.surf,
                text="QUIT",
                width=300,
                height=100,
                x=(WIDTH - 300) / 2,
                y=(HEIGHT - 200) / 2,
                color="brown"
            )

            self.restart_btn = Button(
                app=self.app,
                surf=self.surf,
                text="RESTART",
                width=300,
                height=100,
                x=(WIDTH - 300) / 2,
                y=(HEIGHT + 50) / 2,
                color="brown"
            )

        def draw_end_screen(self):
            if self.rect.y < 0:
                self.rect.y += 3
            else:
                if self.quit_btn.draw():
                    self.app.running = False

                if self.restart_btn.draw():
                    self.app.__init__()

                self.draw_score(self.app.score)

            self.app.screen.blit(self.surf, self.rect)

        def draw_score(self, score):
            score_text = self.app.score_font.render(f"Score: {score}", 1, (255, 255, 255))
            self.surf.blit(score_text, (
                10,
                10
            ))

    class PauseScreen:
        def __init__(self, _class, x, y, width, height, alpha=55, color=(184, 134, 11)):
            self.app = _class
            self.surf = pg.Surface((width, height))
            self.color = color
            self.surf.set_alpha(alpha)
            self.rect = self.surf.get_rect(topleft=(x, y))

            self.width = width
            self.height = 0
            self.is_draw_btn = False

        def draw(self):
            self.app.screen.blit(self.surf, self.rect)
            pg.draw.rect(self.surf, self.color, (0, 0, self.width, self.height))

        def update(self):
            self.is_draw_btn = False
            if self.height < self.rect.height:
                self.height += 5
            else:
                self.is_draw_btn = True

    class StartScreen:
        def __init__(self, class_):
            self.app = class_
            self.image = self.get_image()
            self.rect = self.image.get_rect(topleft=(0, 0))
            self.start_btn = Button(
                class_,
                class_.screen,
                300,
                100,
                x=(WIDTH - 300) / 2,
                y=(HEIGHT - 50) / 2,
                color=(184, 134, 11),
                text="Start Game"

            )
            self.load_width = 0
            self.close = False

        def get_image(self):

            image = load("assets/others/start_game_image.jpg").convert_alpha()
            image = transform.scale(image, (WIDTH, HEIGHT))
            return image

        def loading(self):
            end_loading = False
            width = 450
            height = 100

            if self.load_width < width - 20:
                self.load_width += 1
            else:
                end_loading = True

            if not end_loading:
                pg.draw.rect(self.app.screen, (255, 248, 220),
                             ((WIDTH - width) / 2, (HEIGHT - height) / 2, width, height),
                             border_radius=20)
                pg.draw.rect(self.app.screen, (0, 255, 0),
                             ((WIDTH - width + 20) / 2, (HEIGHT - height + 20) / 2, self.load_width, height - 20),
                             border_radius=20)

            return end_loading

        def draw(self):
            self.app.screen.blit(self.image, self.rect)

    def __init__(self):
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption("Dino-Run")
        pg.display.set_icon(load("assets/dino/Run (7).png"))
        self.clock = pg.time.Clock()
        self.running: bool = True
        self.iter: int = 0
        self.is_active: bool = False
        self.fps = FPS
        self.game_over: bool = GAME_OVER
        self.pause: bool = False

        self.helicopter_group = pg.sprite.Group()
        self.cactus_group = pg.sprite.Group()
        self.dino = Dino(self, 100, HEIGHT - 148, width=100, height=80)
        self.bg = Bg(self)
        self.current_hel = None
        self.fonts = dict(zip(tuple([i + 1 for i in range(len(pg.font.get_fonts()))]), pg.font.get_fonts()))
        self.font = pg.font.SysFont(self.fonts[1], FONT_SIZE, True)
        self.score_font = pg.font.SysFont(self.fonts[7], 30, True)
        self.button_font = pg.font.SysFont(self.fonts[7], 40, True)
        self.pause_btn = ImageButton(self,
                                     "pause",
                                     x=WIDTH - 50,
                                     y=10,
                                     width=40,
                                     height=40)
        self.pause_screen = self.PauseScreen(self,
                                             WIDTH // 2 - 300,
                                             HEIGHT // 2 - 150,
                                             600,
                                             300,
                                             color=(0, 191, 255))
        self.play_btn = ImageButton(self,
                                    "play",
                                    x=WIDTH // 2 - 50,
                                    y=HEIGHT // 2 - 50,
                                    width=100,
                                    height=100)
        self.start_screen = self.StartScreen(self)

        self.timer: int = TIMER
        self.time_counter: int = 1
        self.timer_start, self.timer_end = 3, 5
        self.generation_timer = random.randint(self.timer_start, self.timer_end)
        self.generate_start_x = WIDTH
        self.generate_end_x = self.generate_start_x + 500

        self.data = self.get_json_db_data()
        self.is_saved = False
        if not self.data.get('score', None):
            self.data['score'] = 0

        self.score: int = 0
        # self.last_score: int = self.data['score']
        self.last_score: int = self.get_score_from_db()
        self.feed = self.Feed(self)
        self.bg_sound = pg.mixer.Sound('sounds/bg_sound.mp3')
        self.bg_sound.set_volume(0)
        self.bg_sound.play()

    def get_score_from_db(self) -> int:
        self.db = sql.connect('db/data.db')
        self.cursor = self.db.cursor()
        self.cursor.execute('''
            create table if not exists score(
                score_id integer primary key autoincrement,
                score_value integer
            );
        ''')

        while True:
            self.cursor.execute('''select value from score''')
            try:
                score = self.cursor.fetchone()[0]
                break
            except Exception as e:
                self.cursor.execute('''
                    insert into score (value) values (?);
                ''', (0,))
        self.db.commit()
        return score

    def get_json_db_data(self):
        os.makedirs('db', exist_ok=True)
        while True:
            try:
                with open('db/db.json', 'r', encoding='utf-8') as db_file:
                    data = json.load(db_file)
                    return data
            except Exception as e:
                with open('db/db.json', 'w', encoding='utf-8') as db_file:
                    json.dump({}, db_file)

    def save_score_to_db(self):
        self.cursor.execute('''
            update score set value = ?
            where score_id = ?
        ''', (self.score, 1))
        self.db.commit()
        self.db.close()

    def save_json_db_data(self):
        with open('db/db.json', 'w', encoding='utf-8') as db_file:
            json.dump(self.data, db_file, ensure_ascii=False, indent=4)

    def draw_count_start(self, number: float) -> None:
        if number == 0:
            number: str = str()
        text: pg.font.SysFont = self.font.render(str(number), 1, (139, 0, 0))
        self.screen.blit(text, ((WIDTH - FONT_SIZE) // 2, (HEIGHT - FONT_SIZE) // 2))

    def draw_score(self, score):
        score_text = self.score_font.render(f"Score: {score}", 1, (139, 0, 0))
        self.screen.blit(score_text, (
            10,
            10
        ))

    def draw_last_score(self):
        score_text = self.score_font.render(f"High Score: {self.last_score}", 1, (139, 0, 0))
        self.screen.blit(score_text, (
            10,
            50
        ))

    def draw_speed(self):
        score_text = self.score_font.render(f"Speed: {self.bg.speed}", 1, (139, 0, 0))
        self.screen.blit(score_text, (
            10,
            50
        ))

    def draw_fps(self):
        score_text = self.score_font.render(f"FPS: {round(self.clock.get_fps(), 2)}", 1, (139, 0, 0))
        self.screen.blit(score_text, (
            10,
            90
        ))

    def draw_timer(self):
        score_text = self.score_font.render(f"Timer: {self.timer}", 1, (139, 0, 0))
        self.screen.blit(score_text, (
            10,
            130
        ))

    def draw_counter(self):
        score_text = self.score_font.render(f"Counter: {self.time_counter}", 1, (139, 0, 0))
        self.screen.blit(score_text, (
            10,
            170
        ))

    def draw_jump_force(self):
        score_text = self.score_font.render(f"Jump Force: {self.dino.JUMP_FORCE}", 1, (139, 0, 0))
        self.screen.blit(score_text, (
            10,
            210
        ))

    def draw_jump_delay(self):
        score_text = self.score_font.render(f"Jump Delay: {self.dino.jump_delay}", 1, (139, 0, 0))
        self.screen.blit(score_text, (
            10,
            250
        ))

    def draw_start_screen(self):
        running = True
        while running:
            self.screen.fill(pg.Color('white'))
            self.start_screen.draw()

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False

            if self.start_screen.loading():
                if self.start_screen.start_btn.draw():
                    self.start_screen.close = True
                    running = False

            self.clock.tick(self.fps)
            pg.display.update()

    def run(self):

        while self.running:
            self.iter += 1
            self.screen.fill(pg.Color('white'))

            self.bg.draw()
            self.bg.update()
            self.draw_score(self.score)
            self.draw_last_score()

            if not self.game_over and self.pause_btn.draw():
                self.pause = True

            if self.pause:
                self.pause_screen.draw()
                self.pause_screen.update()

            if self.pause_screen.is_draw_btn:
                if self.play_btn.draw():
                    self.pause = False
                    self.pause_screen.__init__(
                        self,
                        WIDTH // 2 - 300,
                        HEIGHT // 2 - 150,
                        600,
                        300,
                        color=(0, 191, 255)
                    )

            self.dino.draw(self.screen)
            self.dino.update()

            for cactus in self.cactus_group:
                if not cactus.is_deleted:
                    cactus.draw()
                    cactus.update()

            for hel in self.helicopter_group:
                if not hel.is_deleted:
                    if not hel.is_sound_playing:
                        hel.flying_sound.play()
                        hel.flying_sound.set_volume(2)
                        hel.is_sound_playing = True
                    hel.draw()
                    hel.update()
            if not self.game_over:
                # print(f"PLAYING")
                if self.dino.state == "Idle":
                    self.draw_count_start(number=3 - self.iter // self.fps)
                if self.iter / self.fps > 3 and not self.is_active:
                    self.dino.state = "Run"
                    self.is_active = True
                if not self.pause:
                    self.time_counter += 1

                    if self.dino.alive:
                        if self.time_counter >= self.timer:
                            self.time_counter = 0
                            shape = random.randint(1, 10)
                            if shape < 8:
                                self.cactus_group.add(
                                    Cactus(self, x=random.randrange(self.generate_start_x, self.generate_end_x),
                                           y=HEIGHT - 135)
                                )
                            else:
                                self.current_hel = Helicopter(self, x=random.randrange(self.generate_start_x,
                                                                                       self.generate_end_x),
                                                              y=HEIGHT - 5 * TILE_SIZE + 10)
                                self.helicopter_group.add(self.current_hel)
                            self.score += 1
                            if not (len(self.cactus_group) + len(self.helicopter_group)) % 2:
                                if self.timer > 35:
                                    self.timer -= 5
                            if not (len(self.cactus_group) + len(self.helicopter_group)) % 5:
                                if self.bg.speed < 20:
                                    self.bg.speed += 1
                                if self.dino.JUMP_FORCE > 10:
                                    self.dino.change_j_f = True
                                if self.dino.anim_speed > 2:
                                    self.dino.anim_speed -= 1
                        if self.dino.change_j_f and not self.dino.do_jump:
                            self.dino.JUMP_FORCE -= 1
                            self.dino.jump_force = self.dino.JUMP_FORCE
                            self.dino.jump_delay -= 1.6
                            self.dino.rect.y = HEIGHT - 148
                            self.dino.change_j_f = False

            else:
                if self.current_hel: self.current_hel.flying_sound.stop()
                self.bg_sound.stop()
                if not self.is_saved:
                    # print(f'saved score = ', self.score)
                    # self.data['score'] = self.score
                    # self.save_json_db_data()
                    if self.score > self.last_score:
                        self.save_score_to_db()
                    self.is_saved = True
                self.feed.draw_end_screen()

            self.clock.tick(self.fps)
            pg.display.update()

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False
                if self.dino.alive and self.is_active:
                    if event.type == pg.KEYDOWN:
                        if (event.key in (pg.K_SPACE, pg.K_w, pg.K_UP)
                                and not self.dino.do_jump):
                            self.dino.change_state("Jump")
                            self.dino.do_jump = True
                            self.dino.jump_sound.play()
                            self.dino.jump_sound.set_volume(0.25)

                        elif not self.dino.do_jump and event.key in (pg.K_s, pg.K_DOWN):
                            self.dino.change_state("Down")

                        elif event.key == pg.K_ESCAPE and not self.pause:
                            self.pause = True
                    if event.type == pg.KEYUP:
                        if event.key in (pg.K_s, pg.K_DOWN):
                            self.dino.change_state("Run")


if __name__ == "__main__":
    app = App()
    if not app.start_screen.close:
        app.draw_start_screen()
    if app.start_screen.close:
        app.run()
    pg.quit()
