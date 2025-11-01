import pygame
from gui.config import *
from gui.components import CardSprite, Button
from core.action import Action

class AnimatedCard:
    def __init__(self, card, start_x, start_y, end_x, end_y, duration=500):
        self.card = card
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.current_x = start_x
        self.current_y = start_y
        self.duration = duration
        self.elapsed = 0
        self.active = True
    
    def update(self, dt):
        if not self.active:
            return False
        
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.current_x = self.end_x
            self.current_y = self.end_y
            self.active = False
            return False
        
        progress = self.elapsed / self.duration
        eased = self._ease_out_cubic(progress)
        self.current_x = self.start_x + (self.end_x - self.start_x) * eased
        self.current_y = self.start_y + (self.end_y - self.start_y) * eased
        return True
    
    def _ease_out_cubic(self, t):
        return 1 - pow(1 - t, 3)

class GameGUI:
    def __init__(self, screen):
        self.screen = screen
        self.selected_card = None
        self.selected_row = None
        self.card_sprites = []
        self.animations = []
        
        self.board_rect = pygame.Rect(320, 120, 850, 530)
        
        self.pass_button = Button(50, 680, 100, 50, "PASS", RED)
        self.row_buttons = {
            'melee': Button(180, 350, 100, 40, "Melee", BLUE),
            'ranged': Button(180, 300, 100, 40, "Ranged", BLUE),
            'siege': Button(180, 250, 100, 40, "Siege", BLUE)
        }
        
        self.hover_offset = 0
        self.hover_speed = 3
        
        # Load row icons
        self.row_icons = {}
        try:
            self.row_icons['melee'] = pygame.image.load('assets/images/melee.png')
            self.row_icons['ranged'] = pygame.image.load('assets/images/ranged.png')
            self.row_icons['siege'] = pygame.image.load('assets/images/siege.png')
            
            # Scale icons to 24x24 for circular background display
            for row_name in self.row_icons:
                self.row_icons[row_name] = pygame.transform.scale(self.row_icons[row_name], (24, 24))
        except Exception as e:
            print(f"Warning: Could not load row icons: {e}")
            self.row_icons = None
        
        # Banner state tracking
        self.last_round_number = 0
        self.banner_state = None  # None, 'round_end', or 'round_start'
        self.banner_start_time = 0
        self.round_winner = None
    
    def render(self, game_state):
        self.screen.fill((20, 15, 10))
        
        current_time = pygame.time.get_ticks()
        
        # Detect round change
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
        
        # Draw center divider line (between players)
        pygame.draw.line(self.screen, (120, 90, 60), 
                        (self.board_rect.x, self.board_rect.centery),
                        (self.board_rect.right, self.board_rect.centery), 5)
        
        # Draw row divider lines (2 lines per side = 3 rows each)
        row_height = self.board_rect.height // 6  # Divide into 6 equal sections
        
        for i in range(1, 3):
            # Top half (player 2) dividers
            y_top = self.board_rect.y + i * row_height
            pygame.draw.line(self.screen, (80, 60, 40),
                           (self.board_rect.x + 10, y_top),
                           (self.board_rect.right - 10, y_top), 2)
            
            # Bottom half (player 1) dividers
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
        
        if game_state.current_player == 0 and not game_state.game_over and not game_state.players[0].passed:
            self.pass_button.draw(self.screen)
            if self.selected_card and self.selected_card.card_type == -1:
                for button in self.row_buttons.values():
                    button.draw(self.screen)
        
        # Draw banners
        if self.banner_state == 'round_end':
            self._draw_round_end_announcement()
        elif self.banner_state == 'round_start':
            self._draw_round_start_announcement(game_state)
        
        self.hover_offset = (self.hover_offset + self.hover_speed) % 20
    
    def _draw_round_info(self, game_state):
        info_bg = pygame.Surface((280, 180))
        info_bg.fill((40, 30, 20))
        info_bg.set_alpha(220)
        self.screen.blit(info_bg, (20, 20))
        pygame.draw.rect(self.screen, GOLD, (20, 20, 280, 180), 2)
        
        title = FONT_LARGE.render("NANO GWENT", True, GOLD)
        self.screen.blit(title, (35, 30))
        
        round_text = FONT_MEDIUM.render(f"Round {game_state.round_number}/3", True, WHITE)
        self.screen.blit(round_text, (35, 70))
        
        score_text = FONT_MEDIUM.render(
            f"Wins: {game_state.players[0].rounds_won} - {game_state.players[1].rounds_won}",
            True, WHITE
        )
        self.screen.blit(score_text, (35, 100))
        
        if game_state.current_player == 0:
            turn_color = (100, 255, 100)
            turn_text = "Your Turn"
        else:
            turn_color = (255, 100, 100)
            turn_text = "Opponent Turn"
        
        turn_surface = FONT_MEDIUM.render(turn_text, True, turn_color)
        self.screen.blit(turn_surface, (35, 130))
        
        if game_state.players[0].passed:
            pass_text = FONT_SMALL.render("You passed", True, GRAY)
            self.screen.blit(pass_text, (35, 160))
        
        if game_state.players[1].passed:
            pass_text = FONT_SMALL.render("Opp passed", True, GRAY)
            self.screen.blit(pass_text, (160, 160))
    
    def _draw_boards(self, game_state):
        # Calculate row height based on board dimensions (6 rows total, 3 per player)
        row_height = self.board_rect.height // 6  # ~88 pixels per row
        
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
        
        # Draw row icon using image or fallback to emoji
        icon_x = self.board_rect.x - 60  # Position icon to the left of board
        icon_y = y + 15  # Center vertically in the row
        
        # Draw circular background and border (larger size)
        icon_center = (icon_x + 22, icon_y + 22)  # Center of 44x44 circle
        pygame.draw.circle(self.screen, (255, 255, 255), icon_center, 22)  # White background
        pygame.draw.circle(self.screen, (218, 165, 32), icon_center, 22, 3)  # Golden border
        
        if self.row_icons and row_name in self.row_icons:
            icon_surface = self.row_icons[row_name]
            # Center the 24x24 icon in the 44x44 circle
            self.screen.blit(icon_surface, (icon_x + 10, icon_y + 10))
        else:
            # Fallback to emoji if images not loaded
            row_icon = {
                'melee': '⚔',
                'ranged': '🏹',
                'siege': '🗡'
            }.get(row_name, row_name[0].upper())
            
            icon_surface = FONT_LARGE.render(row_icon, True, (200, 180, 150))
            self.screen.blit(icon_surface, (icon_x + 12, icon_y + 12))
        
        # Draw row label
        row_label = FONT_SMALL.render(row_name.capitalize(), True, (180, 160, 130))
        self.screen.blit(row_label, (self.board_rect.x + 15, y + 8))
        
        # Draw cards in the row
        cards = player.board[row_name]
        card_start_x = self.board_rect.x + 110
        
        animating_cards = [anim.card for anim in self.animations if anim.active]
        
        for i, card in enumerate(cards):
            if card not in animating_cards:
                x = card_start_x + i * (CARD_WIDTH + 5)
                sprite = CardSprite(card, x, y + 5)
                sprite.draw(self.screen)
        
        # Draw row strength indicator
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
        
        hand_bg_p1 = pygame.Surface((9000, 130))
        hand_bg_p1.fill((30, 20, 10))
        hand_bg_p1.set_alpha(180)
        self.screen.blit(hand_bg_p1, (280, hand_y_p1 - 20))
        
        hand_bg_p2 = pygame.Surface((1000, 100))
        hand_bg_p2.fill((30, 20, 10))
        hand_bg_p2.set_alpha(180)
        self.screen.blit(hand_bg_p2, (280, hand_y_p2 - 10))
        
        label_p1 = FONT_MEDIUM.render("You", True, (100, 255, 100))
        self.screen.blit(label_p1, (190, hand_y_p1 - 15))

        label_p2 = FONT_MEDIUM.render("Opponent", True, (255, 100, 100))
        self.screen.blit(label_p2, (190, hand_y_p2 - 5))
        
        self.card_sprites = []
        
        for i, card in enumerate(p1_hand):
            x = 420 + i * (CARD_WIDTH + 5)
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
        
        for i, card in enumerate(p2_hand):
            x = 420 + i * (CARD_WIDTH + 5)
            sprite = CardSprite(card, x, hand_y_p2)
            sprite.draw(self.screen)
    
    def _draw_score(self, game_state):
        p1_strength = game_state.players[0].get_board_strength()
        p2_strength = game_state.players[1].get_board_strength()
        
        # score_bg = pygame.Surface((200, 140))
        # score_bg.fill((40, 30, 20))
        # score_bg.set_alpha(220)
        # self.screen.blit(score_bg, (20, 300))
        # pygame.draw.rect(self.screen, GOLD, (20, 300, 200, 140), 2)
        
        p2_color = (255, 100, 100) if p2_strength > p1_strength else WHITE
        p2_text = FONT_LARGE.render(f"Player 2: {p2_strength}", True, p2_color)
        self.screen.blit(p2_text, (35, 285))
        
        p1_color = (100, 255, 100) if p1_strength > p2_strength else WHITE
        p1_text = FONT_LARGE.render(f"Player 1: {p1_strength}", True, p1_color)
        self.screen.blit(p1_text, (35, 520))
    
    def handle_input(self, game_state):
        current_player = game_state.players[game_state.current_player]
        
        if current_player.passed:
            return None
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        
        self.pass_button.update(mouse_pos)
        for button in self.row_buttons.values():
            button.update(mouse_pos)
        
        for sprite in self.card_sprites:
            sprite.update(mouse_pos)
        
        if mouse_pressed[0]:
            if self.pass_button.is_clicked(mouse_pos, mouse_pressed):
                return Action(Action.PASS)
            
            for sprite in self.card_sprites:
                if sprite.hovered and sprite.card in game_state.players[0].hand:
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
                    for row_name, button in self.row_buttons.items():
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
        
        # Title at the top
        if winner is not None:
            if winner == 0:
                text = FONT_TITLE.render("Victory!", True, (100, 255, 100))
            else:
                text = FONT_TITLE.render("Defeat", True, (255, 100, 100))
        else:
            text = FONT_TITLE.render("Draw!", True, WHITE)
        
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 180))
        self.screen.blit(text, text_rect)
        
        # Score table in the middle
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
        
        # Draw You: row with colored scores
        you_label = FONT_MEDIUM.render("You:", True, (100, 255, 100))
        you_label_rect = you_label.get_rect()
        you_label_rect.midleft = (SCREEN_WIDTH // 2 - 250, table_y)
        self.screen.blit(you_label, you_label_rect)
        
        x_offset = SCREEN_WIDTH // 2 - 130
        for i, (p0_str, p1_str, p0_score, p1_score) in enumerate(round_displays):
            if p0_str == "-":
                color = WHITE
            elif p0_score > p1_score:
                color = (100, 255, 100)  # Green for win
            elif p0_score < p1_score:
                color = (255, 100, 100)  # Red for loss
            else:
                color = (200, 200, 200)  # Gray for draw
            
            score_text = FONT_MEDIUM.render(p0_str, True, color)
            score_rect = score_text.get_rect(center=(x_offset + i * 150, table_y))
            self.screen.blit(score_text, score_rect)
        
        table_y += 40
        
        # Draw Opp: row with colored scores
        opp_label = FONT_MEDIUM.render("Opp:", True, (255, 100, 100))
        opp_label_rect = opp_label.get_rect()
        opp_label_rect.midleft = (SCREEN_WIDTH // 2 - 250, table_y)
        self.screen.blit(opp_label, opp_label_rect)
        
        x_offset = SCREEN_WIDTH // 2 - 130
        for i, (p0_str, p1_str, p0_score, p1_score) in enumerate(round_displays):
            if p1_str == "-":
                color = WHITE
            elif p1_score > p0_score:
                color = (100, 255, 100)  # Green for win
            elif p1_score < p0_score:
                color = (255, 100, 100)  # Red for loss
            else:
                color = (200, 200, 200)  # Gray for draw
            
            score_text = FONT_MEDIUM.render(p1_str, True, color)
            score_rect = score_text.get_rect(center=(x_offset + i * 150, table_y))
            self.screen.blit(score_text, score_rect)
        
        # Subtitle below table
        table_y += 60
        if winner is not None:
            if winner == 0:
                subtext = FONT_LARGE.render("You Won the Match!", True, GOLD)
            else:
                subtext = FONT_LARGE.render("Opponent Won the Match", True, GRAY)
        else:
            subtext = FONT_LARGE.render("Match Ended in a Tie", True, GRAY)
        
        subtext_rect = subtext.get_rect(center=(SCREEN_WIDTH // 2, table_y))
        self.screen.blit(subtext, subtext_rect)
        
        # Instructions at the bottom
        continue_text = FONT_MEDIUM.render("Press SPACE to return to menu", True, WHITE)
        continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 180))
        self.screen.blit(continue_text, continue_rect)
        
        esc_text = FONT_SMALL.render("Press ESC to return immediately", True, GRAY)
        esc_rect = esc_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 210))
        self.screen.blit(esc_text, esc_rect)

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
            subtitle = FONT_LARGE.render("You Won This Round!", True, (100, 255, 100))
        elif self.round_winner == 1:
            subtitle = FONT_LARGE.render("Opponent Won This Round!", True, (255, 100, 100))
        else:
            subtitle = FONT_LARGE.render("Round Draw!", True, WHITE)
        
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
        self.screen.blit(subtitle, subtitle_rect)

