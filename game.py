import pygame
import sys
import random
import math

# Инициализация Pygame
pygame.init()

# Параметры окна
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Паровозик проекта')
clock = pygame.time.Clock()

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Параметры паровозика
train_length = 5
train_positions = [(WIDTH // 2, HEIGHT // 2) for _ in range(train_length)]
train_direction = pygame.Vector2(1, 0)
speed = 5

# Параметры парадоксальных объектов
paradox_objects = []
for _ in range(10):
    x = random.randint(50, WIDTH - 50)
    y = random.randint(50, HEIGHT - 50)
    paradox_objects.append(pygame.Rect(x, y, 20, 20))

# Параметры эффекта парадоксальности
paradox_mode = False
paradox_timer = 0
paradox_duration = 3000

# Основной игровой цикл
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Управление паровозиком
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        train_direction = pygame.Vector2(0, -1)
    elif keys[pygame.K_DOWN]:
        train_direction = pygame.Vector2(0, 1)
    elif keys[pygame.K_LEFT]:
        train_direction = pygame.Vector2(-1, 0)
    elif keys[pygame.K_RIGHT]:
        train_direction = pygame.Vector2(1, 0)

    # Движение паровозика
    new_head = train_positions[0] + train_direction * speed
    train_positions = [new_head] + train_positions[:-1]

    # Проверка на столкновение с парадоксальными объектами
    head_rect = pygame.Rect(new_head[0], new_head[1], 20, 20)
    for obj in paradox_objects:
        if head_rect.colliderect(obj):
            paradox_mode = not paradox_mode
            paradox_timer = pygame.time.get_ticks()
            paradox_objects.remove(obj)
            break

    # Обработка парадоксального режима
    if paradox_mode:
        if pygame.time.get_ticks() - paradox_timer > paradox_duration:
            paradox_mode = False
        else:
            # Парадоксальный эффект: направление движения зеркально
            train_direction = -train_direction

    # Отрисовка
    screen.fill(WHITE)
    for pos in train_positions:
        pygame.draw.rect(screen, BLUE, (*pos, 20, 20))

    for obj in paradox_objects:
        pygame.draw.rect(screen, RED, obj)

    pygame.display.flip()
    clock.tick(30)
