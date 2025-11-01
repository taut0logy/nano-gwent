import pygame
from gui.config import *
from gui.components import CardSprite, Button
from core.action import Action
class GameGUI:
    def __init__(self, screen):
        self.screen = screen
        self.selected_card = None
        self.selected_row = None
        self.card_sprites = []
        self.animations = []
        
        self.board_rect = pygame.Rect(320, 120, 850, 530)
        
        # Player 1 (bottom) controls
        self.pass_button = Button(210, 700, 80, 40, "PASS", RED)
        self.row_buttons = {
            'melee': Button(180, 350, 100, 40, "Melee", BLUE),
            'ranged': Button(180, 300, 100, 40, "Ranged", BLUE),
            'siege': Button(180, 250, 100, 40, "Siege", BLUE)
        }
        
        # Player 2 (top) controls
        self.pass_button_p2 = Button(210, 40, 80, 40, "PASS", RED)
        self.row_buttons_p2 = {
            'siege': Button(180, 150, 100, 40, "Siege", BLUE),
            'ranged': Button(180, 200, 100, 40, "Ranged", BLUE),
            'melee': Button(180, 250, 100, 40, "Melee", BLUE)
        }
        
        self.hover_offset = 0
        self.hover_speed = 3
        
        self.row_icons = {}
        try:
            self.row_icons['melee'] = pygame.image.load('assets/images/melee.png')
            self.row_icons['ranged'] = pygame.image.load('assets/images/ranged.png')
            self.row_icons['siege'] = pygame.image.load('assets/images/siege.png')
            
            for row_name in self.row_icons:
                self.row_icons[row_name] = pygame.transform.scale(self.row_icons[row_name], (24, 24))
        except Exception as e:
            print(f"Warning: Could not load row icons: {e}")
            self.row_icons = None
        
        try:
            self.star_icon = pygame.image.load('assets/images/star.png')
            self.star_icon = pygame.transform.scale(self.star_icon, (28, 28))
        except Exception as e:
            print(f"Warning: Could not load star icon: {e}")
            self.star_icon = None
            
        try:
            if self.star_icon:
                self.gray_star_icon = self.star_icon.copy()
                gray_overlay = pygame.Surface(self.gray_star_icon.get_size())
                gray_overlay.fill((100, 100, 100))
                self.gray_star_icon.blit(gray_overlay, (0, 0), special_flags=pygame.BLEND_MULT)
            else:
                self.gray_star_icon = None
        except Exception as e:
            print(f"Warning: Could not create gray star: {e}")
            self.gray_star_icon = None
        
        self.last_round_number = 0
        self.banner_state = None  # None, 'round_end', or 'round_start'
        self.banner_start_time = 0
        self.round_winner = None
    
    def render(self, game_state):
        self.screen.fill((20, 15, 10))
        
        current_time = pygame.time.get_ticks()
        
        if game_state.round_number != self.last_round_number:
            if self.last_round_number == 0:
                # First round - show start banner immediately
                self.banner_state = 'round_start'
                self.banner_start_time = current_time
            else:
                # Round transition - show end banner first
                self.banner_state = 'round_end'
                self.banner_start_time = current_time
                
                # Get the previous round's scores
                if len(game_state.round_scores) > 0:
                    p0_strength, p1_strength = game_state.round_scores[-1]
                    if p0_strength > p1_strength:
                        self.round_winner = 0
                    elif p1_strength > p0_strength:
                        self.round_winner = 1
                    else:
                        self.round_winner = None
            
            self.last_round_number = game_state.round_number
        
        # Handle banner state transitions
        if self.banner_state == 'round_end':
            if current_time - self.banner_start_time >= 2000:
                # End banner finished, show start banner
                self.banner_state = 'round_start'
                self.banner_start_time = current_time
        elif self.banner_state == 'round_start':
            if current_time - self.banner_start_time >= 1500:
                # Start banner finished
                self.banner_state = None
        
        pygame.draw.rect(self.screen, (60, 45, 30), self.board_rect)
        pygame.draw.rect(self.screen, (120, 90, 60), self.board_rect, 3)
        
        pygame.draw.line(self.screen, (120, 90, 60), 
                        (self.board_rect.x, self.board_rect.centery),
                        (self.board_rect.right, self.board_rect.centery), 5)
        
        row_height = self.board_rect.height // 6
        
        for i in range(1, 3):
            y_top = self.board_rect.y + i * row_height
            pygame.draw.line(self.screen, (80, 60, 40),
                           (self.board_rect.x + 10, y_top),
                           (self.board_rect.right - 10, y_top), 2)
            
            y_bottom = self.board_rect.centery + i * row_height
            pygame.draw.line(self.screen, (80, 60, 40),
                           (self.board_rect.x + 10, y_bottom),
                           (self.board_rect.right - 10, y_bottom), 2)
        
        self._draw_round_info(game_state)
        self._draw_boards(game_state)
        self._draw_hands(game_state)
        self._draw_score(game_state)
        
        dt = 16
        self.animations = [anim for anim in self.animations if anim.update(dt)]
        for anim in self.animations:
            sprite = CardSprite(anim.card, int(anim.current_x), int(anim.current_y))
            sprite.draw(self.screen)
        
        # Player 1 (bottom) controls
        if game_state.current_player == 0 and not game_state.game_over and not game_state.players[0].passed:
            self.pass_button.draw(self.screen)
            if self.selected_card and self.selected_card.card_type == -1:
                selected_card_x = None
                for sprite in self.card_sprites:
                    if sprite.card == self.selected_card:
                        selected_card_x = sprite.rect.centerx
                        break

                if selected_card_x is not None:
                    button_y_base = 530
                    button_spacing = 45

                    self.row_buttons['siege'].rect.centerx = selected_card_x
                    self.row_buttons['siege'].rect.y = button_y_base

                    self.row_buttons['ranged'].rect.centerx = selected_card_x
                    self.row_buttons['ranged'].rect.y = button_y_base + button_spacing

                    self.row_buttons['melee'].rect.centerx = selected_card_x
                    self.row_buttons['melee'].rect.y = button_y_base + button_spacing * 2
                
                for button in self.row_buttons.values():
                    button.draw(self.screen)
        
        # Player 2 (top) controls
        if game_state.current_player == 1 and not game_state.game_over and not game_state.players[1].passed:
            self.pass_button_p2.draw(self.screen)
            if self.selected_card and self.selected_card.card_type == -1:
                
                selected_card_x = None
                for sprite in self.card_sprites:
                    if sprite.card == self.selected_card:
                        selected_card_x = sprite.rect.centerx
                        break

                if selected_card_x is not None:
                    button_y_base = 110
                    button_spacing = 45

                    self.row_buttons_p2['siege'].rect.centerx = selected_card_x
                    self.row_buttons_p2['siege'].rect.y = button_y_base

                    self.row_buttons_p2['ranged'].rect.centerx = selected_card_x
                    self.row_buttons_p2['ranged'].rect.y = button_y_base + button_spacing

                    self.row_buttons_p2['melee'].rect.centerx = selected_card_x
                    self.row_buttons_p2['melee'].rect.y = button_y_base + button_spacing * 2
                
                for button in self.row_buttons_p2.values():
                    button.draw(self.screen)
        
        if self.banner_state == 'round_end':
            self._draw_round_end_announcement()
        elif self.banner_state == 'round_start':
            self._draw_round_start_announcement(game_state)
        
        self.hover_offset = (self.hover_offset + self.hover_speed) % 20
    
    def _draw_round_info(self, game_state):
        info_bg = pygame.Surface((160, 50))
        info_bg.fill((40, 30, 20))
        info_bg.set_alpha(220)
        self.screen.blit(info_bg, (10, 10))
        pygame.draw.rect(self.screen, GOLD, (10, 10, 160, 50), 3)

        # Title
        title = FONT_MEDIUM.render("NANO GWENT", True, GOLD)
        title_rect = title.get_rect(center=(90, 35))
        self.screen.blit(title, title_rect)
        
        # Round number
        round_text = FONT_TITLE.render(f"ROUND {game_state.round_number}/3", True, WHITE)
        round_rect = round_text.get_rect(center=(150, 390))
        self.screen.blit(round_text, round_rect)
    
    def _draw_boards(self, game_state):
        row_height = self.board_rect.height // 6
        
        row_order_player1 = ['siege', 'ranged', 'melee']
        row_order_player0 = ['melee', 'ranged', 'siege']
        
        # Draw player 2 rows (top half)
        for idx, row_name in enumerate(row_order_player1):
            y = self.board_rect.y + idx * row_height + 15
            self._draw_row(game_state, 1, row_name, y)
        
        # Draw player 1 rows (bottom half)
        for idx, row_name in enumerate(row_order_player0):
            y = self.board_rect.centery + idx * row_height + 15
            self._draw_row(game_state, 0, row_name, y)
    
    def _draw_row(self, game_state, player_id, row_name, y):
        player = game_state.players[player_id]
        
        icon_x = self.board_rect.x - 20
        icon_y = y + 10
        
        icon_center = (icon_x + 22, icon_y + 22)
        pygame.draw.circle(self.screen, (255, 255, 255), icon_center, 22)  # White background
        pygame.draw.circle(self.screen, (218, 165, 32), icon_center, 22, 3)  # Golden border

        icon_surface = self.row_icons[row_name]
        self.screen.blit(icon_surface, (icon_x + 10, icon_y + 10))
        
        # Draw cards in the row
        cards = player.board[row_name]
        card_start_x = self.board_rect.x + 60
        
        animating_cards = [anim.card for anim in self.animations if anim.active]
        
        for i, card in enumerate(cards):
            if card not in animating_cards:
                x = card_start_x + i * (CARD_WIDTH + 5)
                sprite = CardSprite(card, x, y - 12)
                sprite.draw(self.screen)
        
        row_strength = sum(c.get_current_strength() for c in cards)
        
        strength_bg = pygame.Surface((60, 50))
        strength_bg.fill((50, 40, 25))
        strength_bg.set_alpha(230)
        strength_x = self.board_rect.right - 75
        strength_y = y + 10
        self.screen.blit(strength_bg, (strength_x, strength_y))
        pygame.draw.rect(self.screen, (120, 90, 60), (strength_x, strength_y, 60, 50), 2)
        
        strength_color = GOLD if row_strength > 0 else GRAY
        strength_text = FONT_LARGE.render(str(row_strength), True, strength_color)
        text_rect = strength_text.get_rect(center=(strength_x + 30, strength_y + 25))
        self.screen.blit(strength_text, text_rect)
    
    def _draw_hands(self, game_state):
        p1_hand = game_state.players[0].hand
        p2_hand = game_state.players[1].hand
        
        hand_y_p1 = 680
        hand_y_p2 = 20

        hand_bg_p1 = pygame.Surface((900, 130))
        hand_bg_p1.fill((30, 20, 10))
        hand_bg_p1.set_alpha(180)
        self.screen.blit(hand_bg_p1, (300, hand_y_p1 - 20))
        
        hand_bg_p2 = pygame.Surface((1000, 100))
        hand_bg_p2.fill((30, 20, 10))
        hand_bg_p2.set_alpha(180)
        self.screen.blit(hand_bg_p2, (300, hand_y_p2 - 10))
        
        self.card_sprites = []
        
        # Draw Player 1 (bottom) hand
        for i, card in enumerate(p1_hand):
            x = 350 + i * (CARD_WIDTH + 5)
            y_offset = 0
            
            sprite = CardSprite(card, x, hand_y_p1 + y_offset)
            
            if self.selected_card == card:
                sprite.selected = True
                y_offset = -10
                sprite.y = hand_y_p1 + y_offset
            elif sprite.rect.collidepoint(pygame.mouse.get_pos()):
                hover_amount = abs(10 - (self.hover_offset % 20)) / 2
                sprite.y = hand_y_p1 - hover_amount
            
            self.card_sprites.append(sprite)
            sprite.draw(self.screen)
            
        # Draw Player 2 (top) hand
        for i, card in enumerate(p2_hand):
            x = 350 + i * (CARD_WIDTH + 5)
            y_offset = 0
            
            sprite = CardSprite(card, x, hand_y_p2 + y_offset)
            
            if self.selected_card == card:
                sprite.selected = True
                y_offset = -10
                sprite.y = hand_y_p2 + y_offset
            elif sprite.rect.collidepoint(pygame.mouse.get_pos()):
                hover_amount = abs(10 - (self.hover_offset % 20)) / 2
                sprite.y = hand_y_p2 + hover_amount
            
            self.card_sprites.append(sprite)
            sprite.draw(self.screen)
    
    def _draw_score(self, game_state):
        p1_strength = game_state.players[0].get_board_strength()
        p2_strength = game_state.players[1].get_board_strength()
        
        # Player 2 score
        p2_color = (255, 100, 100) if p2_strength > p1_strength else WHITE
        p2_text = FONT_LARGE.render(f"{p2_strength}", True, p2_color)
        
        p2_center = (250, 255)
        pygame.draw.circle(self.screen, p2_color, p2_center, 30, 3)
        p2_text_rect = p2_text.get_rect(center=p2_center)
        self.screen.blit(p2_text, p2_text_rect)
        
        # Player 2 label
        p2_label = FONT_LARGE.render("Player 2", True, WHITE)
        p2_label_rect = p2_label.get_rect(midleft=(105, 225))
        
        # Draw border if it's player 2's turn
        if game_state.current_player == 1:
            border_rect = pygame.Rect(p2_label_rect.x - 5, p2_label_rect.y - 5, 
                                    p2_label_rect.width + 10, p2_label_rect.height + 10)
            pygame.draw.rect(self.screen, (255, 100, 100), border_rect, 2)
        
        self.screen.blit(p2_label, p2_label_rect)

        # Player 2 pass status
        if game_state.players[1].passed:
            p2_pass = FONT_SMALL.render("PASSED", True, (150, 150, 150))
            self.screen.blit(p2_pass, (225, 305))
            
        p2_lost = game_state.players[0].rounds_won
        star_x = p2_label_rect.centerx - 32
        
        for i in range(2):
            if i < (2 - p2_lost):
                if self.star_icon:
                    self.screen.blit(self.star_icon, (star_x + i * 32, 260))
            else:
                if self.gray_star_icon:
                    self.screen.blit(self.gray_star_icon, (star_x + i * 32, 260))
        
        # Player 1 score
        p1_color = (100, 255, 100) if p1_strength > p2_strength else WHITE
        p1_text = FONT_LARGE.render(f"{p1_strength}", True, p1_color)
        
        p1_center = (250, 520)
        pygame.draw.circle(self.screen, p1_color, p1_center, 30, 3)
        p1_text_rect = p1_text.get_rect(center=p1_center)
        self.screen.blit(p1_text, p1_text_rect)
        
        # Player 1 label
        p1_label = FONT_LARGE.render("Player 1", True, WHITE)
        p1_label_rect = p1_label.get_rect(midleft=(105, 495))
        
        # Draw border if it's player 1's turn
        if game_state.current_player == 0:
            border_rect = pygame.Rect(p1_label_rect.x - 5, p1_label_rect.y - 5, 
                                    p1_label_rect.width + 10, p1_label_rect.height + 10)
            pygame.draw.rect(self.screen, (100, 255, 100), border_rect, 2)
        
        self.screen.blit(p1_label, p1_label_rect)
        
        # Player 1 pass status
        if game_state.players[0].passed:
            p1_pass = FONT_SMALL.render("PASSED", True, (150, 150, 150))
            self.screen.blit(p1_pass, (225, 570))
            
        p1_lost = game_state.players[1].rounds_won
        star_x = p1_label_rect.centerx - 32
        
        for i in range(2):
            if i < (2 - p1_lost):
                if self.star_icon:
                    self.screen.blit(self.star_icon, (star_x + i * 32, 530))
            else:
                if self.gray_star_icon:
                    self.screen.blit(self.gray_star_icon, (star_x + i * 32, 530))

    def handle_input(self, game_state):
        current_player = game_state.players[game_state.current_player]
        current_player_id = game_state.current_player
        
        if current_player.passed:
            return None
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        
        if current_player_id == 0:
            self.pass_button.update(mouse_pos)
            for button in self.row_buttons.values():
                button.update(mouse_pos)
        else:
            self.pass_button_p2.update(mouse_pos)
            for button in self.row_buttons_p2.values():
                button.update(mouse_pos)
        
        for sprite in self.card_sprites:
            sprite.update(mouse_pos)
        
        if mouse_pressed[0]:
            if current_player_id == 0:
                if self.pass_button.is_clicked(mouse_pos, mouse_pressed):
                    return Action(Action.PASS)
            else:
                if self.pass_button_p2.is_clicked(mouse_pos, mouse_pressed):
                    return Action(Action.PASS)
            
            for sprite in self.card_sprites:
                if sprite.hovered and sprite.card in current_player.hand:
                    if self.selected_card == sprite.card:
                        self.selected_card = None
                    else:
                        self.selected_card = sprite.card
                    pygame.time.wait(100)
                    break
            
            if self.selected_card:
                if self.selected_card.card_type in [0, 1, 2]:
                    row_name = {0: 'melee', 1: 'ranged', 2: 'siege'}[self.selected_card.card_type]
                    return Action(Action.PLAY_UNIT, self.selected_card, row_name)
                
                elif self.selected_card.card_type == -2:
                    action = Action(Action.PLAY_SPECIAL, self.selected_card, None)
                    self.selected_card = None
                    return action
                
                elif self.selected_card.card_type == -1:
                    if current_player_id == 0:
                        for row_name, button in self.row_buttons.items():
                            if button.is_clicked(mouse_pos, mouse_pressed):
                                action = Action(Action.PLAY_SPECIAL, self.selected_card, row_name)
                                self.selected_card = None
                                return action
                    else:
                        for row_name, button in self.row_buttons_p2.items():
                            if button.is_clicked(mouse_pos, mouse_pressed):
                                action = Action(Action.PLAY_SPECIAL, self.selected_card, row_name)
                                self.selected_card = None
                                return action
        
        return None
    
    def show_game_over(self, game_state):
        winner = game_state.winner
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(220)
        overlay.fill((10, 5, 0))
        self.screen.blit(overlay, (0, 0))
        
        result_box = pygame.Surface((700, 450))
        result_box.fill((40, 30, 20))
        result_box_rect = result_box.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(result_box, result_box_rect)
        pygame.draw.rect(self.screen, GOLD, result_box_rect, 4)
        
        text = FONT_TITLE.render("Match Over!", True, (100, 255, 100))

        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 180))
        self.screen.blit(text, text_rect)
        
        table_y = SCREEN_HEIGHT // 2 - 120
        score_title = FONT_LARGE.render("MATCH SUMMARY", True, GOLD)
        score_title_rect = score_title.get_rect(center=(SCREEN_WIDTH // 2, table_y))
        self.screen.blit(score_title, score_title_rect)
        
        table_y += 45
        round_headers = FONT_MEDIUM.render("           ROUND 1         ROUND 2         ROUND 3", True, WHITE)
        round_headers_rect = round_headers.get_rect(center=(SCREEN_WIDTH // 2, table_y))
        self.screen.blit(round_headers, round_headers_rect)
        
        table_y += 40
        
        # Prepare round scores with colors
        round_displays = []
        for i in range(3):
            if i < len(game_state.round_scores):
                p0_score, p1_score = game_state.round_scores[i]
                round_displays.append((str(p0_score), str(p1_score), p0_score, p1_score))
            else:
                round_displays.append(("-", "-", 0, 0))

        p1_label = FONT_MEDIUM.render("Player 1:", True, (100, 255, 100))
        p1_label_rect = p1_label.get_rect()
        p1_label_rect.midleft = (SCREEN_WIDTH // 2 - 250, table_y)
        self.screen.blit(p1_label, p1_label_rect)
        
        x_offset = SCREEN_WIDTH // 2 - 130
        for i, (p0_str, p1_str, p0_score, p1_score) in enumerate(round_displays):
            if p0_str == "-":
                color = WHITE
            elif p0_score > p1_score:
                color = (100, 255, 100)
            elif p0_score < p1_score:
                color = (255, 100, 100)
            else:
                color = (200, 200, 200)

            score_text = FONT_MEDIUM.render(p0_str, True, color)
            score_rect = score_text.get_rect(center=(x_offset + i * 150, table_y))
            self.screen.blit(score_text, score_rect)
        
        table_y += 40

        p2_label = FONT_MEDIUM.render("Player 2:", True, (255, 100, 100))
        p2_label_rect = p2_label.get_rect()
        p2_label_rect.midleft = (SCREEN_WIDTH // 2 - 250, table_y)
        self.screen.blit(p2_label, p2_label_rect)
        
        x_offset = SCREEN_WIDTH // 2 - 130
        for i, (p0_str, p1_str, p0_score, p1_score) in enumerate(round_displays):
            if p1_str == "-":
                color = WHITE
            elif p1_score > p0_score:
                color = (100, 255, 100)
            elif p1_score < p0_score:
                color = (255, 100, 100)
            else:
                color = (200, 200, 200)

            score_text = FONT_MEDIUM.render(p1_str, True, color)
            score_rect = score_text.get_rect(center=(x_offset + i * 150, table_y))
            self.screen.blit(score_text, score_rect)
        
        table_y += 60
        if winner is not None:
            if winner == 0:
                subtext = FONT_LARGE.render("Player 1 Won the Match!", True, GOLD)
            else:
                subtext = FONT_LARGE.render("Player 2 Won the Match!", True, GRAY)
        else:
            subtext = FONT_LARGE.render("Match Ended in a Tie", True, GRAY)
        
        subtext_rect = subtext.get_rect(center=(SCREEN_WIDTH // 2, table_y))
        self.screen.blit(subtext, subtext_rect)
        
        continue_text = FONT_MEDIUM.render("Press SPACE to return to menu", True, WHITE)
        continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 180))
        self.screen.blit(continue_text, continue_rect)

    def _draw_round_start_announcement(self, game_state):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        announcement_box = pygame.Surface((500, 200))
        announcement_box.fill((40, 30, 20))
        announcement_box_rect = announcement_box.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(announcement_box, announcement_box_rect)
        pygame.draw.rect(self.screen, GOLD, announcement_box_rect, 4)
        
        title = FONT_TITLE.render(f"ROUND {game_state.round_number}", True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        self.screen.blit(title, title_rect)
        
        subtitle = FONT_LARGE.render("Battle Begins!", True, WHITE)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
        self.screen.blit(subtitle, subtitle_rect)

    def _draw_round_end_announcement(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        announcement_box = pygame.Surface((500, 200))
        announcement_box.fill((40, 30, 20))
        announcement_box_rect = announcement_box.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(announcement_box, announcement_box_rect)
        pygame.draw.rect(self.screen, GOLD, announcement_box_rect, 4)
        
        title = FONT_TITLE.render("ROUND END", True, GOLD)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        self.screen.blit(title, title_rect)
        
        if self.round_winner == 0:
            subtitle = FONT_LARGE.render("Player 1 Won This Round!", True, (100, 255, 100))
        elif self.round_winner == 1:
            subtitle = FONT_LARGE.render("Player 2 Won This Round!", True, (255, 100, 100))
        else:
            subtitle = FONT_LARGE.render("Round Draw!", True, WHITE)
        
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
        self.screen.blit(subtitle, subtitle_rect)

