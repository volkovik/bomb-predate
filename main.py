import pygame


SIZE = WIDTH, HEIGHT = 700, 500  # Размеры окна

# Инициализация окна pygame
pygame.init()
pygame.display.set_caption("BombPredate")
screen = pygame.display.set_mode(SIZE)


def main():
    running = True

    # Основной цикл игры
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((0, 0, 0))
        pygame.display.flip()

    pygame.quit()


if __name__ == '__main__':
    main()
