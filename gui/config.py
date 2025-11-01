import pygame
import os

pygame.init()

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
DARK_GRAY = (100, 100, 100)
GREEN = (0, 200, 0)
BLUE = (0, 100, 200)
RED = (200, 0, 0)
GOLD = (255, 215, 0)

CARD_WIDTH = 50
CARD_HEIGHT = 75
CARD_SPACING = 10

FONT_SMALL = pygame.font.Font(None, 20)
FONT_MEDIUM = pygame.font.Font(None, 28)
FONT_LARGE = pygame.font.Font(None, 36)
FONT_TITLE = pygame.font.Font(None, 48)

COLORS = {
    'background': (30, 30, 40),
    'text': WHITE,
    'button': (60, 60, 80),
    'button_hover': (80, 80, 100),
    'card_bg': GRAY,
    'selected': GOLD,
    'player_bg': BLUE,
    'opponent_bg': RED,
    'board': GREEN
}

FONTS = {
    'small': FONT_SMALL,
    'medium': FONT_MEDIUM,
    'large': FONT_LARGE,
    'title': FONT_TITLE
}

def load_card_image(card_id):
    path = os.path.join('assets', 'images', f'{card_id}.png')
    if os.path.exists(path):
        img = pygame.image.load(path)
        return pygame.transform.scale(img, (CARD_WIDTH, CARD_HEIGHT))
    else:
        surface = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
        surface.fill(GRAY)
        return surface

def load_board_image():
    path = os.path.join('assets', 'images', 'board.png')
    if os.path.exists(path):
        return pygame.image.load(path)
    return None
