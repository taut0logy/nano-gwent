import numpy as np
from agents.base_agent import BaseAgent
from core.action import Action
import random

class FISAgent(BaseAgent):
    def __init__(self, player_id):
        super().__init__(player_id)
    
    def decide_action(self, game_state, valid_actions):
        if len(valid_actions) == 1:
            return valid_actions[0]
        
        my_state = game_state.players[self.player_id]
        opp_state = game_state.players[1 - self.player_id]
        
        my_strength = my_state.get_board_strength()
        opp_strength = opp_state.get_board_strength()
        strength_difference = my_strength - opp_strength
        
        my_cards = len(my_state.hand)
        opponent_cards = len(opp_state.hand)
        
        rounds_won_diff = my_state.rounds_won - opp_state.rounds_won
        
        strength_diff = max(-100, min(100, strength_difference))
        cards_in_hand = my_cards
        round_num = game_state.round_number
        rounds_diff = rounds_won_diff
        opp_cards = opponent_cards
        
        try:
            aggression_level = self._compute_fuzzy_output(
                strength_diff, cards_in_hand, round_num, rounds_diff, opp_cards
            )
        except Exception:
            aggression_level = 50
        
        action = self._select_action_by_aggression(game_state, valid_actions, aggression_level)
        
        return action
    
    def _compute_fuzzy_output(self, strength_diff, cards_in_hand, round_num, rounds_diff, opp_cards):
        
        # Step 1: FUZZIFICATION - Compute membership values for each input
        
        # Strength Difference memberships
        sd_losing_badly = self._trapmf(strength_diff, -100, -100, -30, -15)
        sd_losing = self._trimf(strength_diff, -25, -10, 0)
        sd_tied = self._trimf(strength_diff, -5, 0, 5)
        sd_winning = self._trimf(strength_diff, 0, 10, 25)
        sd_winning_big = self._trapmf(strength_diff, 15, 30, 100, 100)
        
        # Cards in Hand memberships
        cih_very_few = self._trapmf(cards_in_hand, 0, 0, 1, 3)
        cih_few = self._trimf(cards_in_hand, 2, 4, 6)
        cih_moderate = self._trimf(cards_in_hand, 5, 7, 9)
        cih_many = self._trapmf(cards_in_hand, 8, 10, 12, 12)
        
        # Round Number memberships
        rn_early = self._trimf(round_num, 1, 1, 2)
        rn_mid = self._trimf(round_num, 1, 2, 3)
        rn_late = self._trimf(round_num, 2, 3, 3)
        
        # Rounds Won Difference memberships
        rd_behind = self._trimf(rounds_diff, -2, -1, 0)
        rd_tied = self._trimf(rounds_diff, -1, 0, 1)
        rd_ahead = self._trimf(rounds_diff, 0, 1, 2)
        
        # Opponent Cards memberships
        oc_very_few = self._trapmf(opp_cards, 0, 0, 1, 3)
        # Note: oc_few and oc_moderate are defined for completeness but not used in current rules
        # oc_few = self._trimf(opp_cards, 2, 4, 6)
        # oc_moderate = self._trimf(opp_cards, 5, 7, 9)
        oc_many = self._trapmf(opp_cards, 8, 10, 12, 12)
        
        # Step 2: RULE EVALUATION
        # Each rule produces an activation level and maps to an output membership function
        
        rule_activations = []
        
        # --- EARLY GAME RULES ---
        # Rule 1: Early game + many cards + tied rounds -> Balanced
        rule_activations.append((
            min(rn_early, cih_many, rd_tied),
            'balanced'
        ))
        
        # Rule 2: Early game + winning + many cards -> Defensive
        rule_activations.append((
            min(rn_early, sd_winning, cih_many),
            'defensive'
        ))
        
        # Rule 3: Early game + losing badly + many cards -> Very Defensive
        rule_activations.append((
            min(rn_early, sd_losing_badly, cih_many),
            'very_defensive'
        ))
        
        # Rule 4: Early game + few cards -> Aggressive
        rule_activations.append((
            min(rn_early, cih_few),
            'aggressive'
        ))
        
        # --- MID GAME RULES ---
        # Rule 5: Mid game + ahead in rounds + winning -> Very Defensive
        rule_activations.append((
            min(rn_mid, rd_ahead, sd_winning),
            'very_defensive'
        ))
        
        # Rule 6: Mid game + tied rounds + tied strength -> Balanced
        rule_activations.append((
            min(rn_mid, rd_tied, sd_tied),
            'balanced'
        ))
        
        # Rule 7: Mid game + behind in rounds -> Very Aggressive
        rule_activations.append((
            min(rn_mid, rd_behind),
            'very_aggressive'
        ))
        
        # Rule 8: Mid game + winning big -> Very Defensive
        rule_activations.append((
            min(rn_mid, sd_winning_big),
            'very_defensive'
        ))
        
        # --- LATE GAME RULES ---
        # Rule 9: Late game + ahead in rounds -> Very Defensive
        rule_activations.append((
            min(rn_late, rd_ahead),
            'very_defensive'
        ))
        
        # Rule 10: Late game + behind in rounds -> Very Aggressive
        rule_activations.append((
            min(rn_late, rd_behind),
            'very_aggressive'
        ))
        
        # Rule 11: Late game + tied rounds + winning -> Defensive
        rule_activations.append((
            min(rn_late, rd_tied, sd_winning),
            'defensive'
        ))
        
        # Rule 12: Late game + tied rounds + losing -> Very Aggressive
        rule_activations.append((
            min(rn_late, rd_tied, sd_losing),
            'very_aggressive'
        ))
        
        # --- RESOURCE-BASED RULES ---
        # Rule 13: Very few cards + losing -> Very Aggressive
        rule_activations.append((
            min(cih_very_few, sd_losing),
            'very_aggressive'
        ))
        
        # Rule 14: Very few cards + winning -> Very Defensive
        rule_activations.append((
            min(cih_very_few, sd_winning),
            'very_defensive'
        ))
        
        # Rule 15: Many cards + opponent has very few -> Aggressive
        rule_activations.append((
            min(cih_many, oc_very_few),
            'aggressive'
        ))
        
        # Rule 16: Few cards + opponent has many -> Defensive
        rule_activations.append((
            min(cih_few, oc_many),
            'defensive'
        ))
        
        # --- STRATEGIC RULES ---
        # Rule 17: Winning big + opponent has few cards -> Very Defensive
        rule_activations.append((
            min(sd_winning_big, oc_very_few),
            'very_defensive'
        ))
        
        # Rule 18: Losing badly + moderate cards -> Aggressive
        rule_activations.append((
            min(sd_losing_badly, cih_moderate),
            'aggressive'
        ))
        
        # Rule 19: Tied strength + moderate cards + mid game -> Balanced
        rule_activations.append((
            min(sd_tied, cih_moderate, rn_mid),
            'balanced'
        ))
        
        # Rule 20: Ahead in rounds + early game -> Defensive
        rule_activations.append((
            min(rd_ahead, rn_early),
            'defensive'
        ))
        
        # Rule 21: Behind in rounds + early game + many cards -> Aggressive
        rule_activations.append((
            min(rd_behind, rn_early, cih_many),
            'aggressive'
        ))
        
        # Rule 22: Tied everything -> Balanced
        rule_activations.append((
            min(sd_tied, rd_tied, cih_moderate),
            'balanced'
        ))
        
        # Rule 23: Late game + tied + very few cards -> Very Aggressive
        rule_activations.append((
            min(rn_late, rd_tied, cih_very_few),
            'very_aggressive'
        ))
        
        # Rule 24: Moderate cards + losing -> Aggressive
        rule_activations.append((
            min(cih_moderate, sd_losing),
            'aggressive'
        ))
        
        # Rule 25: Many cards + losing + early -> Balanced
        rule_activations.append((
            min(cih_many, sd_losing, rn_early),
            'balanced'
        ))
        
        # Step 3: AGGREGATION AND DEFUZZIFICATION
        # Use centroid method (center of gravity)
        
        # Define output universe (0 to 100)
        output_universe = np.arange(0, 101, 1)
        
        # Initialize aggregated membership array
        aggregated_membership = np.zeros_like(output_universe, dtype=float)
        
        # For each rule activation, apply it to the corresponding output membership function
        for activation, output_label in rule_activations:
            if activation > 0:
                # Get the membership function for this output
                output_mf = self._get_output_membership(output_universe, output_label)
                
                # Apply activation level (clip the membership function)
                clipped_mf = np.minimum(activation, output_mf)
                
                # Aggregate using max operator
                aggregated_membership = np.maximum(aggregated_membership, clipped_mf)
        
        # Defuzzification using centroid method
        if np.sum(aggregated_membership) > 0:
            aggression_level = np.sum(output_universe * aggregated_membership) / np.sum(aggregated_membership)
        else:
            # If no rules fired, default to balanced
            aggression_level = 50
        
        return aggression_level
    
    def _trimf(self, x, a, b, c):
        if x <= a:
            return 0.0 if x < a else (1.0 if a == b else 0.0)
        elif x <= b:
            if b == a:
                return 1.0
            return (x - a) / (b - a)
        elif x <= c:
            if c == b:
                return 1.0
            return (c - x) / (c - b)
        else:
            return 0.0
    
    def _trapmf(self, x, a, b, c, d):
        if x <= a:
            return 0.0 if x < a else (1.0 if a == b else 0.0)
        elif x <= b:
            if b == a:
                return 1.0
            return (x - a) / (b - a)
        elif x <= c:
            return 1.0
        elif x <= d:
            if d == c:
                return 1.0
            return (d - x) / (d - c)
        else:
            return 0.0
    
    def _get_output_membership(self, universe, label):
        membership = np.zeros_like(universe, dtype=float)
        
        for i, x in enumerate(universe):
            if label == 'very_defensive':
                membership[i] = self._trapmf(x, 0, 0, 10, 25)
            elif label == 'defensive':
                membership[i] = self._trimf(x, 15, 30, 45)
            elif label == 'balanced':
                membership[i] = self._trimf(x, 35, 50, 65)
            elif label == 'aggressive':
                membership[i] = self._trimf(x, 55, 70, 85)
            elif label == 'very_aggressive':
                membership[i] = self._trapmf(x, 75, 90, 100, 100)
        
        return membership
    
    def _select_action_by_aggression(self, game_state, valid_actions, aggression_level):
        my_state = game_state.players[self.player_id]
        opp_state = game_state.players[1 - self.player_id]
        
        my_strength = my_state.get_board_strength()
        opp_strength = opp_state.get_board_strength()
        
        # Separate actions by type
        unit_actions = [a for a in valid_actions if a.type == Action.PLAY_UNIT]
        special_actions = [a for a in valid_actions if a.type == Action.PLAY_SPECIAL]
        pass_action = [a for a in valid_actions if a.type == Action.PASS]
        
        # VERY DEFENSIVE (0-20): Pass if ahead, minimal play if behind
        if aggression_level < 20:
            if my_strength >= opp_strength and len(my_state.hand) > 0:
                return pass_action[0] if pass_action else valid_actions[0]
            elif unit_actions:
                weakest = min(unit_actions, key=lambda a: a.card.strength)
                return weakest
            return pass_action[0] if pass_action else valid_actions[0]
        
        # DEFENSIVE (20-40): Play low-medium cards
        elif aggression_level < 40:
            if unit_actions:
                sorted_units = sorted(unit_actions, key=lambda a: a.card.strength)
                defensive_cards = sorted_units[:max(1, len(sorted_units) * 2 // 5)]
                return random.choice(defensive_cards)
            return pass_action[0] if pass_action else valid_actions[0]
        
        # BALANCED (40-60): Play medium cards
        elif aggression_level < 60:
            if unit_actions:
                sorted_units = sorted(unit_actions, key=lambda a: a.card.strength)
                mid_start = len(sorted_units) * 3 // 10
                mid_end = len(sorted_units) * 7 // 10
                if mid_end > mid_start:
                    balanced_cards = sorted_units[mid_start:mid_end]
                    return random.choice(balanced_cards)
                return random.choice(unit_actions)
            return pass_action[0] if pass_action else valid_actions[0]
        
        # AGGRESSIVE (60-80): Play high cards, consider row debuff
        elif aggression_level < 80:
            row_debuff_actions = [a for a in special_actions if a.card.card_type == -1]
            if row_debuff_actions:
                best_row = None
                best_impact = 0
                for row in ['melee', 'ranged', 'siege']:
                    row_strength = sum(c.get_current_strength() for c in opp_state.board[row])
                    if row_strength > best_impact and row_strength > 10:
                        best_impact = row_strength
                        best_row = row
                
                if best_row and best_impact > 15:
                    for action in row_debuff_actions:
                        if action.target_row == best_row:
                            return action
            
            if unit_actions:
                sorted_units = sorted(unit_actions, key=lambda a: a.card.strength, reverse=True)
                aggressive_cards = sorted_units[:max(1, len(sorted_units) * 2 // 5)]
                return random.choice(aggressive_cards)
            
            return pass_action[0] if pass_action else valid_actions[0]
        
        # VERY AGGRESSIVE (80-100): Play strongest cards, use scorch
        else:
            scorch_actions = [a for a in special_actions if a.card.card_type == -2]
            if scorch_actions:
                all_cards = []
                for row in ['melee', 'ranged', 'siege']:
                    all_cards.extend([(c, self.player_id) for c in my_state.board[row]])
                    all_cards.extend([(c, 1 - self.player_id) for c in opp_state.board[row]])
                
                if all_cards:
                    max_strength = max(c.get_current_strength() for c, _ in all_cards)
                    my_max_count = sum(1 for c, pid in all_cards 
                                      if pid == self.player_id and c.get_current_strength() == max_strength)
                    opp_max_count = sum(1 for c, pid in all_cards 
                                       if pid != self.player_id and c.get_current_strength() == max_strength)
                    
                    if opp_max_count > my_max_count and max_strength >= 5:
                        return scorch_actions[0]
            
            if unit_actions:
                strongest = max(unit_actions, key=lambda a: a.card.strength)
                return strongest
            
            if special_actions:
                return random.choice(special_actions)
            
            return pass_action[0] if pass_action else valid_actions[0]
