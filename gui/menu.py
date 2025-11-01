import pygame
from gui.config import COLORS

class Button:
    def __init__(self, x, y, width, height, text, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.hovered = False
    
    def draw(self, screen):
        color = COLORS['button_hover'] if self.hovered else COLORS['button']
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, COLORS['text'], self.rect, 2, border_radius=8)
        
        text_surface = self.font.render(self.text, True, COLORS['text'])
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False

class GameMenu:
    def __init__(self, screen):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        self.title_font = pygame.font.Font(None, 80)
        self.button_font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 28)
        
        self.state = "main"
        self.selected_ai_0 = None
        self.selected_ai_1 = None
        
        button_width = 300
        button_height = 60
        button_x = (self.width - button_width) // 2
        start_y = 300
        spacing = 80
        
        self.main_buttons = [
            Button(button_x, start_y, button_width, button_height, "Human vs Human", self.button_font),
            Button(button_x, start_y + spacing, button_width, button_height, "Human vs AI", self.button_font),
            Button(button_x, start_y + spacing * 2, button_width, button_height, "AI vs AI", self.button_font),
            Button(button_x, start_y + spacing * 3, button_width, button_height, "Exit", self.button_font)
        ]
        
        ai_button_width = 250
        ai_button_height = 50
        ai_button_x = (self.width - ai_button_width) // 2
        ai_start_y = 250
        ai_spacing = 70
        
        self.ai_buttons = [
            Button(ai_button_x, ai_start_y, ai_button_width, ai_button_height, "FIS Agent", self.button_font),
            Button(ai_button_x, ai_start_y + ai_spacing, ai_button_width, ai_button_height, "CSP Agent", self.button_font),
            Button(ai_button_x, ai_start_y + ai_spacing * 2, ai_button_width, ai_button_height, "Minimax Agent", self.button_font),
            Button(ai_button_x, ai_start_y + ai_spacing * 3, ai_button_width, ai_button_height, "Back", self.button_font)
        ]
        
        left_x = self.width // 4 - ai_button_width // 2
        right_x = 3 * self.width // 4 - ai_button_width // 2
        
        self.ai_vs_ai_buttons_left = [
            Button(left_x, ai_start_y, ai_button_width, ai_button_height, "FIS Agent", self.button_font),
            Button(left_x, ai_start_y + ai_spacing, ai_button_width, ai_button_height, "CSP Agent", self.button_font),
            Button(left_x, ai_start_y + ai_spacing * 2, ai_button_width, ai_button_height, "Minimax Agent", self.button_font)
        ]
        
        self.ai_vs_ai_buttons_right = [
            Button(right_x, ai_start_y, ai_button_width, ai_button_height, "FIS Agent", self.button_font),
            Button(right_x, ai_start_y + ai_spacing, ai_button_width, ai_button_height, "CSP Agent", self.button_font),
            Button(right_x, ai_start_y + ai_spacing * 2, ai_button_width, ai_button_height, "Minimax Agent", self.button_font)
        ]
        
        self.start_button = Button((self.width - 200) // 2, 550, 200, 50, "Start Game", self.button_font)
        self.back_button = Button((self.width - 200) // 2, 620, 200, 50, "Back", self.button_font)
    
    def run(self):
        from agents.fis_agent import FISAgent
        from agents.csp_agent import CSPAgent
        from agents.minimax_agent import MinimaxAgent
        
        agent_map = {
            "FIS Agent": FISAgent,
            "CSP Agent": CSPAgent,
            "Minimax Agent": MinimaxAgent
        }
        
        self.state = "main"
        self.selected_ai_0 = None
        self.selected_ai_1 = None
        
        clock = pygame.time.Clock()
        
        while True:
            clock.tick(60)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                
                if self.state == "main":
                    for i, button in enumerate(self.main_buttons):
                        if button.handle_event(event):
                            if i == 0:
                                return {'mode': 'human_vs_human'}
                            elif i == 1:
                                self.state = "select_ai"
                            elif i == 2:
                                self.state = "select_ai_vs_ai"
                            elif i == 3:
                                return None
                
                elif self.state == "select_ai":
                    for i, button in enumerate(self.ai_buttons):
                        if button.handle_event(event):
                            if i < 3:
                                return {
                                    'mode': 'human_vs_ai',
                                    'ai_agent': agent_map[button.text]
                                }
                            else:
                                self.state = "main"
                
                elif self.state == "select_ai_vs_ai":
                    for i, button in enumerate(self.ai_vs_ai_buttons_left):
                        if button.handle_event(event):
                            self.selected_ai_0 = button.text
                    
                    for i, button in enumerate(self.ai_vs_ai_buttons_right):
                        if button.handle_event(event):
                            self.selected_ai_1 = button.text
                    
                    if self.selected_ai_0 and self.selected_ai_1:
                        if self.start_button.handle_event(event):
                            return {
                                'mode': 'ai_vs_ai',
                                'ai_agent_0': agent_map[self.selected_ai_0],
                                'ai_agent_1': agent_map[self.selected_ai_1]
                            }
                    
                    if self.back_button.handle_event(event):
                        self.state = "main"
                        self.selected_ai_0 = None
                        self.selected_ai_1 = None
            
            self.screen.fill(COLORS['background'])
            
            if self.state == "main":
                self._draw_main_menu()
            elif self.state == "select_ai":
                self._draw_ai_selection()
            elif self.state == "select_ai_vs_ai":
                self._draw_ai_vs_ai_selection()
            
            pygame.display.flip()
    
    def _draw_main_menu(self):
        title = self.title_font.render("Nano Gwent", True, COLORS['text'])
        title_rect = title.get_rect(center=(self.width // 2, 150))
        self.screen.blit(title, title_rect)
        
        subtitle = self.small_font.render("Select Game Mode", True, COLORS['text'])
        subtitle_rect = subtitle.get_rect(center=(self.width // 2, 220))
        self.screen.blit(subtitle, subtitle_rect)
        
        for button in self.main_buttons:
            button.draw(self.screen)
    
    def _draw_ai_selection(self):
        title = self.title_font.render("Select AI Opponent", True, COLORS['text'])
        title_rect = title.get_rect(center=(self.width // 2, 120))
        self.screen.blit(title, title_rect)
        
        for button in self.ai_buttons:
            button.draw(self.screen)
    
    def _draw_ai_vs_ai_selection(self):
        title = self.title_font.render("Select AI Agents", True, COLORS['text'])
        title_rect = title.get_rect(center=(self.width // 2, 80))
        self.screen.blit(title, title_rect)
        
        left_label = self.button_font.render("Player 0 (Bottom)", True, COLORS['text'])
        left_rect = left_label.get_rect(center=(self.width // 4, 180))
        self.screen.blit(left_label, left_rect)
        
        right_label = self.button_font.render("Player 1 (Top)", True, COLORS['text'])
        right_rect = right_label.get_rect(center=(3 * self.width // 4, 180))
        self.screen.blit(right_label, right_rect)
        
        for i, button in enumerate(self.ai_vs_ai_buttons_left):
            if self.selected_ai_0 == button.text:
                pygame.draw.rect(self.screen, (0, 255, 0), button.rect.inflate(10, 10), 3, border_radius=8)
            button.draw(self.screen)
        
        for i, button in enumerate(self.ai_vs_ai_buttons_right):
            if self.selected_ai_1 == button.text:
                pygame.draw.rect(self.screen, (0, 255, 0), button.rect.inflate(10, 10), 3, border_radius=8)
            button.draw(self.screen)
        
        if self.selected_ai_0 and self.selected_ai_1:
            self.start_button.draw(self.screen)
        
        self.back_button.draw(self.screen)
