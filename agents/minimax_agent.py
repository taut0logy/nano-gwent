import math
from agents.base_agent import BaseAgent
from core.action import Action
from core.game_engine import GameEngine

class MinimaxAgent(BaseAgent):
    def __init__(self, player_id, max_depth=3):
        super().__init__(player_id)
        self.max_depth = max_depth
        self.nodes_explored = 0
    
    def decide_action(self, game_state, valid_actions):
        """
        Choose the best action using Minimax with Alpha-Beta pruning.
        """
        if len(valid_actions) == 1:
            return valid_actions[0]
        
        self.nodes_explored = 0
        
        # Filter out PASS from initial consideration if we have other options
        non_pass_actions = [a for a in valid_actions if a.type != Action.PASS]
        
        # If we only have PASS, return it
        if not non_pass_actions:
            return valid_actions[0]
        
        best_action = None
        best_value = -math.inf
        alpha = -math.inf
        beta = math.inf
        
        # Evaluate each possible action
        for action in non_pass_actions:
            # Create a copy of the game state and simulate the action
            new_state = game_state.clone()
            new_engine = GameEngine(new_state)
            new_engine.execute_action(action)
            
            # If game ended after this action, evaluate terminal state
            if new_state.game_over:
                value = self._terminal(new_state)
            else:
                # Otherwise, use minimax to evaluate
                value = self._minimax(new_state, self.max_depth - 1, alpha, beta, False)
            
            if value > best_value:
                best_value = value
                best_action = action
            
            alpha = max(alpha, value)
        
        # If no action was selected (shouldn't happen), pass
        if best_action is None:
            return Action(Action.PASS)
        
        return best_action
    
    def _minimax(self, game_state, depth, alpha, beta, is_maximizing):
        """
        Minimax algorithm with alpha-beta pruning.
        
        Args:
            game_state: Current game state
            depth: Remaining search depth
            alpha: Alpha value for pruning
            beta: Beta value for pruning
            is_maximizing: True if maximizing player's turn
        
        Returns:
            Best value for the current player
        """
        self.nodes_explored += 1
        
        # Terminal conditions
        if game_state.game_over:
            return self._terminal(game_state)
        
        if depth == 0:
            return self._utility(game_state)
        
        engine = GameEngine(game_state)
        valid_actions = engine.get_valid_actions()
        
        # If only PASS is available, execute it and continue
        if len(valid_actions) == 1 and valid_actions[0].type == Action.PASS:
            new_state = game_state.clone()
            new_engine = GameEngine(new_state)
            new_engine.execute_action(valid_actions[0])
            
            if new_state.game_over:
                return self._terminal(new_state)
            else:
                return self._minimax(new_state, depth - 1, alpha, beta, not is_maximizing)
        
        if is_maximizing:
            max_eval = -math.inf
            for action in valid_actions:
                if action.type == Action.PASS and len(valid_actions) > 1:
                    continue  # Skip PASS if we have other options
                
                new_state = game_state.clone()
                new_engine = GameEngine(new_state)
                new_engine.execute_action(action)
                
                if new_state.game_over:
                    eval_score = self._terminal(new_state)
                else:
                    eval_score = self._minimax(new_state, depth - 1, alpha, beta, False)
                
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                
                if beta <= alpha:
                    break  # Beta cutoff
            
            return max_eval
        else:
            min_eval = math.inf
            for action in valid_actions:
                if action.type == Action.PASS and len(valid_actions) > 1:
                    continue  # Skip PASS if we have other options
                
                new_state = game_state.clone()
                new_engine = GameEngine(new_state)
                new_engine.execute_action(action)
                
                if new_state.game_over:
                    eval_score = self._terminal(new_state)
                else:
                    eval_score = self._minimax(new_state, depth - 1, alpha, beta, True)
                
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                
                if beta <= alpha:
                    break  # Alpha cutoff
            
            return min_eval
    
    def _terminal(self, game_state):
        """
        Evaluate a terminal game state (game over).
        Returns a high positive value for win, negative for loss, 0 for draw.
        """
        if game_state.winner is None:
            return 0  # Draw
        elif game_state.winner == self.player_id:
            return 10000  # Win
        else:
            return -10000  # Loss
    
    def _utility(self, game_state):
        """
        Heuristic evaluation function for non-terminal states.
        
        Considers:
        1. Round score difference
        2. Rounds won difference
        3. Cards remaining in hand
        4. Current board strength
        5. Position in the game
        """
        my_state = game_state.players[self.player_id]
        opp_state = game_state.players[1 - self.player_id]
        
        score = 0
        
        # 1. Rounds won difference (most important)
        rounds_diff = my_state.rounds_won - opp_state.rounds_won
        score += rounds_diff * 3000
        
        # 2. Current round board strength difference
        my_strength = my_state.get_board_strength()
        opp_strength = opp_state.get_board_strength()
        strength_diff = my_strength - opp_strength
        
        # Weight strength difference based on whether both players have passed
        if my_state.passed and opp_state.passed:
            # Round is ending, strength difference is critical
            score += strength_diff * 100
        else:
            # Round is ongoing, strength matters but not as much
            score += strength_diff * 50
        
        # 3. Cards in hand advantage (resource advantage)
        hand_diff = len(my_state.hand) - len(opp_state.hand)
        score += hand_diff * 30
        
        # 4. Bonus for having passed when ahead
        if my_state.passed and not opp_state.passed and my_strength > opp_strength:
            score += 200  # Conserving cards while winning
        
        # 5. Penalty for passing when behind
        if my_state.passed and not opp_state.passed and my_strength < opp_strength:
            score -= 300  # Bad position, passed while losing
        
        # 6. Special cards still available (flexibility bonus)
        special_cards_my = sum(1 for c in my_state.hand if c.card_type in [-1, -2])
        special_cards_opp = sum(1 for c in opp_state.hand if c.card_type in [-1, -2])
        score += (special_cards_my - special_cards_opp) * 40
        
        # 7. Position-based evaluation
        if game_state.round_number == 3:
            # Final round - be more aggressive
            score += strength_diff * 20
        elif game_state.round_number == 1:
            # First round - value card conservation
            score += hand_diff * 10
        
        # 8. High-value cards in hand (potential advantage)
        my_high_cards = sum(1 for c in my_state.hand if c.card_type in [0, 1, 2] and c.strength >= 7)
        opp_high_cards = sum(1 for c in opp_state.hand if c.card_type in [0, 1, 2] and c.strength >= 7)
        score += (my_high_cards - opp_high_cards) * 15
        
        return score
