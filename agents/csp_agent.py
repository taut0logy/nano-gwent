import math
from agents.base_agent import BaseAgent
from core.action import Action

class CSPAgent(BaseAgent):
    def __init__(self, player_id):
        super().__init__(player_id)
    
    def decide_action(self, game_state, valid_actions):
        if not valid_actions:
            return Action(Action.PASS)
        
        feasible_actions = [a for a in valid_actions if self._satisfies_constraints(a, game_state)]
        
        if not feasible_actions:
            return Action(Action.PASS)
        
        best_action = None
        best_utility = -float('inf')
        
        for action in feasible_actions:
            utility = self._calculate_utility(action, game_state)
            if utility > best_utility:
                best_utility = utility
                best_action = action
        
        return best_action if best_action else feasible_actions[0]
    
    def _satisfies_constraints(self, action, game_state):
        current_player = game_state.player()
        opponent_player = game_state.opponent()
        
        if action.type in [Action.PLAY_UNIT, Action.PLAY_SPECIAL]:
            if action.card not in current_player.hand:
                return False
        
        if action.type == Action.PLAY_SPECIAL:
            if game_state.special_cards_used[action.card.card_type] >= 2:
                return False
        
        if current_player.passed and action.type != Action.PASS:
            return False
        
        if game_state.round_number < 3:
            cards_after = len(current_player.hand) - (1 if action.type != Action.PASS else 0)
            my_strength = self.calculate_board_strength(current_player.board)
            opp_strength = self.calculate_board_strength(opponent_player.board)
            strength_diff = my_strength - opp_strength
            winning_big = strength_diff > 15
            
            if not winning_big and cards_after < 1:
                return False
        
        if game_state.round_number < 3:
            cards_after = len(current_player.hand) - (1 if action.type != Action.PASS else 0)
            rounds_remaining = 3 - game_state.round_number
            
            if cards_after < rounds_remaining:
                return False
        
        return True
    
    def _calculate_utility(self, action, game_state):
        current_player = game_state.player()
        opponent_player = game_state.opponent()
        round_num = game_state.round_number
        
        weights = self._get_weights(round_num)
        
        simulated_state = game_state.clone()
        sim_player = simulated_state.player()
        
        my_strength_before = self.calculate_board_strength(current_player.board)
        opp_strength_before = self.calculate_board_strength(opponent_player.board)
        
        if action.type == Action.PLAY_UNIT and action.card in sim_player.hand:
            sim_player.hand.remove(action.card)
            row_name = {0: "melee", 1: "ranged", 2: "siege"}[action.card.card_type]
            sim_player.board[row_name].append(action.card)
        
        my_strength_after = self.calculate_board_strength(sim_player.board)
        opp_strength_after = self.calculate_board_strength(simulated_state.opponent().board)
        
        strength_adv = (my_strength_after - opp_strength_after) - (my_strength_before - opp_strength_before)
        
        cards_remaining = len(sim_player.hand)
        round_importance = [0.5, 0.7, 1.0][round_num - 1]
        card_efficiency = (cards_remaining / 10.0) * round_importance
        
        special_value = 0
        if action.type == Action.PLAY_SPECIAL:
            if action.card.card_type == -2:
                all_cards = []
                for row in ['melee', 'ranged', 'siege']:
                    all_cards.extend(current_player.board.get(row, []))
                    all_cards.extend(opponent_player.board.get(row, []))
                
                if all_cards:
                    highest_strength = max([c.get_current_strength() for c in all_cards])
                    special_value = highest_strength * 2
            
            elif action.card.card_type == -1:
                my_cards = current_player.board.get(action.target_row, [])
                opp_cards = opponent_player.board.get(action.target_row, [])
                opp_loss = sum([c.get_current_strength() - 1 for c in opp_cards])
                my_loss = sum([c.get_current_strength() - 1 for c in my_cards])
                special_value = max(0, opp_loss - my_loss)
        
        risk_penalty = 0
        if action.type == Action.PLAY_UNIT:
            exposure_factor = 1.0 if not opponent_player.passed else 0.5
            if round_num == 3:
                exposure_factor = 0.0
            risk_penalty = action.card.strength * exposure_factor * (1 - round_num / 3)
        
        win_prob = (1 / (1 + math.exp(-(my_strength_after - opp_strength_after) / 10))) * 100
        
        opponent_hand_threat = self._evaluate_opponent_threat(opponent_player.hand, round_num)
        
        # Add pass penalty - passing should be costly, especially early in rounds
        pass_penalty = 0
        if action.type == Action.PASS:
            # Strong penalty for passing when you haven't played any cards
            if my_strength_after == 0:
                pass_penalty = 200  # Very high penalty for passing without playing anything
            # Penalty based on how early in the round it is (more cards = earlier in round)
            elif cards_remaining > 8:
                pass_penalty = 100  # High penalty for passing early
            elif cards_remaining > 5:
                pass_penalty = 50   # Medium penalty for passing mid-round
            else:
                pass_penalty = 20   # Small penalty for passing late in round
            
            # Reduce penalty if opponent has passed (then passing makes sense)
            if opponent_player.passed:
                pass_penalty = 0
        
        utility = (weights['alpha1'] * strength_adv +
                   weights['alpha2'] * card_efficiency +
                   weights['alpha3'] * special_value -
                   weights['alpha4'] * risk_penalty +
                   weights['alpha5'] * win_prob +
                   weights['alpha6'] * opponent_hand_threat -
                   pass_penalty)  # Subtract pass penalty
        
        return utility
    
    def _get_weights(self, round_num):
        weight_sets = {
            1: {'alpha1': 10, 'alpha2': 5, 'alpha3': 20, 'alpha4': 5, 'alpha5': 8, 'alpha6': 3},
            2: {'alpha1': 15, 'alpha2': 3, 'alpha3': 25, 'alpha4': 2, 'alpha5': 12, 'alpha6': 6},
            3: {'alpha1': 25, 'alpha2': 1, 'alpha3': 30, 'alpha4': 0, 'alpha5': 20, 'alpha6': 10}
        }
        return weight_sets.get(round_num, weight_sets[1])
    
    def _evaluate_opponent_threat(self, opponent_hand, round_num):
        if not opponent_hand:
            return 0
        
        unit_cards = [c for c in opponent_hand if c.card_type in [0, 1, 2]]
        total_strength = sum([c.strength for c in unit_cards]) if unit_cards else 0
        
        scorch_count = sum([1 for c in opponent_hand if c.card_type == -2])
        debuff_count = sum([1 for c in opponent_hand if c.card_type == -1])
        
        strength_threat = total_strength / 10.0
        special_threat = (scorch_count * 3 + debuff_count * 2)
        
        round_multiplier = [1.0, 1.5, 2.0][round_num - 1]
        
        return (strength_threat + special_threat) * round_multiplier
