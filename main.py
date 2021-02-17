import os
import random
import sys
from math import sqrt

import pygame


SIZE = WIDTH, HEIGHT = 700, 500  # Размеры окна
FPS = 60  # Количество кадром в секунду
PLAYER_VELOCITY = 2

# Инициализация окна pygame
pygame.init()
pygame.display.set_caption("BombPredate")
screen = pygame.display.set_mode(SIZE)

# События pygame
START_GAME = pygame.USEREVENT + 1
CONTINUE_GAME = pygame.USEREVENT + 2
PAUSE = pygame.USEREVENT + 3
MAIN_MENU = pygame.USEREVENT + 4
OPEN_TUTORIAL_PAGE = pygame.USEREVENT + 5
PLAYER_WON = pygame.USEREVENT + 6
ENEMY_WON = pygame.USEREVENT + 7

# Состояния игры
START_MENU = 100
PAUSE_MENU = 101
TUTORIAL_PAGE = 102
GAME = 103
GAME_ENDED_MENU = 104

# Основные спрайты
entities_sprites = pygame.sprite.Group()  # Спрайты сущностей (игроки)
items_sprites = pygame.sprite.Group()  # Спрайты препятсвий, предметов и т.д.
effects_sprites = pygame.sprite.Group()  # Спрайты эффектов
collide_game_sprites = pygame.sprite.Group()  # Спрайты игры, которые не могут пройти сквозь друг друга

cloud_sprites = pygame.sprite.Group()  # Спрайты облаков

# Спрайты меню
start_menu_sprites = pygame.sprite.Group()  # Спрайты главного меню
pause_menu_sprites = pygame.sprite.Group()  # Спрайты меню паузы
game_ended_sprites = pygame.sprite.Group()  # Спрайты меню окончания игры
tutorial_sprites = pygame.sprite.Group()  # Спрайты для страницы помощи


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


class Border(pygame.sprite.Sprite):
    def __init__(self, x1, y1, x2, y2):
        """
        Игровые границы. За пределами этих границ не могут заходить игроки и другие предметы

        :param x1: x первой координаты
        :param y1: y первой координаты
        :param x2: x второй координаты
        :param y2: y второй координаты
        """
        super(Border, self).__init__(collide_game_sprites)

        if x1 == x2:
            self.image = pygame.Surface([1, y2 - y1])
            self.rect = pygame.Rect(x1, y1, 1, y2 - y1)
        else:
            self.image = pygame.Surface([x2 - x1, 1])
            self.rect = pygame.Rect(x1, y1, x2 - x1, 1)


