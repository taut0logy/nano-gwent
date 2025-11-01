class PlayerState:
    def __init__(self, player_id):
        self.id = player_id
        self.hand = []
        self.board = {"melee": [], "ranged": [], "siege": []}
        self.passed = False
        self.rounds_won = 0
    
    def reset_round(self):
        self.board = {"melee": [], "ranged": [], "siege": []}
        self.passed = False
        for card in self.hand:
            card.remove_debuff()
    
    def get_board_strength(self):
        total = 0
        for row in ['melee', 'ranged', 'siege']:
            for card in self.board[row]:
                total += card.get_current_strength()
        return total
    
    def __repr__(self):
        return f"PlayerState(id={self.id}, hand={len(self.hand)}, strength={self.get_board_strength()}, passed={self.passed})"
