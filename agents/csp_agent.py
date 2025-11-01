from agents.base_agent import BaseAgent
from core.action import Action
from core.game_engine import GameEngine
import random

class CSPAgent(BaseAgent):
    """
    Constraint Satisfaction Problem (CSP) Agent for Nano Gwent.
    
    The CSP formulation:
    - Variables: Available actions (cards to play or pass)
    - Domain: Valid actions from game state
    - Constraints: Game rules + strategic constraints
    - Objective: Maximize utility while satisfying constraints
    
    Approach: Constraint-based optimization with heuristic evaluation
    """
    
    def __init__(self, player_id):
        super().__init__(player_id)
        self.action_history = []
    
    def decide_action(self, game_state, valid_actions):
        """
        Use CSP-based reasoning to select the best action.
        """
        if len(valid_actions) == 1:
            return valid_actions[0]
        
        # Get game context
        my_state = game_state.players[self.player_id]
        opp_state = game_state.players[1 - self.player_id]
        
        # Filter actions by hard constraints
        feasible_actions = self._apply_hard_constraints(
            game_state, valid_actions, my_state, opp_state
        )
        
        if not feasible_actions:
            # If no actions satisfy hard constraints, relax and use all valid actions
            feasible_actions = valid_actions
        
        # Evaluate each feasible action with soft constraints (utility function)
        action_scores = []
        for action in feasible_actions:
            score = self._evaluate_action(game_state, action, my_state, opp_state)
            action_scores.append((action, score))
        
        # Sort by score and select best action
        action_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return best action
        best_action = action_scores[0][0]
        self.action_history.append(best_action)
        
        return best_action
    
    def _apply_hard_constraints(self, game_state, valid_actions, my_state, opp_state):
        """
        Apply hard constraints to filter out invalid/suboptimal actions.
        Hard constraints are rules that must be satisfied.
        """
        feasible = []
        
        my_strength = my_state.get_board_strength()
        opp_strength = opp_state.get_board_strength()
        my_cards = len(my_state.hand)
        rounds_won_diff = my_state.rounds_won - opp_state.rounds_won
        
        for action in valid_actions:
            # Constraint 1: Don't pass if we're losing and can still play cards
            if action.type == Action.PASS:
                # Allow passing if:
                # - We're winning
                # - We have no cards
                # - Opponent has passed and we're tied/winning
                # - We're ahead in rounds and in a good position
                if my_strength > opp_strength:
                    feasible.append(action)
                elif my_cards == 0:
                    feasible.append(action)
                elif opp_state.passed and my_strength >= opp_strength:
                    feasible.append(action)
                elif rounds_won_diff > 0 and game_state.round_number >= 2:
                    feasible.append(action)
                # Skip pass if losing and have cards (hard constraint)
                continue
            
            # Constraint 2: Don't play weak cards when losing badly (unless desperate)
            if action.type == Action.PLAY_UNIT:
                if my_strength < opp_strength - 15 and my_cards > 3:
                    # Losing badly - don't play weak cards (strength < 5)
                    if action.card.strength < 5:
                        continue  # Skip weak cards
                
                # Constraint 3: Don't play high-value cards early when winning big
                if game_state.round_number == 1 and my_strength > opp_strength + 10:
                    if action.card.strength >= 8 and my_cards >= 7:
                        continue  # Save high cards
            
            # Constraint 4: Special card usage constraints
            if action.type == Action.PLAY_SPECIAL:
                if action.card.card_type == -1:  # Row Debuff
                    # Only use if target row has significant strength
                    target_row_strength = sum(c.get_current_strength() 
                                             for c in opp_state.board[action.target_row])
                    if target_row_strength < 8:
                        continue  # Don't waste on weak rows
                    
                    # Don't debuff if it hurts us more than opponent
                    my_row_strength = sum(c.get_current_strength() 
                                         for c in my_state.board[action.target_row])
                    if my_row_strength > target_row_strength:
                        continue  # Would hurt us more
                
                elif action.card.card_type == -2:  # Scorch
                    # Only use scorch if it helps us
                    all_cards = []
                    for row in ['melee', 'ranged', 'siege']:
                        all_cards.extend([(c, self.player_id) for c in my_state.board[row]])
                        all_cards.extend([(c, 1 - self.player_id) for c in opp_state.board[row]])
                    
                    if all_cards:
                        max_strength = max(c.get_current_strength() for c, _ in all_cards)
                        my_loss = sum(c.get_current_strength() for c, pid in all_cards 
                                     if pid == self.player_id and c.get_current_strength() == max_strength)
                        opp_loss = sum(c.get_current_strength() for c, pid in all_cards 
                                      if pid != self.player_id and c.get_current_strength() == max_strength)
                        
                        # Only use if opponent loses more or equal value
                        if my_loss > opp_loss:
                            continue  # Don't use scorch if we lose more
                        if opp_loss == 0:
                            continue  # No effect
            
            # Action satisfies all hard constraints
            feasible.append(action)
        
        return feasible if feasible else valid_actions
    
    def _evaluate_action(self, game_state, action, my_state, opp_state):
        """
        Evaluate an action using a utility function with soft constraints.
        Higher score = better action.
        """
        score = 0.0
        
        # Get current state information
        my_strength = my_state.get_board_strength()
        opp_strength = opp_state.get_board_strength()
        my_cards = len(my_state.hand)
        opp_cards = len(opp_state.hand)
        rounds_won_diff = my_state.rounds_won - opp_state.rounds_won
        strength_diff = my_strength - opp_strength
        round_num = game_state.round_number
        
        # Simulate action to get resulting state
        sim_state = game_state.clone()
        sim_engine = GameEngine(sim_state)
        sim_engine.execute_action(action)
        
        sim_my_state = sim_state.players[self.player_id]
        sim_opp_state = sim_state.players[1 - self.player_id]
        sim_my_strength = sim_my_state.get_board_strength()
        sim_opp_strength = sim_opp_state.get_board_strength()
        sim_strength_diff = sim_my_strength - sim_opp_strength
        
        # === OBJECTIVE 1: Maximize strength difference ===
        strength_improvement = sim_strength_diff - strength_diff
        score += strength_improvement * 10
        
        # === OBJECTIVE 2: Win the round with minimum investment ===
        if sim_strength_diff > 0:
            # Winning - bonus for being ahead
            score += 100
            
            # Prefer minimal lead (save cards for later)
            if sim_strength_diff <= 5:
                score += 50  # Optimal lead
            elif sim_strength_diff > 15:
                score -= 30  # Overcommitting
        
        # === OBJECTIVE 3: Resource efficiency ===
        if action.type == Action.PLAY_UNIT:
            # Efficiency: strength gained per card played
            efficiency = action.card.strength / max(1, my_cards)
            score += efficiency * 5
            
            # Bonus for appropriate strength cards based on situation
            if strength_diff < -10:
                # Losing - prefer high-strength cards
                if action.card.strength >= 7:
                    score += 40
            elif strength_diff > 10:
                # Winning - prefer low-strength cards
                if action.card.strength <= 5:
                    score += 30
            else:
                # Tied - prefer medium-strength cards
                if 4 <= action.card.strength <= 7:
                    score += 25
        
        # === OBJECTIVE 4: Round-specific strategies ===
        if round_num == 1:
            # Early round - conservative play
            if action.type == Action.PASS and strength_diff > 3:
                score += 200  # Pass early when winning
            if action.type == Action.PLAY_UNIT and action.card.strength >= 8:
                score -= 50  # Penalty for high cards early
        
        elif round_num == 2:
            # Mid round - balanced play
            if rounds_won_diff > 0:
                # Already won a round - can be conservative
                if action.type == Action.PASS and strength_diff >= 0:
                    score += 150
            elif rounds_won_diff < 0:
                # Lost first round - must win this
                if action.type == Action.PLAY_UNIT and action.card.strength >= 6:
                    score += 60
        
        elif round_num == 3:
            # Final round - decisive play
            if rounds_won_diff > 0:
                # Already winning - just need to not lose
                if action.type == Action.PASS:
                    score += 300
            elif rounds_won_diff < 0:
                # Must win - all in
                if action.type == Action.PLAY_UNIT:
                    score += action.card.strength * 15
            else:
                # Tied - must win this round
                if action.type == Action.PLAY_UNIT:
                    score += action.card.strength * 12
        
        # === OBJECTIVE 5: Special card value ===
        if action.type == Action.PLAY_SPECIAL:
            if action.card.card_type == -1:  # Row Debuff
                # Calculate impact
                target_row = action.target_row
                opp_row_cards = opp_state.board[target_row]
                my_row_cards = my_state.board[target_row]
                
                opp_loss = sum(c.get_current_strength() - 1 
                              for c in opp_row_cards if c.get_current_strength() > 1)
                my_loss = sum(c.get_current_strength() - 1 
                             for c in my_row_cards if c.get_current_strength() > 1)
                
                net_gain = opp_loss - my_loss
                score += net_gain * 15
                
                # Bonus for good timing
                if opp_cards < my_cards and net_gain > 10:
                    score += 100  # Opponent can't recover easily
            
            elif action.card.card_type == -2:  # Scorch
                # Calculate scorch value
                all_cards = []
                for row in ['melee', 'ranged', 'siege']:
                    all_cards.extend([(c, self.player_id) for c in my_state.board[row]])
                    all_cards.extend([(c, 1 - self.player_id) for c in opp_state.board[row]])
                
                if all_cards:
                    max_strength = max(c.get_current_strength() for c, _ in all_cards)
                    my_loss = sum(c.get_current_strength() for c, pid in all_cards 
                                 if pid == self.player_id and c.get_current_strength() == max_strength)
                    opp_loss = sum(c.get_current_strength() for c, pid in all_cards 
                                  if pid != self.player_id and c.get_current_strength() == max_strength)
                    
                    net_gain = opp_loss - my_loss
                    score += net_gain * 20
                    
                    # Bonus for high-value scorches
                    if opp_loss >= 10 and my_loss == 0:
                        score += 150
        
        # === OBJECTIVE 6: Opponent modeling ===
        if opp_state.passed:
            # Opponent passed - be conservative
            if action.type == Action.PASS and sim_strength_diff >= 0:
                score += 250  # Match their pass if winning
            elif action.type == Action.PLAY_UNIT:
                # Play minimal card to win
                if sim_strength_diff > 0 and sim_strength_diff <= 5:
                    score += 100
        
        # === OBJECTIVE 7: Card advantage ===
        card_advantage = my_cards - opp_cards
        if card_advantage > 2:
            # We have more cards - can afford to invest
            score += 20
        elif card_advantage < -2:
            # Opponent has more cards - be conservative
            if action.type == Action.PASS and strength_diff >= 0:
                score += 50
        
        # === OBJECTIVE 8: Tiebreaker consideration ===
        if round_num == 3 and rounds_won_diff == 0:
            # Final round, tied - card count matters
            if my_cards > opp_cards:
                # We'd win tiebreaker - can pass if tied
                if action.type == Action.PASS and strength_diff == 0:
                    score += 200
            else:
                # They'd win tiebreaker - must win this round
                if action.type == Action.PLAY_UNIT:
                    score += 50
        
        # === OBJECTIVE 9: Avoid desperation plays ===
        if my_cards <= 2 and round_num <= 2:
            # Low on cards early - penalty for playing
            if action.type == Action.PLAY_UNIT:
                score -= 40
        
        # === OBJECTIVE 10: Random tiebreaking ===
        # Add small random noise to break ties
        score += random.uniform(-1, 1)
        
        return score
    
    def _calculate_strength_after_action(self, game_state, action, player_id):
        """
        Calculate board strength after applying an action.
        Helper method for lookahead.
        """
        sim_state = game_state.clone()
        sim_engine = GameEngine(sim_state)
        sim_engine.execute_action(action)
        return sim_state.players[player_id].get_board_strength()
    
    def _get_card_value_tier(self, strength):
        """
        Categorize cards by strength tier.
        """
        if strength <= 3:
            return "low"
        elif strength <= 6:
            return "medium"
        elif strength <= 8:
            return "high"
        else:
            return "very_high"
    
    
