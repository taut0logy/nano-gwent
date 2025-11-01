import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from agents.base_agent import BaseAgent
from core.action import Action

class FISAgent(BaseAgent):
    def __init__(self, player_id):
        super().__init__(player_id)
        self._setup_fuzzy_system()
    
    def _setup_fuzzy_system(self):
        self.strength_diff = ctrl.Antecedent(np.arange(-50, 51, 1), 'strength_diff')
        self.cards_in_hand = ctrl.Antecedent(np.arange(0, 13, 1), 'cards_in_hand')
        self.round_num = ctrl.Antecedent(np.arange(1, 4, 1), 'round_num')
        self.opp_passed = ctrl.Antecedent(np.arange(0, 2, 1), 'opp_passed')
        self.opp_threat = ctrl.Antecedent(np.arange(0, 11, 1), 'opp_threat')
        
        self.action_priority = ctrl.Consequent(np.arange(0, 101, 1), 'action_priority')
        
        self.strength_diff['losing_big'] = fuzz.trimf(self.strength_diff.universe, [-50, -50, -15])
        self.strength_diff['losing_small'] = fuzz.trimf(self.strength_diff.universe, [-20, -10, 0])
        self.strength_diff['even'] = fuzz.trimf(self.strength_diff.universe, [-5, 0, 5])
        self.strength_diff['winning_small'] = fuzz.trimf(self.strength_diff.universe, [0, 10, 20])
        self.strength_diff['winning_big'] = fuzz.trimf(self.strength_diff.universe, [15, 50, 50])
        
        self.cards_in_hand['few'] = fuzz.trimf(self.cards_in_hand.universe, [0, 0, 3])
        self.cards_in_hand['medium'] = fuzz.trimf(self.cards_in_hand.universe, [2, 5, 8])
        self.cards_in_hand['many'] = fuzz.trimf(self.cards_in_hand.universe, [7, 12, 12])
        
        self.round_num['first'] = fuzz.trimf(self.round_num.universe, [1, 1, 1])
        self.round_num['second'] = fuzz.trimf(self.round_num.universe, [2, 2, 2])
        self.round_num['final'] = fuzz.trimf(self.round_num.universe, [3, 3, 3])
        
        self.opp_passed['not_passed'] = fuzz.trimf(self.opp_passed.universe, [0, 0, 0])
        self.opp_passed['passed'] = fuzz.trimf(self.opp_passed.universe, [1, 1, 1])
        
        self.opp_threat['low_threat'] = fuzz.trimf(self.opp_threat.universe, [0, 0, 4])
        self.opp_threat['medium_threat'] = fuzz.trimf(self.opp_threat.universe, [3, 5, 7])
        self.opp_threat['high_threat'] = fuzz.trimf(self.opp_threat.universe, [6, 10, 10])
        
        self.action_priority['very_low'] = fuzz.trimf(self.action_priority.universe, [0, 0, 25])
        self.action_priority['low'] = fuzz.trimf(self.action_priority.universe, [15, 30, 45])
        self.action_priority['medium'] = fuzz.trimf(self.action_priority.universe, [35, 50, 65])
        self.action_priority['high'] = fuzz.trimf(self.action_priority.universe, [55, 70, 85])
        self.action_priority['very_high'] = fuzz.trimf(self.action_priority.universe, [75, 100, 100])
        
        self.rules = self._create_rules()
        self.control_system = ctrl.ControlSystem(self.rules)
        self.simulation = ctrl.ControlSystemSimulation(self.control_system)
    
    def _create_rules(self):
        rules = []
        
        rules.append(ctrl.Rule(self.strength_diff['losing_big'] & self.round_num['final'], self.action_priority['very_high']))
        rules.append(ctrl.Rule(self.strength_diff['losing_small'] & self.round_num['final'], self.action_priority['high']))
        rules.append(ctrl.Rule(self.strength_diff['winning_big'] & self.opp_passed['passed'], self.action_priority['very_low']))
        rules.append(ctrl.Rule(self.strength_diff['winning_small'] & self.opp_passed['passed'], self.action_priority['low']))
        rules.append(ctrl.Rule(self.cards_in_hand['few'] & self.round_num['first'], self.action_priority['medium']))
        rules.append(ctrl.Rule(self.cards_in_hand['many'] & self.round_num['first'], self.action_priority['low']))
        rules.append(ctrl.Rule(self.opp_threat['high_threat'] & self.round_num['final'], self.action_priority['very_high']))
        rules.append(ctrl.Rule(self.opp_threat['low_threat'] & self.strength_diff['winning_big'], self.action_priority['low']))
        
        return rules
    
    def decide_action(self, game_state, valid_actions):
        current_player = game_state.player()
        opponent_player = game_state.opponent()
        
        my_strength = self.calculate_board_strength(current_player.board)
        opp_strength = self.calculate_board_strength(opponent_player.board)
        strength_diff = my_strength - opp_strength
        
        cards_count = len(current_player.hand)
        round_number = game_state.round_number
        opponent_passed = 1 if opponent_player.passed else 0
        
        opp_hand = opponent_player.hand
        if opp_hand:
            unit_cards = [c for c in opp_hand if c.card_type in [0, 1, 2]]
            opp_strongest = max([c.strength for c in unit_cards]) if unit_cards else 0
        else:
            opp_strongest = 0
        
        action_scores = {}
        
        for action in valid_actions:
            try:
                self.simulation.input['strength_diff'] = max(-50, min(50, strength_diff))
                self.simulation.input['cards_in_hand'] = max(0, min(12, cards_count))
                self.simulation.input['round_num'] = round_number
                self.simulation.input['opp_passed'] = opponent_passed
                self.simulation.input['opp_threat'] = max(0, min(10, opp_strongest))
                
                self.simulation.compute()
                score = self.simulation.output['action_priority']
                
                if action.type == Action.PASS:
                    if opponent_passed == 1 and strength_diff > 0:
                        score *= 1.5
                    elif strength_diff < -10 and round_number < 3:
                        score *= 0.3
                    # Penalty for passing when no cards are on board
                    elif my_strength == 0:
                        score *= 0.1  # Very low score for passing without playing anything
                
                elif action.type == Action.PLAY_SPECIAL:
                    # Special cards are only valuable if there are cards on the board
                    total_board_cards = len([c for row in ['melee', 'ranged', 'siege'] 
                                           for c in current_player.board.get(row, []) + opponent_player.board.get(row, [])])
                    
                    if total_board_cards == 0:
                        # No cards on board - special cards are useless
                        score *= 0.1
                    else:
                        # Cards on board - special cards can be valuable
                        if action.card.card_type == -2:  # Scorch
                            # Check if there are high-value targets
                            all_strengths = [c.get_current_strength() for row in ['melee', 'ranged', 'siege']
                                           for c in current_player.board.get(row, []) + opponent_player.board.get(row, [])]
                            if all_strengths and max(all_strengths) >= 7:
                                score *= 1.3  # Good target for scorch
                            else:
                                score *= 0.8  # Not a great target
                        elif action.card.card_type == -1:  # Row debuff
                            # Check if target row has cards
                            target_row = action.target_row
                            if target_row:
                                row_cards = opponent_player.board.get(target_row, [])
                                if len(row_cards) >= 2:
                                    score *= 1.2  # Good target for debuff
                                else:
                                    score *= 0.7  # Not many cards to debuff
                
                elif action.type == Action.PLAY_UNIT:
                    # Playing unit cards is generally good, especially early
                    if round_number == 1 and cards_count > 8:
                        score *= 1.1  # Slight boost for playing units early
                
                action_scores[action] = score
            except Exception as e:
                action_scores[action] = 50
                print(f"Error occurred while scoring action {action}: {e}")

        if not action_scores:
            return valid_actions[0]
        
        return max(action_scores, key=action_scores.get)
