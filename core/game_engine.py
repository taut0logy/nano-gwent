from core.action import Action

class GameEngine:
    def __init__(self, game_state):
        self.game_state = game_state
    
    def execute_action(self, action):
        if action.type == Action.PASS:
            self.game_state.player().passed = True
        
        elif action.type == Action.PLAY_UNIT:
            current_player = self.game_state.player()
            if action.card in current_player.hand:
                current_player.hand.remove(action.card)
                
                row_name = {0: "melee", 1: "ranged", 2: "siege"}[action.card.card_type]
                current_player.board[row_name].append(action.card)
        
        elif action.type == Action.PLAY_SPECIAL:
            current_player = self.game_state.player()
            if action.card in current_player.hand:
                current_player.hand.remove(action.card)
                
                if action.card.card_type == -2:
                    self._apply_scorch()
                elif action.card.card_type == -1:
                    self._apply_row_debuff(action.target_row)
                
                self.game_state.special_cards_used[action.card.card_type] += 1
        
        if self.game_state.check_round_end():
            self.game_state.resolve_round()
        else:
            self.game_state.switch_player()
            self._skip_passed_players()
    
    def _apply_scorch(self):
        all_cards = []
        for pid in [0, 1]:
            player = self.game_state.players[pid]
            for row in ['melee', 'ranged', 'siege']:
                all_cards.extend(player.board[row])
        
        if not all_cards:
            return
        
        max_strength = max(card.get_current_strength() for card in all_cards)
        
        for pid in [0, 1]:
            player = self.game_state.players[pid]
            for row in ['melee', 'ranged', 'siege']:
                player.board[row] = [c for c in player.board[row] if c.get_current_strength() != max_strength]
    
    def _apply_row_debuff(self, target_row):
        for pid in [0, 1]:
            player = self.game_state.players[pid]
            for card in player.board[target_row]:
                card.apply_debuff()
    
    def _skip_passed_players(self):
        """Skip the turn if the current player has already passed."""
        visited = set()
        while self.game_state.player().passed and not self.game_state.check_round_end():
            if self.game_state.current_player in visited:
                break
            visited.add(self.game_state.current_player)
            self.game_state.switch_player()
        
        if self.game_state.check_round_end():
            self.game_state.resolve_round()
    
    def check_auto_end_round(self):
        """Check if the round should auto-end (both players have no cards or both passed)."""
        p0_has_cards = len(self.game_state.players[0].hand) > 0
        p1_has_cards = len(self.game_state.players[1].hand) > 0
        
        if not p0_has_cards and not p1_has_cards:
            self.game_state.players[0].passed = True
            self.game_state.players[1].passed = True
            self.game_state.resolve_round()
            return True
        
        if self.game_state.check_round_end():
            self.game_state.resolve_round()
            return True
        
        return False
    
    def get_valid_actions(self):
        actions = []
        current_player = self.game_state.player()
        
        if current_player.passed:
            return [Action(Action.PASS)]
        
        actions.append(Action(Action.PASS))
        
        for card in current_player.hand:
            if card.card_type in [0, 1, 2]:
                row_name = {0: "melee", 1: "ranged", 2: "siege"}[card.card_type]
                actions.append(Action(Action.PLAY_UNIT, card, row_name))
            
            elif card.card_type in [-1, -2]:
                if self.game_state.special_cards_used[card.card_type] < 2:
                    if card.card_type == -2:
                        actions.append(Action(Action.PLAY_SPECIAL, card, None))
                    elif card.card_type == -1:
                        for row in ['melee', 'ranged', 'siege']:
                            actions.append(Action(Action.PLAY_SPECIAL, card, row))
        
        return actions