class Board:
    def __init__(self, cell_size):
        """
        Игровая доска, которая подстраивается под размеры окна игры

        :param cell_size: размер клетки
        """
        self.rows = (HEIGHT - 20) // cell_size
        self.columns = (WIDTH - 20) // cell_size
        self.board = [[None] * self.columns for _ in range(self.rows)]

        self.left = (WIDTH - 20) % cell_size // 2 + 10
        self.top = 5
        self.cell_size = cell_size

        self.width = cell_size * self.columns
        self.height = cell_size * self.rows

        for i in range(self.left, self.left + self.width + 1, self.width):
            Border(i, self.top, i, self.top + self.height + 1)

        for i in range(self.top, self.top + self.height + 1, self.height):
            Border(self.left, i, self.left + self.width + 1, i)

        self.loser = None
        self.players = []

    def render(self, surface):
        """
        Нарисовать доску на экране

        :param surface: pygame.Surface
        """
        for i in range(self.rows):
            for j in range(self.columns):
                pygame.draw.rect(
                    surface, (180, 219, 50),
                    (self.left + j * self.cell_size, self.top + i * self.cell_size,
                     self.cell_size, self.cell_size)
                )
                pygame.draw.rect(
                    surface, (157, 189, 53),
                    (self.left + j * self.cell_size, self.top + i * self.cell_size,
                     self.cell_size, self.cell_size), 1
                )

    def get_cell(self, pos):
        """
        Определяет клетку, на которой находится координата

        :param pos: координата x, y
        :return: выдаёт номер колонки и строки клетки
        """
        board_x, board_y = pos[0] - self.left, pos[1] - self.top
        row, column = board_y // self.cell_size, board_x // self.cell_size

        if board_x >= 0 and board_y >= 0 and row <= self.rows - 1 and column <= self.columns - 1:
            return row, column
        else:
            return None

    def add_player(self, player):
        """
        Добавить игрока на доску

        :param player: Entity, класс сущности
        """
        self.players.append(player)

    def kill_player_if_exists(self, x, y):
        """
        Убить игрока, если он стоит на клетке по координатам x, y

        :param x: строка
        :param y: столбец
        """
        # Начальные данные
        cr = (self.cell_size - 10) // 2  # радиус круга (моделька игрока)
        rx, ry = self.cell_size * y + self.left, self.cell_size * x + self.top  # x, y клетки, где взрывается бомба
        rh, rw = self.cell_size, self.cell_size  # высота и ширина клетки

        for player in self.players:
            cx, cy = player.rect.x + cr, player.rect.y + cr  # x, y точки O круга (моделька игрока)

            # Находим ближайшие координаты к кругу в пределах клетки
            if cx < rx:
                nearest_x = rx
            elif cx > rx + rw:
                nearest_x = rx + rw
            else:
                nearest_x = cx

            if cy < ry:
                nearest_y = ry
            elif cy > ry + rh:
                nearest_y = ry + rh
            else:
                nearest_y = cy

            # Находим растояние между игроком и клеткой и проверяем, меньше ли полученное растояние радиуса круга игрока
            # если да, то игрок пересекает клетку и игрок будет убит. Специально добавлена погрешность, чтобы игроки не
            # взрывались, если они пересекли пару пикселей
            if sqrt((cx - nearest_x) ** 2 + (cy - nearest_y) ** 2) + 3 <= cr:
                player.kill()

    def place_item(self, x, y, item):
        """
        Поставить спрайт на определённую клетку

        :param x: строка
        :param y: столбец
        :param item: спрайт
        """
        if self.board[x][y] is not None:
            self.board[x][y].kill()

        self.board[x][y] = item

    def delete_item(self, x, y):
        """
        Удалить спрайт с доски и убить его

        :param x: строка
        :param y: столбец
        """
        if self.board[x][y] is not None:
            if type(self.board[x][y]) is Bomb:
                self.board[x][y].start_explosion()
            else:
                self.board[x][y].kill()
                self.board[x][y] = None


