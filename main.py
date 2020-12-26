import pygame as pg


SIZE = WIDTH, HEIGHT = 700, 500  # Размеры окна

# Инициализация окна pygame
pg.init()
pg.display.set_caption("BombPredate")
screen = pg.display.set_mode(SIZE)

# Спрайты
all_sprites = pg.sprite.Group()
start_menu = pg.sprite.Group()  # Спрайты главное меню игры (например: кнопки)


class Button(pg.sprite.Sprite):
    def __init__(self, name, point, width=185, height=35, button_color=(38, 222, 255), text_color=(255, 255, 255)):
        """
        Спрайт кнопки

        :param name: название на кнопке
        :param point: (x, y) - точка, где будет располагаться левый верхний угол кнопки
        :param width: длинна кнопки
        :param height: ширина кнопки
        :param button_color: цвет кнопки
        :param text_color: цвет текста
        """
        super(Button, self).__init__()
        self.image = pg.Surface((width, height), pg.SRCALPHA, 32)
        self.rect = pg.Rect(*point, width, height)

        # Рисуем фон кнопки
        pg.draw.rect(self.image, button_color, (0, 0, width, height), border_radius=7)

        # Создаём текст и рисуем на кнопке
        font = pg.font.Font(None, 28)
        text = font.render(name, True, text_color)
        self.image.blit(text, (width / 2 - text.get_width() / 2, height / 2 - text.get_height() / 2))


def main():
    running = True

    button = Button("Начать игру", (50, 50))
    start_menu.add(button)

    # Основной цикл игры
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

        screen.fill((0, 0, 0))
        start_menu.draw(screen)
        pg.display.flip()

    pg.quit()


if __name__ == '__main__':
    main()
