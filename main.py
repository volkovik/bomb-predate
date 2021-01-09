import os
import random
import sys

import pygame


SIZE = WIDTH, HEIGHT = 700, 500  # Размеры окна
FPS = 60  # Количество кадром в секунду

# Инициализация окна pygame
pygame.init()
pygame.display.set_caption("BombPredate")
screen = pygame.display.set_mode(SIZE)

# События
START_GAME = pygame.USEREVENT + 1
CONTINUE_GAME = pygame.USEREVENT + 2
PAUSE = pygame.USEREVENT + 3

# Спрайты
game_sprites = pygame.sprite.Group()  # Спрайты игры
start_menu_sprites = pygame.sprite.Group()  # Спрайты главного меню
cloud_sprites = pygame.sprite.Group()  # Спрайты облаков
pause_menu_sprites = pygame.sprite.Group()  # Спрайты меню паузы


def load_image(name, colorkey=None):
    """
    Загрузить изображение из папки с ресурсами

    :param name: название файла
    :param colorkey: координаты пикселя, по которому будет обрезаться изображение
    :return: изображение
    """
    fullname = os.path.join("data", name)
    # если файл не существует, то выходим
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()

    image = pygame.image.load(fullname)

    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()

    return image


class Board:
    def __init__(self, cell_size):
        """
        Игровая доска, которая подстраивается под размеры окна игры

        :param cell_size: размер клетки
        """
        self.rows = (WIDTH - 20) // cell_size
        self.columns = (HEIGHT - 20) // cell_size
        self.board = [[None] * self.columns for _ in range(self.rows)]

        self.left = (WIDTH - 20) % cell_size // 2 + 10
        self.top = (HEIGHT - 20) % cell_size // 2 + 10
        self.cell_size = cell_size

    def render(self, surface):
        """
        Нарисовать доску на экране

        :param surface: pygame.Surface
        """
        for i in range(self.rows):
            for j in range(self.columns):
                pygame.draw.rect(
                    surface, (65, 194, 48),
                    (self.left + i * self.cell_size, self.top + j * self.cell_size,
                     self.cell_size, self.cell_size)
                )
                pygame.draw.rect(
                    surface, (66, 201, 48),
                    (self.left + i * self.cell_size, self.top + j * self.cell_size,
                     self.cell_size, self.cell_size), 1
                )

    def get_cell(self, mouse_pos):
        """
        Определяет клетку, на которой находится координата

        :param mouse_pos: координата x, y
        :return: выдаёт номер колонки и строки клетки
        """
        board_x, board_y = mouse_pos[0] - self.left, mouse_pos[1] - self.top
        row, column = board_x // self.cell_size, board_y // self.cell_size

        if board_x >= 0 and board_y >= 0 and row <= self.rows - 1 and column <= self.columns - 1:
            return row, column
        else:
            return None


class Button(pygame.sprite.Sprite):
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
        self.image = pygame.Surface((width, height), pygame.SRCALPHA, 32)
        self.rect = pygame.Rect(*point, width, height)

        self.name = name
        self.event = event
        self.x, self.y = point
        self.w, self.h = width, height
        self.button_color = button_color
        self.text_color = text_color

        # Рисуем кнопку
        self.font = pygame.font.Font(None, 28)
        self.draw(button_color, text_color)

    def draw(self, button_color, text_color):
        """
        Рисует кнопку

        :param button_color: цвет кнопки
        :param text_color: цвет текста
        """
        # Рисуем фон кнопки
        pygame.draw.rect(self.image, button_color, (0, 0, self.w, self.h), border_radius=7)
        pygame.draw.rect(
            self.image, (self.button_color[0] * .8, self.button_color[1] * .8, self.button_color[2] * .8),
            (0, 0, self.w, self.h), width=2, border_radius=7
        )

        # Показываем текст на кнопке
        text = self.font.render(self.name, True, text_color)
        self.image.blit(text, (self.w / 2 - text.get_width() / 2, self.h / 2 - text.get_height() / 2))

    def update(self, event=None):
        if event:
            # Когда кнопка мышки была нажата
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos_x, pos_y = event.pos
                # Если в момент нажатия мышки
                if self.x <= pos_x <= self.x + self.w and self.y <= pos_y <= self.y + self.h:
                    self.clicked = True

            # Когда кнопка мышки была отжата
            if event.type == pygame.MOUSEBUTTONUP:
                # Если в этот момент кнопка до этого была нажата и курсор до сих пор находится на кнопке, то происходят
                # заданные инструкции при создании кнопки
                if self.clicked:
                    pygame.event.post(pygame.event.Event(self.event))

                self.clicked = False

            # Когда курсор двигается
            if event.type == pygame.MOUSEMOTION:
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


