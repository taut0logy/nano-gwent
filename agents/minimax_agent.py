import math
from agents.base_agent import BaseAgent
from core.action import Action
from core.game_engine import GameEngine

class MinimaxAgent(BaseAgent):
    def __init__(self, player_id):
        super().__init__(player_id)
    
    def decide_action(self, game_state, valid_actions):
        if not valid_actions:
            return Action(Action.PASS)
        
        depth = self._select_search_depth(game_state)
        
        # Order moves for better alpha-beta pruning efficiency
        ordered_actions = self._order_moves(valid_actions, game_state, True)
        
        best_action = None
        best_value = -math.inf
        alpha = -math.inf
        beta = math.inf
        
        for action in ordered_actions:
            sim_state = game_state.clone()
            sim_engine = GameEngine(sim_state)
            
            # Check if round will end to preserve board state
            will_end_round = self._will_action_end_round(sim_state, action)
            pre_resolution_strengths = None
            
            if will_end_round:
                # Store board strengths BEFORE executing action
                pre_resolution_strengths = (
                    sim_state.players[0].get_board_strength(),
                    sim_state.players[1].get_board_strength()
                )
            
            sim_engine.execute_action(action)
            
            # Pass pre-resolution info to evaluation
            value = self._minimax(sim_state, depth - 1, alpha, beta, False, pre_resolution_strengths)
            
            if value > best_value:
                best_value = value
                best_action = action
            
            alpha = max(alpha, value)
            if beta <= alpha:
                break  # Alpha cutoff at root
        
        return best_action if best_action else valid_actions[0]
    
    def _minimax(self, game_state, depth, alpha, beta, maximizing, pre_resolution_strengths=None):
        if depth == 0 or self._is_terminal(game_state):
            return self._evaluate_state(game_state, pre_resolution_strengths)
        
        engine = GameEngine(game_state)
        valid_actions = engine.get_valid_actions()
        
        # Order moves for better pruning
        ordered_actions = self._order_moves(valid_actions, game_state, maximizing)
        
        if maximizing:
            max_eval = -math.inf
            for action in ordered_actions:
                sim_state = game_state.clone()
                sim_engine = GameEngine(sim_state)
                
                # Check if round will end and preserve state
                will_end_round = self._will_action_end_round(sim_state, action)
                pre_res_strengths = None
                
                if will_end_round:
                    pre_res_strengths = (
                        sim_state.players[0].get_board_strength(),
                        sim_state.players[1].get_board_strength()
                    )
                
                sim_engine.execute_action(action)
                
                eval_score = self._minimax(sim_state, depth - 1, alpha, beta, False, pre_res_strengths)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = math.inf
            for action in ordered_actions:
                sim_state = game_state.clone()
                sim_engine = GameEngine(sim_state)
                
                # Check if round will end and preserve state
                will_end_round = self._will_action_end_round(sim_state, action)
                pre_res_strengths = None
                
                if will_end_round:
                    pre_res_strengths = (
                        sim_state.players[0].get_board_strength(),
                        sim_state.players[1].get_board_strength()
                    )
                
                sim_engine.execute_action(action)
                
                eval_score = self._minimax(sim_state, depth - 1, alpha, beta, True, pre_res_strengths)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                
                if beta <= alpha:
                    break
            return min_eval
    
    def _will_action_end_round(self, game_state, action):
        """Check if executing this action will end the round"""
        if action.type == Action.PASS:
            opponent_player = game_state.opponent()
            # Round ends if current player passes and opponent has already passed
            return opponent_player.passed
        return False
    
    def _order_moves(self, actions, game_state, maximizing):
        """
        Order moves for better alpha-beta pruning efficiency.
        Priority (per specification): Special cards > High strength > Medium > Low > Pass
        
        However, special cards should only have high priority when there are cards on board to affect.
        For maximizing player: we want best moves first (special cards, then high strength)
        For minimizing player: we want worst moves first (pass, then low strength)
        """
        # Check if there are any cards on either board
        total_board_cards = 0
        for player_id in [0, 1]:
            player = game_state.players[player_id]
            for row_cards in player.board.values():
                total_board_cards += len(row_cards)
        
        def get_action_priority(action):
            if action.type == Action.PASS:
                return (5, 0)  # Highest number = lowest priority
            
            card = action.card
            if card is None:
                return (5, 0)
            
            # Check if special card (row debuff or scorch)
            if card.card_type in [-1, -2]:
                # Special cards should only be prioritized when there are targets on board
                if total_board_cards > 0:
                    return (1, 0)  # Lowest number = highest priority (when effective)
                else:
                    return (4, 0)  # Low priority when no targets (treat like low strength unit)
            
            # Regular unit cards - prioritize by strength
            strength = card.strength
            if strength >= 7:
                return (2, -strength)  # Negative so higher strength sorts first
            elif strength >= 4:
                return (3, -strength)
            else:
                return (4, -strength)
        
        # Sort actions by priority (lower priority numbers come first)
        sorted_actions = sorted(actions, key=get_action_priority)
        
        # For minimizing player, reverse to get worst moves first
        if not maximizing:
            sorted_actions.reverse()
        
        return sorted_actions
    
    def _is_terminal(self, game_state):
        player0 = game_state.players[0]
        player1 = game_state.players[1]
        
        # Terminal if both players passed (round end)
        if player0.passed and player1.passed:
            return True
        
        # Terminal if someone won the game
        if player0.rounds_won == 2 or player1.rounds_won == 2:
            return True
        
        # Terminal if it's round 3+ and game is over
        if game_state.game_over:
            return True
        
        return False
    
    def _evaluate_state(self, game_state, pre_resolution_strengths=None):
        """
        Evaluate game state from the agent's perspective.
        Uses pre_resolution_strengths if round just ended to avoid information loss.
        """
        my_player = game_state.players[self.player_id]
        opp_player = game_state.players[1 - self.player_id]
        
        round_num = game_state.round_number
        weights = self._get_weights(round_num)
        
        # Component 1: Round Score
        # Use pre-resolution strengths if available (when round just ended)
        if pre_resolution_strengths is not None:
            # Round just ended - use actual board strengths before clearing
            if self.player_id == 0:
                my_strength = pre_resolution_strengths[0]
                opp_strength = pre_resolution_strengths[1]
            else:
                my_strength = pre_resolution_strengths[1]
                opp_strength = pre_resolution_strengths[0]
        else:
            # Normal case - use current board
            my_strength = self.calculate_board_strength(my_player.board)
            opp_strength = self.calculate_board_strength(opp_player.board)
        
        round_score = my_strength - opp_strength
        
        # Component 2: Hand Value
        hand_value = 0
        if my_player.hand:
            unit_cards = [c for c in my_player.hand if c.card_type in [0, 1, 2]]
            if unit_cards:
                avg_strength = sum([c.strength for c in unit_cards]) / len(unit_cards)
                cards_count = len(my_player.hand)
                round_factor = [1.0, 0.7, 0.3][min(round_num, 3) - 1]
                hand_value = avg_strength * cards_count * round_factor
        
        # Component 3: Round Control
        round_control = 0
        if opp_player.passed and not my_player.passed:
            round_control = 50
            if round_score > 0:
                round_control += 20
        elif my_player.passed and not opp_player.passed:
            round_control = -50
            if round_score < 0:
                round_control -= 20
        
        # Component 4: Game Score (rounds won)
        game_score = (my_player.rounds_won - opp_player.rounds_won) * 100
        
        # Component 5: Special Card Advantage
        my_specials = len([c for c in my_player.hand if c.card_type in [-1, -2]])
        opp_specials = len([c for c in opp_player.hand if c.card_type in [-1, -2]])
        special_advantage = (my_specials - opp_specials) * 15
        
        # Calculate total evaluation using specification weights
        total_eval = (weights[0] * round_score +
                      weights[1] * hand_value +
                      weights[2] * round_control +
                      weights[3] * game_score +
                      weights[4] * special_advantage)
        
        return total_eval
    
    def _get_weights(self, round_num):
        """
        Get evaluation weights according to specification.
        weights: [round_score, hand_value, round_control, game_score, special_advantage]
        """
        weight_sets = {
            1: [1.0, 0.8, 0.5, 2.0, 0.6],   # Round 1: balanced approach
            2: [1.5, 0.6, 0.7, 2.5, 0.8],   # Round 2: more aggressive
            3: [2.0, 0.3, 1.0, 3.0, 1.0]    # Round 3: all-in, hand value less important
        }
        return weight_sets.get(round_num, weight_sets[1])
    
    def _select_search_depth(self, game_state):
        current_player = game_state.players[self.player_id]
        
        base_depth = {1: 3, 2: 4, 3: 5}[game_state.round_number]
        
        hand_size = len(current_player.hand)
        if hand_size <= 2:
            base_depth += 1
        
        return base_depth
