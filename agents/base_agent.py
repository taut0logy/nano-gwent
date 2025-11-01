class BaseAgent:
    def __init__(self, player_id):
        self.player_id = player_id
    
    def decide_action(self, game_state, valid_actions):
        raise NotImplementedError
    
    def calculate_board_strength(self, board):
        total = 0
        for row in ['melee', 'ranged', 'siege']:
            for card in board.get(row, []):
                total += card.get_current_strength()
        return total
