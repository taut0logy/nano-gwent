import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from agents.base_agent import BaseAgent
from core.action import Action
import random

class FISAgent(BaseAgent):
    def __init__(self, player_id):
        super().__init__(player_id)
        self.fuzzy_system = self._build_fuzzy_system()
    
    def _build_fuzzy_system(self):
        """
        Build the Mamdani Fuzzy Inference System with input/output variables,
        membership functions, and fuzzy rules.
        """
        
        # ==================== INPUT VARIABLES ====================
        
        # 1. Strength Difference (current board strength: my - opponent)
        # Range: -100 to 100 (can be negative if losing)
        strength_diff = ctrl.Antecedent(np.arange(-100, 101, 1), 'strength_diff')
        strength_diff['losing_badly'] = fuzz.trapmf(strength_diff.universe, [-100, -100, -30, -15])
        strength_diff['losing'] = fuzz.trimf(strength_diff.universe, [-25, -10, 0])
        strength_diff['tied'] = fuzz.trimf(strength_diff.universe, [-5, 0, 5])
        strength_diff['winning'] = fuzz.trimf(strength_diff.universe, [0, 10, 25])
        strength_diff['winning_big'] = fuzz.trapmf(strength_diff.universe, [15, 30, 100, 100])
        
        # 2. Cards in Hand (resource availability)
        # Range: 0 to 12
        cards_in_hand = ctrl.Antecedent(np.arange(0, 13, 1), 'cards_in_hand')
        cards_in_hand['very_few'] = fuzz.trapmf(cards_in_hand.universe, [0, 0, 1, 3])
        cards_in_hand['few'] = fuzz.trimf(cards_in_hand.universe, [2, 4, 6])
        cards_in_hand['moderate'] = fuzz.trimf(cards_in_hand.universe, [5, 7, 9])
        cards_in_hand['many'] = fuzz.trapmf(cards_in_hand.universe, [8, 10, 12, 12])
        
        # 3. Round Number (game phase)
        # Range: 1 to 3
        round_num = ctrl.Antecedent(np.arange(1, 4, 1), 'round_num')
        round_num['early'] = fuzz.trimf(round_num.universe, [1, 1, 2])
        round_num['mid'] = fuzz.trimf(round_num.universe, [1, 2, 3])
        round_num['late'] = fuzz.trimf(round_num.universe, [2, 3, 3])
        
        # 4. Rounds Won Difference (strategic position)
        # Range: -2 to 2
        rounds_diff = ctrl.Antecedent(np.arange(-2, 3, 1), 'rounds_diff')
        rounds_diff['behind'] = fuzz.trimf(rounds_diff.universe, [-2, -1, 0])
        rounds_diff['tied'] = fuzz.trimf(rounds_diff.universe, [-1, 0, 1])
        rounds_diff['ahead'] = fuzz.trimf(rounds_diff.universe, [0, 1, 2])
        
        # 5. Opponent Cards (opponent's resource state)
        # Range: 0 to 12
        opp_cards = ctrl.Antecedent(np.arange(0, 13, 1), 'opp_cards')
        opp_cards['very_few'] = fuzz.trapmf(opp_cards.universe, [0, 0, 1, 3])
        opp_cards['few'] = fuzz.trimf(opp_cards.universe, [2, 4, 6])
        opp_cards['moderate'] = fuzz.trimf(opp_cards.universe, [5, 7, 9])
        opp_cards['many'] = fuzz.trapmf(opp_cards.universe, [8, 10, 12, 12])
        
        # ==================== OUTPUT VARIABLE ====================
        
        # Aggression Level (how aggressively to play)
        # Range: 0 to 100
        # 0-20: Very Defensive (pass or minimal play)
        # 20-40: Defensive (play low cards, conserve)
        # 40-60: Balanced (moderate play)
        # 60-80: Aggressive (play strong cards)
        # 80-100: Very Aggressive (play strongest cards, use specials)
        aggression = ctrl.Consequent(np.arange(0, 101, 1), 'aggression')
        aggression['very_defensive'] = fuzz.trapmf(aggression.universe, [0, 0, 10, 25])
        aggression['defensive'] = fuzz.trimf(aggression.universe, [15, 30, 45])
        aggression['balanced'] = fuzz.trimf(aggression.universe, [35, 50, 65])
        aggression['aggressive'] = fuzz.trimf(aggression.universe, [55, 70, 85])
        aggression['very_aggressive'] = fuzz.trapmf(aggression.universe, [75, 90, 100, 100])
        
        # ==================== FUZZY RULES ====================
        
        rules = []
        
        # --- EARLY GAME RULES ---
        # Rule 1: Early game + many cards + tied rounds -> Balanced play
        rules.append(ctrl.Rule(round_num['early'] & cards_in_hand['many'] & rounds_diff['tied'],
                               aggression['balanced']))
        
        # Rule 2: Early game + winning + many cards -> Defensive (conserve resources)
        rules.append(ctrl.Rule(round_num['early'] & strength_diff['winning'] & cards_in_hand['many'],
                               aggression['defensive']))
        
        # Rule 3: Early game + losing badly -> Defensive (bait opponent to overcommit)
        rules.append(ctrl.Rule(round_num['early'] & strength_diff['losing_badly'] & cards_in_hand['many'],
                               aggression['very_defensive']))
        
        # Rule 4: Early game + few cards -> Aggressive (need to win this round)
        rules.append(ctrl.Rule(round_num['early'] & cards_in_hand['few'],
                               aggression['aggressive']))
        
        # --- MID GAME RULES ---
        # Rule 5: Mid game + ahead in rounds + winning -> Defensive (protect lead)
        rules.append(ctrl.Rule(round_num['mid'] & rounds_diff['ahead'] & strength_diff['winning'],
                               aggression['very_defensive']))
        
        # Rule 6: Mid game + tied rounds + tied strength -> Balanced
        rules.append(ctrl.Rule(round_num['mid'] & rounds_diff['tied'] & strength_diff['tied'],
                               aggression['balanced']))
        
        # Rule 7: Mid game + behind in rounds -> Aggressive (must win)
        rules.append(ctrl.Rule(round_num['mid'] & rounds_diff['behind'],
                               aggression['very_aggressive']))
        
        # Rule 8: Mid game + winning big -> Defensive (conserve for final)
        rules.append(ctrl.Rule(round_num['mid'] & strength_diff['winning_big'],
                               aggression['very_defensive']))
        
        # --- LATE GAME RULES ---
        # Rule 9: Late game + ahead in rounds -> Very Defensive (just pass)
        rules.append(ctrl.Rule(round_num['late'] & rounds_diff['ahead'],
                               aggression['very_defensive']))
        
        # Rule 10: Late game + behind in rounds -> Very Aggressive (all or nothing)
        rules.append(ctrl.Rule(round_num['late'] & rounds_diff['behind'],
                               aggression['very_aggressive']))
        
        # Rule 11: Late game + tied rounds + winning -> Defensive (small commitment)
        rules.append(ctrl.Rule(round_num['late'] & rounds_diff['tied'] & strength_diff['winning'],
                               aggression['defensive']))
        
        # Rule 12: Late game + tied rounds + losing -> Very Aggressive
        rules.append(ctrl.Rule(round_num['late'] & rounds_diff['tied'] & strength_diff['losing'],
                               aggression['very_aggressive']))
        
        # --- RESOURCE-BASED RULES ---
        # Rule 13: Very few cards + losing -> Very Aggressive (desperation)
        rules.append(ctrl.Rule(cards_in_hand['very_few'] & strength_diff['losing'],
                               aggression['very_aggressive']))
        
        # Rule 14: Very few cards + winning -> Very Defensive (pass and preserve)
        rules.append(ctrl.Rule(cards_in_hand['very_few'] & strength_diff['winning'],
                               aggression['very_defensive']))
        
        # Rule 15: Many cards + opponent has very few -> Aggressive (exploit advantage)
        rules.append(ctrl.Rule(cards_in_hand['many'] & opp_cards['very_few'],
                               aggression['aggressive']))
        
        # Rule 16: Few cards + opponent has many -> Defensive (conserve)
        rules.append(ctrl.Rule(cards_in_hand['few'] & opp_cards['many'],
                               aggression['defensive']))
        
        # --- STRATEGIC RULES ---
        # Rule 17: Winning big + opponent has few cards -> Very Defensive (they're desperate)
        rules.append(ctrl.Rule(strength_diff['winning_big'] & opp_cards['very_few'],
                               aggression['very_defensive']))
        
        # Rule 18: Losing badly + many cards -> Aggressive (fight back)
        rules.append(ctrl.Rule(strength_diff['losing_badly'] & cards_in_hand['moderate'],
                               aggression['aggressive']))
        
        # Rule 19: Tied strength + moderate cards + mid game -> Balanced
        rules.append(ctrl.Rule(strength_diff['tied'] & cards_in_hand['moderate'] & round_num['mid'],
                               aggression['balanced']))
        
        # Rule 20: Ahead in rounds + early game -> Defensive (already have advantage)
        rules.append(ctrl.Rule(rounds_diff['ahead'] & round_num['early'],
                               aggression['defensive']))
        
        # Rule 21: Behind in rounds + early game + many cards -> Aggressive
        rules.append(ctrl.Rule(rounds_diff['behind'] & round_num['early'] & cards_in_hand['many'],
                               aggression['aggressive']))
        
        # Rule 22: Tied everything -> Balanced
        rules.append(ctrl.Rule(strength_diff['tied'] & rounds_diff['tied'] & cards_in_hand['moderate'],
                               aggression['balanced']))
        
        # Rule 23: Late game + tied + very few cards -> Very Aggressive (last chance)
        rules.append(ctrl.Rule(round_num['late'] & rounds_diff['tied'] & cards_in_hand['very_few'],
                               aggression['very_aggressive']))
        
        # Rule 24: Moderate cards + losing -> Aggressive
        rules.append(ctrl.Rule(cards_in_hand['moderate'] & strength_diff['losing'],
                               aggression['aggressive']))
        
        # Rule 25: Many cards + losing + early -> Balanced (have resources to recover)
        rules.append(ctrl.Rule(cards_in_hand['many'] & strength_diff['losing'] & round_num['early'],
                               aggression['balanced']))
        
        # Create control system
        control_system = ctrl.ControlSystem(rules)
        return ctrl.ControlSystemSimulation(control_system)
    
    def decide_action(self, game_state, valid_actions):
        """
        Decide which action to take using the Fuzzy Inference System.
        """
        if len(valid_actions) == 1:
            return valid_actions[0]
        
        # Calculate input variables
        my_state = game_state.players[self.player_id]
        opp_state = game_state.players[1 - self.player_id]
        
        my_strength = my_state.get_board_strength()
        opp_strength = opp_state.get_board_strength()
        strength_difference = my_strength - opp_strength
        
        my_cards = len(my_state.hand)
        opponent_cards = len(opp_state.hand)
        
        rounds_won_diff = my_state.rounds_won - opp_state.rounds_won
        
        # Set fuzzy inputs
        self.fuzzy_system.input['strength_diff'] = max(-100, min(100, strength_difference))
        self.fuzzy_system.input['cards_in_hand'] = my_cards
        self.fuzzy_system.input['round_num'] = game_state.round_number
        self.fuzzy_system.input['rounds_diff'] = rounds_won_diff
        self.fuzzy_system.input['opp_cards'] = opponent_cards
        
        # Compute fuzzy output
        try:
            self.fuzzy_system.compute()
            aggression_level = self.fuzzy_system.output['aggression']
        except Exception:
            # If fuzzy system fails (no rules fired), default to balanced
            aggression_level = 50
        
        # Select action based on aggression level
        action = self._select_action_by_aggression(game_state, valid_actions, aggression_level)
        
        return action
    
    def _select_action_by_aggression(self, game_state, valid_actions, aggression_level):
        """
        Select an action based on the computed aggression level.
        
        Aggression ranges:
        - 0-20: Very Defensive (pass if winning, play lowest card if losing)
        - 20-40: Defensive (play low-medium cards, avoid specials)
        - 40-60: Balanced (play medium cards, consider all options)
        - 60-80: Aggressive (play high cards, consider row debuff)
        - 80-100: Very Aggressive (play highest cards, use scorch)
        """
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
                # Play the weakest card
                weakest = min(unit_actions, key=lambda a: a.card.strength)
                return weakest
            return pass_action[0] if pass_action else valid_actions[0]
        
        # DEFENSIVE (20-40): Play low-medium cards, conserve resources
        elif aggression_level < 40:
            if unit_actions:
                # Play cards in the lower 40% of strength
                sorted_units = sorted(unit_actions, key=lambda a: a.card.strength)
                defensive_cards = sorted_units[:max(1, len(sorted_units) * 2 // 5)]
                return random.choice(defensive_cards)
            return pass_action[0] if pass_action else valid_actions[0]
        
        # BALANCED (40-60): Play medium cards, balanced strategy
        elif aggression_level < 60:
            if unit_actions:
                # Play cards in the middle 40% of strength
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
            # Consider row debuff if opponent has strong cards in a row
            row_debuff_actions = [a for a in special_actions if a.card.card_type == -1]
            if row_debuff_actions:
                # Find opponent's strongest row
                best_row = None
                best_impact = 0
                for row in ['melee', 'ranged', 'siege']:
                    row_strength = sum(c.get_current_strength() for c in opp_state.board[row])
                    if row_strength > best_impact and row_strength > 10:
                        best_impact = row_strength
                        best_row = row
                
                if best_row and best_impact > 15:
                    # Use row debuff on strongest row
                    for action in row_debuff_actions:
                        if action.target_row == best_row:
                            return action
            
            # Otherwise play high-strength cards
            if unit_actions:
                sorted_units = sorted(unit_actions, key=lambda a: a.card.strength, reverse=True)
                # Top 40% of cards
                aggressive_cards = sorted_units[:max(1, len(sorted_units) * 2 // 5)]
                return random.choice(aggressive_cards)
            
            return pass_action[0] if pass_action else valid_actions[0]
        
        # VERY AGGRESSIVE (80-100): Play strongest cards, use scorch
        else:
            # Consider scorch if it benefits us
            scorch_actions = [a for a in special_actions if a.card.card_type == -2]
            if scorch_actions:
                # Check if scorch would help
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
                    
                    # Use scorch if opponent loses more value
                    if opp_max_count > my_max_count and max_strength >= 5:
                        return scorch_actions[0]
            
            # Play the strongest unit card
            if unit_actions:
                strongest = max(unit_actions, key=lambda a: a.card.strength)
                return strongest
            
            # If only special actions remain, use them
            if special_actions:
                return random.choice(special_actions)
            
            return pass_action[0] if pass_action else valid_actions[0]