class Action:
    PLAY_UNIT = "play_unit"
    PLAY_SPECIAL = "play_special"
    PASS = "pass"
    
    def __init__(self, action_type, card=None, target_row=None):
        self.type = action_type
        self.card = card
        self.target_row = target_row
    
    def __repr__(self):
        if self.type == Action.PASS:
            return "Action(PASS)"
        elif self.card:
            return f"Action({self.type}, card={self.card.id}, row={self.target_row})"
        return f"Action({self.type})"