class Entity(pygame.sprite.Sprite):
    up_key = pygame.K_w
    down_key = pygame.K_s
    right_key = pygame.K_d
    left_key = pygame.K_a
    bomb_key = pygame.K_e

    def __init__(self, board, cell_point=(0, 0), color=pygame.Color(255, 255, 255)):
        """
        Так называемая "сущность". Базовый класс для реализации игрока и противников.

        :param board: класс Board
        :param cell_point: позиция клетки, на которой будет первоначальная позиция сущности (row, column)
        """
        super(Entity, self).__init__(entities_sprites, collide_game_sprites)
        width = board.cell_size - 10

        # Основные перменнные
        self.board = board
        self.board.add_player(self)
        self.color = color
        self.image = pygame.Surface((width, width), pygame.SRCALPHA, 32)
        self.rect = pygame.Rect(
            board.left + 5 + board.cell_size * cell_point[1], board.top + 5 + board.cell_size * cell_point[0],
            width, width
        )

        # Рисуем игрока
        pygame.draw.circle(self.image, color, (width // 2, width // 2), width // 2)
        pygame.draw.circle(
            self.image,
            (int(color.r * .75), int(color.g * .75), int(color.b * .75)),
            (width // 2, width // 2), width // 2, 2
        )

        # Таймер для задержки создание бомб
        self.bomb_clock = pygame.time.Clock()
        self.bomb_timer = 300

        self.bomb_adder_clock = pygame.time.Clock()
        self.bomb_adder_timer = 0

        self.bombs = 3  # Количество бомб у игрока

    def move(self, x, y):
        """
        Движение сущности

        :param x: количество клеток по x
        :param y: количество клеток по y
        """
        def collided_sprites():
            s = pygame.sprite.spritecollide(self, collide_game_sprites, False, pygame.sprite.collide_mask)
            s.remove(self)
            return s

        self.rect.x += x
        i = x

        while collided_sprites():
            self.rect.x -= i // 2

        self.rect.y += y
        i = y

        while collided_sprites():
            self.rect.y -= i // 2

    def update(self, event=None):
        # Управление игроком
        pressed = pygame.key.get_pressed()
        mod_pressed = pygame.key.get_mods()

        if pressed[self.up_key]:
            self.move(0, -PLAYER_VELOCITY)
        if pressed[self.down_key]:
            self.move(0, PLAYER_VELOCITY)
        if pressed[self.left_key]:
            self.move(-PLAYER_VELOCITY, 0)
        if pressed[self.right_key]:
            self.move(PLAYER_VELOCITY, 0)
        if pressed[self.bomb_key] or mod_pressed & self.bomb_key:
            self.place_bomb()

        # Если у игрока меньше трёх бомб, то запустить таймер
        if self.bombs < 3:
            self.bomb_adder_timer += self.bomb_adder_clock.tick()

            # Если прошло 3 секунд и бомб у игрока меньше 3-х, то дадим игроку ещё одну бомбу
            if self.bomb_adder_timer >= 3000:
                self.bombs += 1
                self.bomb_adder_timer = 0
        else:
            self.bomb_adder_clock.tick()

    def place_bomb(self):
        """Поставить бомбу на место, где стоит данный игрок"""
        self.bomb_timer += self.bomb_clock.tick()  # Прибавляем пройденые тики

        if self.bomb_timer >= 300 and self.bombs > 0:
            Bomb(self.board, self.board.get_cell((self.rect.x + self.rect.w // 2, self.rect.y + self.rect.h // 2)))
            self.bombs -= 1  # Вычисть количество бомб у игрока
            self.bomb_timer = 0  # Сбрасываем таймер


class Player(Entity):
    def __init__(self, board, cell_point):
        """Сущность игрока"""
        super(Player, self).__init__(board, cell_point, pygame.Color(0, 255, 38))

    def kill(self):
        super(Player, self).kill()
        pygame.event.post(pygame.event.Event(ENEMY_WON))


class Enemy(Entity):
    up_key = pygame.K_UP
    down_key = pygame.K_DOWN
    right_key = pygame.K_RIGHT
    left_key = pygame.K_LEFT
    bomb_key = pygame.KMOD_CTRL

    def __init__(self, board, cell_point):
        """Сущность противника-бота"""
        super(Enemy, self).__init__(board, cell_point, pygame.Color(255, 74, 74))

    def kill(self):
        super(Enemy, self).kill()
        pygame.event.post(pygame.event.Event(PLAYER_WON))


class BoxParticle(pygame.sprite.Sprite):
    fire = [load_image(f"sawdust{i}.png") for i in range(1, 3)]  # частицы дерева

    def __init__(self, pos, dx, dy):
        """
        Спрайт опилки. Используется для эффекта взрыва коробки

        :param pos: координата, где появится опилка
        :param dx: скорость по x
        :param dy: скорость по y
        """
        super().__init__(effects_sprites)
        self.scale = 20  # изначальный размер частиц

        self.image = pygame.transform.scale(random.choice(self.fire), (self.scale, self.scale))
        self.rect = self.image.get_rect()

        self.velocity = [dx, dy]  # скорость полёта опилки
        self.rect.x, self.rect.y = pos  # координаты, откуда будет падать опилка

        self.distance = 15  # если опилка достигнет 15 пикселей, то она исчезнет

        self.collide_rect = (pos[0] - self.distance, pos[1] - self.distance, self.distance * 2, self.distance * 2)

    def update(self):
        # перемещаем частицу
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        # уменьшаем частицу для эффекта падения
        self.scale = self.scale - 2 if self.scale > 5 else self.scale
        self.image = pygame.transform.scale(self.image, (self.scale, self.scale))
        # убиваем, если частица ушла за экран
        if not self.rect.colliderect(self.collide_rect):
            self.kill()


class Box(pygame.sprite.Sprite):
    def __init__(self, board, cell_point=(0, 0)):
        """
        Спрайт коробки, разрушается бомбой

        :param board: класс доски
        :param cell_point: клетка, где расположена коробка
        """
        super(Box, self).__init__(items_sprites, collide_game_sprites)
        width = board.cell_size - 10
        color = pygame.Color(212, 169, 116)

        self.board = board
        self.cell_point = cell_point

        self.image = pygame.Surface((width, width), pygame.SRCALPHA, 32)
        self.rect = pygame.Rect(
            board.left + 5 + board.cell_size * cell_point[1], board.top + 5 + board.cell_size * cell_point[0],
            width, width
        )

        # Рисуем коробку
        pygame.draw.rect(self.image, color, (0, 0, width, width))
        pygame.draw.line(
            self.image,
            (int(color.r * .7), int(color.g * .7), int(color.b * .7)),
            (0, 0), (width, width), 8
        )
        pygame.draw.rect(
            self.image,
            (int(color.r * .75), int(color.g * .75), int(color.b * .75)),
            (0, 0, width, width), 9
        )

        board.place_item(*cell_point, self)

    def kill(self):
        super(Box, self).kill()

        # Эффект взрыва коробки
        position = (
            self.board.left + self.board.cell_size * self.cell_point[1] + self.board.cell_size // 2,
            self.board.top + self.board.cell_size * self.cell_point[0] + self.board.cell_size // 2
        )

        static_vel = range(1, 2)
        dynamic_vel = range(-2, 3)

        for _ in range(2):
            BoxParticle(position, random.choice(static_vel), random.choice(dynamic_vel))
        for _ in range(2):
            BoxParticle(position, -random.choice(static_vel), random.choice(dynamic_vel))
        for _ in range(2):
            BoxParticle(position, random.choice(dynamic_vel), random.choice(static_vel))
        for _ in range(2):
            BoxParticle(position, random.choice(dynamic_vel), -random.choice(static_vel))


class BombExplosion(pygame.sprite.Sprite):
    frames = [pygame.transform.scale(load_image(f"explosion{i}.png"), (50, 50)) for i in range(1, 9)]
    
    def __init__(self, pos):
        super(BombExplosion, self).__init__(effects_sprites)
        self.remaining_frames = iter(self.frames)

        self.image = next(self.remaining_frames)
        self.rect = self.image.get_rect()

        self.rect.x, self.rect.y = pos[0] - self.rect.w // 2, pos[1] - self.rect.h // 2

        self.clock = pygame.time.Clock()
        self.timer = 0

    def update(self):
        try:
            self.timer += self.clock.tick()

            if self.timer >= 50:
                self.image = next(self.remaining_frames)
                self.timer = 0
        except StopIteration:
            self.kill()
        
        
class Bomb(pygame.sprite.Sprite):
    def __init__(self, board, cell_point=(0, 0)):
        """
        Спрайт бомбы. После спайвна на доске нужно 1.5 секунд, чтобы взорваться

        :param board: доска
        :param cell_point: координата на доске, где должна стоять бомба
        """
        super(Bomb, self).__init__(items_sprites)

        width = board.cell_size - 20
        color = pygame.Color(59, 59, 59)

        self.image = pygame.Surface((width, width), pygame.SRCALPHA, 32)
        self.rect = pygame.Rect(
            board.left + 10 + board.cell_size * cell_point[1], board.top + 10 + board.cell_size * cell_point[0],
            width, width
        )

        # Рисуем бомбу
        pygame.draw.circle(self.image, color, (width // 2, width // 2), width // 2)
        pygame.draw.circle(
            self.image,
            (int(color.r * .75), int(color.g * .75), int(color.b * .75)),
            (width // 2, width // 2), width // 2, 2
        )
        pygame.draw.circle(self.image, (255, 133, 25), (self.rect.w // 2, self.rect.h // 2), 2)

        board.place_item(*cell_point, self)

        self.board = board
        self.cell_point = cell_point

        # Таймер для создания взрывов на поле
        self.clock = pygame.time.Clock()
        self.timer = 0

        self.exploding = False  # Статус взрыва
        self.exploded_boxes = 0  # Взорванные коробки
        self.explosion_up, self.explosion_down, self.explosion_left, self.explosion_right = [None] * 4  # Позиции взрыва

    def start_explosion(self):
        # Убиваем игрока, если он стоит на клетке с бомбой
        self.board.kill_player_if_exists(self.cell_point[0], self.cell_point[1])
        # Эффект взрыва
        BombExplosion((
            self.board.left + self.board.cell_size * self.cell_point[1] + self.board.cell_size // 2,
            self.board.top + self.board.cell_size * self.cell_point[0] + self.board.cell_size // 2
        ))

        # Скрыть изображение бомбы
        self.image.set_alpha(0)

        # Ставим начальные позиции для взрыва остальных клеток
        self.explosion_up, self.explosion_down = self.cell_point[0], self.cell_point[0]
        self.explosion_left, self.explosion_right = self.cell_point[1], self.cell_point[1]

        # Сбросим таймер и поставим статус бомбы как "взрывается"
        self.exploding = True
        self.timer = 0

    def update(self, event=None):
        self.timer += self.clock.tick()  # Добавим в таймер сколько прошло с прошлого обновления

        # Если проходит процесс взрыва бомбы
        if self.exploding:
            # Если прошло 0.035 секунды
            if self.timer >= 35:
                # Функция, которая удаляет предмет и убивает игрока если они есть на клетке
                def fun(*coords):
                    if self.board.board[coords[0]][coords[1]] is not None:
                        self.exploded_boxes += 1

                        if self.exploded_boxes >= 3:
                            self.exploding = False
                    elif self.exploded_boxes != 0:
                        self.exploded_boxes -= 0.75

                    BombExplosion((
                        self.board.left + self.board.cell_size * coords[1] + self.board.cell_size // 2,
                        self.board.top + self.board.cell_size * coords[0] + self.board.cell_size // 2
                    ))

                    self.board.kill_player_if_exists(*coords)
                    self.board.delete_item(*coords)

                # Проверяем доступность клеток и взрываем их
                if self.explosion_left > 0:
                    self.explosion_left -= 1
                    fun(self.cell_point[0], self.explosion_left)
                if self.explosion_right < self.board.columns - 1:
                    self.explosion_right += 1
                    fun(self.cell_point[0], self.explosion_right)
                if self.explosion_up > 0:
                    self.explosion_up -= 1
                    fun(self.explosion_up, self.cell_point[1])
                if self.explosion_down < self.board.rows - 1:
                    self.explosion_down += 1
                    fun(self.explosion_down, self.cell_point[1])

                # Если больше нет клеток для взрыва
                if self.explosion_left == 0 and self.explosion_right == self.board.columns - 1 \
                        and self.explosion_up == 0 and self.explosion_down == self.board.rows - 1 or not self.exploding:
                    self.board.board[self.cell_point[0]][self.cell_point[1]] = None
                    self.kill()

                self.timer = 0  # Сбрасываем таймер
        else:
            # Если прошло 1.5 секунд и бомба ещё не начала взрываться
            if self.timer >= 1500:
                self.start_explosion()


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


class GameInterface:
    def __init__(self, player, enemy):
        self.width = 600
        self.height = 40

        self.player = player
        self.enemy = enemy
        self.player_bombs = player.bombs
        self.enemy_bombs = enemy.bombs

        self.player_color = player.color
        self.enemy_color = enemy.color

        self.sprites = pygame.sprite.Group()
        self.player_bombs_text = self.make_text(self.player)
        self.enemy_bombs_text = self.make_text(self.enemy)
        self.sprites.add(self.player_bombs_text, self.enemy_bombs_text)

    def draw(self, surface):
        pygame.draw.rect(
            surface, self.player_color, 
            ((WIDTH - self.width) // 2, HEIGHT - self.height, self.width // 2, self.height + 5),
            border_top_left_radius=7
        )
        pygame.draw.rect(
            surface, (self.player_color[0] * .7, self.player_color[1] * .7, self.player_color[2] * .7),
            ((WIDTH - self.width) // 2, HEIGHT - self.height, self.width // 2, self.height + 5),  width=2,
            border_top_left_radius=7
        )
        pygame.draw.rect(
            surface, self.enemy_color,
            (WIDTH // 2, HEIGHT - self.height, self.width // 2, self.height + 5),
            border_top_right_radius=7
        )
        pygame.draw.rect(
            surface, (self.enemy_color[0] * .7, self.enemy_color[1] * .7, self.enemy_color[2] * .7),
            (WIDTH // 2, HEIGHT - self.height, self.width // 2, self.height + 5), width=2,
            border_top_right_radius=7
        )
        self.sprites.draw(surface)

    def update(self):
        if self.player.bombs != self.player_bombs:
            self.player_bombs = self.player.bombs
            self.sprites.remove(self.player_bombs_text)
            self.player_bombs_text = self.make_text(self.player)
            self.sprites.add(self.player_bombs_text)

        if self.enemy.bombs != self.enemy_bombs:
            self.enemy_bombs = self.enemy.bombs
            self.sprites.remove(self.enemy_bombs_text)
            self.enemy_bombs_text = self.make_text(self.enemy)
            self.sprites.add(self.enemy_bombs_text)

    def make_text(self, player):
        if player == self.player:
            return Text(
                f"Бомб: {self.player_bombs} из 3", (WIDTH - self.width // 2) // 2, HEIGHT - 18, 26, (0, 0, 0),
                font="YanoneKaffeesatz"
            )
        else:
            return Text(
                f"Бомб: {self.enemy_bombs} из 3", WIDTH // 2 + self.width // 4, HEIGHT - 18, 26, (255, 255, 255),
                font="YanoneKaffeesatz"
            )


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
            "Справка": OPEN_TUTORIAL_PAGE,
            "Выйти из игры": pygame.QUIT
        }, start_menu_sprites
    )

    Text("BombPredate", WIDTH / 2 + 2, HEIGHT / 5 + 3, 70, (0, 0, 0), 175, group=start_menu_sprites)  # Тень текста
    Text("BombPredate", WIDTH / 2, HEIGHT / 5, 70, (102, 222, 78), group=start_menu_sprites)


def make_game_ended_menu(text, color):
    """Создаёт заставку о законченной игре"""
    game_ended_sprites.empty()
    make_menu(
        {
            "Начать заново": START_GAME,
            "В главное меню": MAIN_MENU
        }, game_ended_sprites
    )

    Text(text, WIDTH / 2, HEIGHT / 5, 70, color, font="YanoneKaffeesatz", group=game_ended_sprites)


def main():
    running = True
    clock = pygame.time.Clock()

    background = pygame.transform.scale(load_image("bg.png"), (WIDTH, HEIGHT))  # Небо для фона

    # Затемнение для заставки об окончании игры
    bg_gameover = pygame.Surface((WIDTH, HEIGHT))
    bg_gameover.set_alpha(100)
    pygame.draw.rect(bg_gameover, (0, 0, 0), (0, 0, WIDTH, HEIGHT))

    # Картинка со справкой как играть
    tutorial_image = load_image("tutorial.png")

    # Создаём облака под фон
    for i in range(10):
        Cloud(cloud_sprites)

    make_start_menu()

    # Создаём интерфейс меню паузы
    make_menu(
        {
            "Продолжить": CONTINUE_GAME,
            "Начать заново": START_GAME,
            "В главное меню": MAIN_MENU
        }, pause_menu_sprites
    )

    Button("ОК", MAIN_MENU, (WIDTH - 190, HEIGHT - 40), groups=(tutorial_sprites,))

    current_event = START_MENU

    # Основной цикл игры
    while running:
        for event in pygame.event.get():
            # Если игра ещё не была запущена, то вызвать
            if current_event == START_MENU:
                start_menu_sprites.update(event)
            elif current_event == PAUSE_MENU:
                pause_menu_sprites.update(event)
            elif current_event == GAME_ENDED_MENU:
                game_ended_sprites.update(event)
            elif current_event == TUTORIAL_PAGE:
                tutorial_sprites.update(event)

            if event.type == pygame.QUIT:
                running = False
            # Если игрок начинает игру заново или впервые начал её
            if event.type == START_GAME:
                current_event = GAME
                items_sprites.empty()
                entities_sprites.empty()
                collide_game_sprites.empty()
                effects_sprites.empty()
                board = Board(45)

                for i in range(board.rows):
                    for j in range(board.columns):
                        if (i, j) not in [(0, 0), (0, 1), (1, 0), (1, 1), (board.rows - 1, board.columns - 1),
                                          (board.rows - 1, board.columns - 2), (board.rows - 2, board.columns - 1),
                                          (board.rows - 2, board.columns - 2)]:
                            Box(board, (i, j))

                player = Player(board, (0, 0))
                enemy = Enemy(board, (board.rows - 1, board.columns - 1))

                game_interface = GameInterface(player, enemy)

            # Если игрок был в меню паузы и решил продолжить игру
            if event.type == CONTINUE_GAME:
                current_event = GAME

            if current_event != GAME_ENDED_MENU:
                if event.type == PLAYER_WON:
                    current_event = GAME_ENDED_MENU
                    make_game_ended_menu("Выиграл зелёный игрок", (0, 255, 38))
                elif event.type == ENEMY_WON:
                    current_event = GAME_ENDED_MENU
                    make_game_ended_menu("Выиграл красный игрок", (255, 74, 74))

            if event.type == MAIN_MENU:
                current_event = START_MENU

            if event.type == OPEN_TUTORIAL_PAGE:
                current_event = TUTORIAL_PAGE

            # Если игрок нажал на кнопку
            if event.type == pygame.KEYDOWN:
                key = event.key

                if key == pygame.K_ESCAPE:
                    # Если игрок был в игре, то при нажатии ESC откроется меню паузы
                    if current_event == GAME:
                        current_event = PAUSE_MENU
                    # Если игрок был в меню паузы, то при нажатии ESC он вернётся в игру
                    elif current_event == PAUSE_MENU:
                        current_event = GAME

        # Ставим на фон изображение
        screen.blit(background, (0, 0))
        # Рисуем облака и обновляем их позиции на фоне
        cloud_sprites.update()
        cloud_sprites.draw(screen)

        # Если текущее состояние это сама игра
        if current_event == GAME:
            board.render(screen)  # Прорисуем доску

            # Обновим состояние спрайтов и прорисуем их
            entities_sprites.update()
            items_sprites.update()
            game_interface.update()
            effects_sprites.update()
            game_interface.draw(screen)
            items_sprites.draw(screen)
            entities_sprites.draw(screen)
            effects_sprites.draw(screen)
        # Если состояние игры это пауза
        elif current_event == PAUSE_MENU:
            pause_menu_sprites.draw(screen)  # Прорисуем спрайты меню паузы
        # Если состояние игры это заставка о конце игры
        elif current_event == GAME_ENDED_MENU:
            # Прорисуем доску и спрайты, чтобы на заднем фоне было видно, что произошло
            board.render(screen)
            effects_sprites.update()
            items_sprites.update()
            items_sprites.draw(screen)
            entities_sprites.draw(screen)
            effects_sprites.draw(screen)
            game_interface.draw(screen)

            screen.blit(bg_gameover, (0, 0))  # Сделаем картинку темнее, но видимой
            game_ended_sprites.draw(screen)  # Прорисовываем спрайты заставки
        elif current_event == TUTORIAL_PAGE:
            screen.blit(tutorial_image, (0, 0))
            tutorial_sprites.draw(screen)
        else:
            start_menu_sprites.draw(screen)

        clock.tick(FPS)
        pygame.display.flip()

    pygame.quit()


if __name__ == '__main__':
    main()
