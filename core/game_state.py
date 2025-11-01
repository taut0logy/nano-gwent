import copy
import random
from core.card import Card
from core.player_state import PlayerState
from utils import constants

class GameState:
    def __init__(self):
        self.initial_hand = []
        self.round_number = 1
        self.current_player = 0
        self.players = {
            0: PlayerState(0),
            1: PlayerState(1)
        }
        self.game_over = False
        self.winner = None
        self.round_scores = []  # List of (p0_score, p1_score) tuples for each round
    
    def initialize(self):
        card_pool = constants.CARD_POOL.copy()
        selected_ids = random.sample(card_pool, 10)
        
        self.initial_hand = []
        for card_id in selected_ids:
            if 1 <= card_id <= 5:
                card_type = 0
            elif 6 <= card_id <= 10:
                card_type = 1
            elif 11 <= card_id <= 15:
                card_type = 2
            else:
                card_type = 0
            self.initial_hand.append(Card(card_id, card_type))
        
        self.initial_hand.append(Card(-1, -1))
        self.initial_hand.append(Card(-2, -2))
        
        self.players[0].hand = [Card(c.id, c.card_type) for c in self.initial_hand]
        self.players[1].hand = [Card(c.id, c.card_type) for c in self.initial_hand]
        
        self.current_player = 0
    
    def player(self):
        return self.players[self.current_player]
    
    def opponent(self):
        return self.players[1 - self.current_player]
    
    def clone(self):
        return copy.deepcopy(self)
    
    def switch_player(self):
        self.current_player = 1 - self.current_player
    
    def check_round_end(self):
        return self.players[0].passed and self.players[1].passed
    
    def resolve_round(self):
        p0_strength = self.players[0].get_board_strength()
        p1_strength = self.players[1].get_board_strength()
        
        # Store the round scores
        self.round_scores.append((p0_strength, p1_strength))
        
        if p0_strength > p1_strength:
            self.players[0].rounds_won += 1
        elif p1_strength > p0_strength:
            self.players[1].rounds_won += 1
        
        if self.players[0].rounds_won == 2:
            self.game_over = True
            self.winner = 0
        elif self.players[1].rounds_won == 2:
            self.game_over = True
            self.winner = 1
        elif self.round_number == 3:
            self.game_over = True
            if self.players[0].rounds_won > self.players[1].rounds_won:
                self.winner = 0
            elif self.players[1].rounds_won > self.players[0].rounds_won:
                self.winner = 1
            else:
                # Tiebreaker: player with more cards in hand wins
                p0_cards = len(self.players[0].hand)
                p1_cards = len(self.players[1].hand)
                if p0_cards > p1_cards:
                    self.winner = 0
                elif p1_cards > p0_cards:
                    self.winner = 1
                else:
                    self.winner = None  # Still a draw if equal cards
        else:
            self.round_number += 1
            self.players[0].reset_round()
            self.players[1].reset_round()
            self.current_player = (self.round_number - 1) % 2
            
            # Auto-pass players with no cards at start of new round
            if len(self.players[0].hand) == 0:
                self.players[0].passed = True
            if len(self.players[1].hand) == 0:
                self.players[1].passed = True
    
    def __repr__(self):
        return f"GameState(round={self.round_number}, current_player={self.current_player}, scores={self.players[0].rounds_won}-{self.players[1].rounds_won})"
