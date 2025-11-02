import math
from agents.base_agent import BaseAgent
from core.action import Action
from core.game_engine import GameEngine

class MinimaxAgent(BaseAgent):
    def __init__(self, player_id, max_depth=6):
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
        1. Rounds won difference (most critical)
        2. Round outcome prediction
        3. Card advantage and quality
        4. Special cards and threats
        5. Board position and debuffs
        6. Strategic passing position
        """
        my_state = game_state.players[self.player_id]
        opp_state = game_state.players[1 - self.player_id]
        
        score = 0
        
        # 1. Rounds won difference (most important - exponential weight)
        rounds_diff = my_state.rounds_won - opp_state.rounds_won
        if rounds_diff >= 1:
            score += 5000  # One round ahead is huge
        elif rounds_diff <= -1:
            score -= 5000  # One round behind is critical
        
        # 2. Current round evaluation
        my_strength = my_state.get_board_strength()
        opp_strength = opp_state.get_board_strength()
        strength_diff = my_strength - opp_strength
        
        # Determine round status
        both_passed = my_state.passed and opp_state.passed
        i_passed = my_state.passed and not opp_state.passed
        opp_passed = opp_state.passed and not my_state.passed
        
        if both_passed:
            # Round is decided - this is critical
            if strength_diff > 0:
                score += 2000  # Winning this round
            elif strength_diff < 0:
                score -= 2000  # Losing this round
            # Draw doesn't change score much
        elif i_passed:
            # I passed, opponent still playing
            if strength_diff > 0:
                # Ahead and conserving cards - good position
                margin = strength_diff
                if margin > 5:
                    score += 800  # Safe lead
                elif margin > 2:
                    score += 400  # Comfortable lead
                else:
                    score += 100  # Risky lead
                
                # Extra bonus for card conservation
                score += len(my_state.hand) * 50
            else:
                # Behind and passed - very bad
                score -= 1000
                score -= abs(strength_diff) * 20
        elif opp_passed:
            # Opponent passed, I'm still playing
            if strength_diff < 0:
                # Behind but can still play - opportunity to catch up
                deficit = abs(strength_diff)
                # Can I catch up with cards in hand?
                my_max_potential = sum(c.strength for c in my_state.hand if c.card_type in [0, 1, 2])
                if my_max_potential > deficit:
                    score += 300  # Can potentially win
                else:
                    score -= 200  # Can't catch up, should conserve cards
            else:
                # Ahead and opponent passed - excellent position
                score += 500
        else:
            # Both still playing - evaluate position
            score += strength_diff * 30
        
        # 3. Card advantage (quality over quantity)
        my_cards = len(my_state.hand)
        opp_cards = len(opp_state.hand)
        hand_diff = my_cards - opp_cards
        
        # Weight card advantage based on game state
        if game_state.round_number == 1:
            score += hand_diff * 60  # Cards very valuable early
        elif game_state.round_number == 2:
            score += hand_diff * 80  # Most critical in round 2
        else:  # Round 3
            score += hand_diff * 40  # Less important in final round
        
        # 4. Card quality evaluation
        my_total_strength = sum(c.strength for c in my_state.hand if c.card_type in [0, 1, 2])
        opp_total_strength = sum(c.strength for c in opp_state.hand if c.card_type in [0, 1, 2])
        score += (my_total_strength - opp_total_strength) * 8
        
        # High-value cards (7+) are more flexible
        my_high_cards = sum(1 for c in my_state.hand if c.card_type in [0, 1, 2] and c.strength >= 7)
        opp_high_cards = sum(1 for c in opp_state.hand if c.card_type in [0, 1, 2] and c.strength >= 7)
        score += (my_high_cards - opp_high_cards) * 25
        
        # 5. Special cards evaluation
        my_scorch = sum(1 for c in my_state.hand if c.card_type == -2)
        opp_scorch = sum(1 for c in opp_state.hand if c.card_type == -2)
        my_debuff = sum(1 for c in my_state.hand if c.card_type == -1)
        opp_debuff = sum(1 for c in opp_state.hand if c.card_type == -1)
        
        # Scorch is powerful when opponent has high cards on board
        if my_scorch > 0:
            opp_board_cards = sum(len(opp_state.board[row]) for row in ['melee', 'ranged', 'siege'])
            if opp_board_cards > 0:
                opp_max_strength = max(
                    (c.get_current_strength() for row in ['melee', 'ranged', 'siege'] 
                     for c in opp_state.board[row]),
                    default=0
                )
                if opp_max_strength >= 8:
                    score += my_scorch * 150  # Very valuable
                else:
                    score += my_scorch * 50
        
        # Debuff cards are valuable
        score += my_debuff * 60
        
        # Opponent having special cards is a threat
        score -= opp_scorch * 100
        score -= opp_debuff * 60
        
        # 6. Board state analysis - check for debuffs
        my_debuffed = sum(1 for row in ['melee', 'ranged', 'siege'] 
                         for c in my_state.board[row] if c.is_debuffed)
        opp_debuffed = sum(1 for row in ['melee', 'ranged', 'siege'] 
                          for c in opp_state.board[row] if c.is_debuffed)
        
        score -= my_debuffed * 30  # Penalty for having debuffed cards
        score += opp_debuffed * 30  # Bonus for opponent having debuffed cards
        
        # 7. Scorch vulnerability - penalty for having highest card on board
        all_cards_on_board = []
        for row in ['melee', 'ranged', 'siege']:
            all_cards_on_board.extend(my_state.board[row])
            all_cards_on_board.extend(opp_state.board[row])
        
        if all_cards_on_board and opp_scorch > 0:
            max_strength = max(c.get_current_strength() for c in all_cards_on_board)
            my_max_cards = [c for c in all_cards_on_board 
                           if c in sum([my_state.board[r] for r in ['melee', 'ranged', 'siege']], [])
                           and c.get_current_strength() == max_strength]
            if my_max_cards:
                score -= len(my_max_cards) * 80  # Vulnerable to scorch
        
        # 8. Strategic depth - penalize being forced to play weak cards
        if not my_state.passed and my_cards > 0:
            avg_card_strength = my_total_strength / max(my_cards - my_scorch - my_debuff, 1)
            if avg_card_strength < 4:
                score -= 50  # Stuck with weak cards
        
        return score