class Cloud(pygame.sprite.Sprite):
    duplicate = False
    images = [load_image(f"cloud{i}.png") for i in range(1, 5)]

    def __init__(self, group, x=None, y=None, cloud_index=None):
        """
        Спрайт облака, украшение

        :param group: группа спрайтов
        :param x: расположение спрайта по координате x
        :param y: расположение спрайта по координате y
        :param cloud_index: вид облака
        """
        super(Cloud, self).__init__(group)
        if cloud_index:
            self.image = Cloud.images[cloud_index]
            self.cloud_index = cloud_index
        else:
            self.image = random.choice(Cloud.images)
            self.cloud_index = Cloud.images.index(self.image)

        self.rect = self.image.get_rect()
        if not x or not y:
            self.rect.x = self.x = random.randrange(WIDTH - self.rect.w)
            self.rect.y = random.randrange(HEIGHT - self.rect.h)
        else:
            self.rect.x = self.x = x
            self.rect.y = y

        self.vel = 60 / FPS

    def update(self, event=None):
        if not event:
            self.x -= self.vel  # из-за того, что rect может хранить только целые числа, то реальную координату x
            # облака мы храним в отдельном параметре
            self.rect.x = self.x

            if self.rect.x < 0 and not self.duplicate:
                self.duplicate = True
                Cloud(self.groups()[0], WIDTH - 1, self.rect.y, self.cloud_index)
            if self.rect.x == -self.rect.w:
                self.kill()


class Text(pygame.sprite.Sprite):
    def __init__(self, text, x, y, size, color, alpha=255, font="Sweet Macarons", group=None):
        """
        Текст-спрайт

        :param text: текст
        :param x: координата x середины текста
        :param y: координата y середины текста
        :param size: размер шрифта
        :param color: цвет текста
        :param alpha: прозрачность текста
        :param font: шрифт
        :param group: группа спрайтов
        """
        if group:
            super(Text, self).__init__(group)
        else:
            super(Text, self).__init__()

        self.font = pygame.font.Font(f"data/{font}.ttf", size)
        self.text = self.font.render(text, True, color)
        self.text.set_alpha(alpha)
        self.image = pygame.Surface((self.text.get_width(), self.text.get_height()), pygame.SRCALPHA, 32)
        self.rect = self.image.get_rect()
        self.rect.x = x - self.rect.w / 2
        self.rect.y = y - self.rect.h / 2
        self.image.blit(self.text, (0, 0))


def make_menu(button_names, sprite_group):
    """
    Создаёт кнопки в середине экрана

    :param button_names: словарь с названием кнопки и событием, которое будет воспроизводиться при нажатии
    :param sprite_group: группа спрайтов, в котором будут созданы кнопки
    """
    but_w, but_h = 185, 35

    start_x, start_y = WIDTH // 2 - but_w // 2, HEIGHT // 2 - but_h // 2 - (len(button_names) - 1) * 15

    for num, but in enumerate(button_names.items()):
        name, event = but
        Button(name, event, (start_x, start_y + (but_h + 15) * num), groups=(sprite_group,))


def make_start_menu():
    """Создаёт стартовое меню"""
    make_menu(
        {
            "Начать игру": START_GAME,
            "Выйти из игры": pygame.QUIT
        }, start_menu_sprites
    )

    Text("BombPredate", WIDTH / 2 + 2, HEIGHT / 5 + 3, 70, (0, 0, 0), 175, group=start_menu_sprites)  # Тень текста
    Text("BombPredate", WIDTH / 2, HEIGHT / 5, 70, (102, 222, 78), group=start_menu_sprites)


def main():
    running = True
    clock = pygame.time.Clock()

    background = pygame.transform.scale(load_image("bg.png"), (WIDTH, HEIGHT))
    board = Board(45)

    # Создаём облака под фон
    for i in range(10):
        Cloud(cloud_sprites)

    make_start_menu()

    # Создаём интерфейс меню паузы
    make_menu(
        {
            "Продолжить игру": CONTINUE_GAME,
            "Начать заново": START_GAME,
            "Выйти из игры": pygame.QUIT
        }, pause_menu_sprites
    )

    current_sprites = start_menu_sprites

    # Основной цикл игры
    while running:
        for event in pygame.event.get():
            current_sprites.update(event)

            if event.type == pygame.QUIT:
                running = False
            # Если игрок начинает игру заново или впервые начал её
            if event.type == START_GAME:
                current_sprites = game_sprites
            # Если игрок был в меню паузы и решил продолжить игру
            if event.type == CONTINUE_GAME:
                current_sprites = game_sprites
            # Если игрок нажал на кнопку
            if event.type == pygame.KEYDOWN:
                key = event.key

                if key == pygame.K_ESCAPE:
                    # Если игрок был в игре, то при нажатии ESC откроется меню паузы
                    if current_sprites == game_sprites:
                        current_sprites = pause_menu_sprites
                    # Если игрок был в меню паузы, то при нажатии ESC он вернётся в игру
                    elif current_sprites == pause_menu_sprites:
                        current_sprites = game_sprites

        # Ставим на фон изображение
        screen.blit(background, (0, 0))
        # Рисуем облака и обновляем их позиции на фоне
        cloud_sprites.update()
        cloud_sprites.draw(screen)
        # Рисуем текущие спрайты на экране и обновляем их
        current_sprites.draw(screen)
        current_sprites.update()

        if current_sprites == game_sprites:
            board.render(screen)

        clock.tick(FPS)
        pygame.display.flip()

    pygame.quit()


if __name__ == '__main__':
    main()
