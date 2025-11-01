from utils import constants

class Card:
    def __init__(self, card_id, card_type):
        self.id = card_id
        self.card_type = card_type
        self.is_debuffed = False
        
        if 1 <= card_id <= 15:
            self.strength = constants.CARD_STRENGTHS[card_id - 1]
        else:
            self.strength = 0
    
    def get_current_strength(self):
        if self.is_debuffed:
            return 1
        return self.strength
    
    def apply_debuff(self):
        self.is_debuffed = True
    
    def remove_debuff(self):
        self.is_debuffed = False
    
    def __repr__(self):
        type_names = {0: "Melee", 1: "Ranged", 2: "Siege", -1: "RowDebuff", -2: "Scorch"}
        return f"Card(id={self.id}, type={type_names.get(self.card_type, 'Unknown')}, strength={self.get_current_strength()})"
