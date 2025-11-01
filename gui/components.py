import pygame
from gui.config import *

class CardSprite(pygame.sprite.Sprite):
    def __init__(self, card, x, y):
        super().__init__()
        self.card = card
        self.image = load_card_image(card.id)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.selected = False
        self.hovered = False
    
    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
    
    def draw(self, screen):
        screen.blit(self.image, self.rect)
        
        if self.card.is_debuffed:
            pygame.draw.rect(screen, RED, self.rect, 3)
        
        if self.selected:
            pygame.draw.rect(screen, GOLD, self.rect, 4)
        elif self.hovered:
            pygame.draw.rect(screen, GREEN, self.rect, 2)
        
        strength_text = FONT_SMALL.render(str(self.card.get_current_strength()), True, WHITE)
        strength_bg = pygame.Surface((25, 20))
        strength_bg.fill(BLACK)
        strength_bg.set_alpha(180)
        screen.blit(strength_bg, (self.rect.x + 2, self.rect.y + 2))
        screen.blit(strength_text, (self.rect.x + 5, self.rect.y + 3))

class Button:
    def __init__(self, x, y, width, height, text, color=BLUE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hovered = False
    
    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
    
    def draw(self, screen):
        color = tuple(min(c + 30, 255) for c in self.color) if self.hovered else self.color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        
        text_surface = FONT_MEDIUM.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    
    def is_clicked(self, mouse_pos, mouse_pressed):
        return self.rect.collidepoint(mouse_pos) and mouse_pressed[0]
