import pygame as pg

SIZE = WIDTH, HEIGHT = 700, 500  # Размеры окна

# Инициализация окна pygame
pg.init()
pg.display.set_caption("BombPredate")
screen = pg.display.set_mode(SIZE)

# События
START_GAME = pg.USEREVENT + 1
CONTINUE_GAME = pg.USEREVENT + 2
PAUSE = pg.USEREVENT + 3

# Спрайты
game_sprites = pg.sprite.Group()  # Спрайты игры
start_menu_sprites = pg.sprite.Group()  # Спрайты главного меню
pause_menu_sprites = pg.sprite.Group()  # Спрайты меню паузы


class Button(pg.sprite.Sprite):
    clicked = False
    hovered = False

    def __init__(self, name, event, point, width=185, height=35,
                 button_color=(38, 222, 255), text_color=(255, 255, 255), groups=tuple()):
        """
        Спрайт кнопки

        :param name: название на кнопке
        :param event: тип события, которое будет вызвано при нажатии кнопки
        :param point: (x, y) - точка, где будет располагаться левый верхний угол кнопки
        :param width: длинна кнопки
        :param height: ширина кнопки
        :param button_color: цвет кнопки
        :param text_color: цвет текста
        """
        super(Button, self).__init__(*groups)
        self.image = pg.Surface((width, height), pg.SRCALPHA, 32)
        self.rect = pg.Rect(*point, width, height)

        self.name = name
        self.event = event
        self.x, self.y = point
        self.w, self.h = width, height
        self.button_color = button_color
        self.text_color = text_color

        # Рисуем кнопку
        self.font = pg.font.Font(None, 28)
        self.draw(button_color, text_color)

    def draw(self, button_color, text_color):
        """
        Рисует кнопку

        :param button_color: цвет кнопки
        :param text_color: цвет текста
        """
        # Рисуем фон кнопки
        pg.draw.rect(self.image, button_color, (0, 0, self.w, self.h), border_radius=7)
        pg.draw.rect(
            self.image, (self.button_color[0] * .8, self.button_color[1] * .8, self.button_color[2] * .8),
            (0, 0, self.w, self.h), width=2, border_radius=7
        )

        # Показываем текст на кнопке
        text = self.font.render(self.name, True, text_color)
        self.image.blit(text, (self.w / 2 - text.get_width() / 2, self.h / 2 - text.get_height() / 2))

    def update(self, *args):
        if args:
            event = args[0]
        else:
            event = None

        if event:
            # Когда кнопка мышки была нажата
            if event.type == pg.MOUSEBUTTONDOWN:
                pos_x, pos_y = event.pos
                # Если в момент нажатия мышки
                if self.x <= pos_x <= self.x + self.w and self.y <= pos_y <= self.y + self.h:
                    self.clicked = True

            # Когда кнопка мышки была отжата
            if event.type == pg.MOUSEBUTTONUP:
                # Если в этот момент кнопка до этого была нажата и курсор до сих пор находится на кнопке, то происходят
                # заданные инструкции при создании кнопки
                if self.clicked:
                    pg.event.post(pg.event.Event(self.event))

                self.clicked = False

            # Когда курсор двигается
            if event.type == pg.MOUSEMOTION:
                pos_x, pos_y = event.pos
                # Если курсор находится на кнопке
                if self.x <= pos_x <= self.x + self.w and self.y <= pos_y <= self.y + self.h:
                    self.hovered = True
                else:
                    self.hovered = False
                    self.clicked = False

            # В зависимости от приоритетов, кнопка будет отображаться темнее
            if self.clicked:
                self.draw((self.button_color[0] * .8, self.button_color[1] * .8, self.button_color[2] * .8),
                          self.text_color)
            elif self.hovered:
                self.draw((self.button_color[0] * .95, self.button_color[1] * .95, self.button_color[2] * .95),
                          self.text_color)
            else:
                self.draw(self.button_color, self.text_color)


def make_menu(button_names, sprite_group):
    but_w, but_h = 185, 35

    start_x, start_y = WIDTH // 2 - but_w // 2, HEIGHT // 2 - but_h // 2 - (len(button_names) - 1) * 15

    for num, but in enumerate(button_names.items()):
        name, event = but
        Button(name, event, (start_x, start_y + (but_h + 15) * num), groups=(sprite_group,))


def main():
    running = True

    make_menu(
        {
            "Начать игру": START_GAME,
            "Выйти из игры": pg.QUIT
        }, start_menu_sprites
    )
    make_menu(
        {
            "Продолжить игру": CONTINUE_GAME,
            "Начать заново": START_GAME,
            "Выйти из игры": pg.QUIT
        }, pause_menu_sprites
    )

    current_sprites = start_menu_sprites

    # Основной цикл игры
    while running:
        for event in pg.event.get():
            current_sprites.update(event)

            if event.type == pg.QUIT:
                running = False
            # Если игрок начинает игру заново или впервые начал её
            if event.type == START_GAME:
                current_sprites = game_sprites
            # Если игрок был в меню паузы и решил продолжить игру
            if event.type == CONTINUE_GAME:
                current_sprites = game_sprites
            # Если игрок нажал на кнопку
            if event.type == pg.KEYDOWN:
                key = event.key

                if key == pg.K_ESCAPE:
                    # Если игрок был в игре, то при нажатии ESC откроется меню паузы
                    if current_sprites == game_sprites:
                        current_sprites = pause_menu_sprites
                    # Если игрок был в меню паузы, то при нажатии ESC он вернётся в игру
                    elif current_sprites == pause_menu_sprites:
                        current_sprites = game_sprites

        screen.fill((0, 0, 0))
        current_sprites.draw(screen)
        pg.display.flip()

    pg.quit()


if __name__ == '__main__':
    main()
