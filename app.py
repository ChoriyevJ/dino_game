from sprite_cls import *
import random

pg.init()


class App:
    class Feed:
        def __init__(self, app):
            self.app = app
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
                self.rect.y += 10
            else:
                if self.quit_btn.draw():
                    self.app.running = False

                if self.restart_btn.draw():
                    self.app.__init__()
                    self.app.game_over = False

            self.app.screen.blit(self.surf, self.rect)

    def __init__(self):
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        self.clock = pg.time.Clock()
        self.running: bool = True
        self.iter: int = 0
        self.is_active: bool = False
        self.fps = FPS
        self.game_over: bool = GAME_OVER

        self.cactus_group = pg.sprite.Group()
        self.dino = Dino(self, 100, HEIGHT - 148, width=100, height=80)
        self.bg = Bg(self)
        self.fonts = dict(zip(tuple([i + 1 for i in range(len(pg.font.get_fonts()))]), pg.font.get_fonts()))
        self.font = pg.font.SysFont(self.fonts[1], FONT_SIZE, True)
        self.score_font = pg.font.SysFont(self.fonts[7], 30, True)
        self.button_font = pg.font.SysFont(self.fonts[7], 40, True)

        self.timer: int = 0
        self.time_counter: int = 1
        self.timer_start, self.timer_end = 3, 5
        self.generation_timer = random.randint(self.timer_start, self.timer_end)
        self.generate_start_x = 1000
        self.generate_end_x = 1200

        self.score: int = 0
        self.feed = self.Feed(self)

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

    def run(self):

        while self.running:
            self.iter += 1
            self.screen.fill(pg.Color('white'))

            self.bg.draw()
            self.bg.update()
            self.draw_score(self.score)

            self.dino.draw(self.screen)
            self.dino.update()

            for cactus in self.cactus_group:
                if not cactus.is_deleted:
                    cactus.draw()
                    cactus.update()
            if not self.game_over:
                if self.dino.state == "Idle":
                    self.draw_count_start(number=3 - self.iter // self.fps)
                if self.iter / self.fps > 3 and not self.is_active:
                    self.dino.state = "Run"
                    self.is_active = True

                self.timer += self.time_counter
                if self.dino.alive and self.timer // self.fps > self.generation_timer:
                    self.timer = 0
                    self.generation_timer = random.randint(self.timer_start, self.timer_end)
                    self.cactus_group.add(
                        Cactus(self, x=random.randrange(self.generate_start_x, self.generate_end_x), y=HEIGHT - 135)
                    )
                    if not len(self.cactus_group) % 1:
                        self.fps += 1
                        self.bg.speed += 0.2
                        self.time_counter += 0.1
                        if self.generate_start_x > WIDTH + 10: self.generate_start_x -= 10
                        if self.generate_end_x > self.generate_start_x + 10: self.generate_end_x -= 10
                        if self.timer_start > 1: self.timer_start -= 1
                        if self.timer_end > self.timer_start: self.timer_end -= 1

                if self.is_active and self.dino.alive:
                    self.score += 1
            else:
                self.feed.draw_end_screen()

            self.clock.tick(self.fps)
            pg.display.update()

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False
                if event.type == pg.KEYDOWN:
                    if (event.key == pg.K_SPACE
                            and not self.dino.do_jump
                            and self.dino.alive
                            and self.is_active
                    ):
                        self.dino.change_state("Jump")
                        self.dino.do_jump = True


if __name__ == "__main__":
    app = App()
    app.run()
    pg.quit()
