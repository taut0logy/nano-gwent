# Nano Gwent - AI Card Game

A simplified, strategic, turn-based card game inspired by Gwent from The Witcher 3, featuring three AI agents using different decision-making algorithms: Fuzzy Inference System (FIS), Constraint Satisfaction Problem (CSP), and Minimax with Alpha-Beta Pruning.

## Project Overview

This project demonstrates the application of AI algorithms in an adversarial card game environment:

- **Agent 1**: Fuzzy Inference System (FIS) - Rule-based reasoning with fuzzy logic
- **Agent 2**: Constraint Satisfaction Problem (CSP) - Constraint-based optimization
- **Agent 3**: Minimax with Alpha-Beta Pruning - Adversarial search with game tree exploration

Built with Python and pygame for visualization.

## Table of Contents

- [Game Rules](#game-rules)
- [AI Agent Specifications](#ai-agent-specifications)
- [Implementation Guide](#implementation-guide)
- [References](#references)

## Game Rules

### 1. Game Objective

- Win **2 out of 3 rounds** to win the game
- A round is won by having the **highest total strength** on the board after both players pass

### 2. Game Setup

**Card Pool**:

- Pool of **15 Unit Cards**: 5 Melee, 5 Ranged, 5 Siege
- Each card has unique ID (1-15) and strength value (1-10)
- Pool is used only at game start

**Deck Construction**:

- Draw **10 random cards** from the pool at game start
- **Both players receive the SAME 10 cards** (perfect information)
- All 10 cards start in hand (no reserved cards)
- **Special Cards**: Each player has 2 Row Debuff and 2 Scorch cards (with the 10 unit cards in hand)
- Total hand size: 14 cards (10 unit + 4 special)

### 3. Card Types

#### Unit Cards

- **Strength Values**: 1-10
- **Row Assignments**:
  - Melee (Front row)
  - Ranged (Middle row)
  - Siege (Back row)

#### Special Cards

- **Row Debuff Card**:
  - Can be placed on one of the three rows (Melee, Ranged, or Siege)
  - Reduces **all cards in the selected row to strength 1**
  - **Applies to BOTH players** - affects both your cards and opponent's cards in that row
  - Example: Playing Row Debuff on Melee row reduces all Melee cards (yours and opponent's) to strength 1
  
- **Scorch Card**:
  - Destroys the **highest strength card(s)** on the battlefield
  - Applies to **both players** - removes ALL cards with the highest strength value
  - Affects all cards regardless of which player owns them
  - Example: If highest cards are 10 (yours) and 10 (opponent's), both are destroyed

### 4. Game Flow

#### Turn Structure

Players alternate turns. On each turn, a player must choose ONE action:

1. **Play a Unit Card** - Place it in its designated row
2. **Play a Special Card** - Apply Row Debuff or Scorch
3. **Pass** - End participation in the current round

#### Passing Mechanics

- Once a player passes, they **cannot play any more cards** in that round
- The round continues until **both players have passed**
- Passed status resets at the start of each new round
- If a player has no valid moves left, they will be forced to pass
- If a new round begins and a player has no cards left in hand, they automatically pass

#### Round Resolution

- Calculate total strength: Sum of all unit cards across all three rows
- **Winner**: Player with higher total strength
- **Draw**: If total strengths are equal
- Winner takes the round; first to 2 rounds wins the game

### 5. Game Conclusion

#### Winning Conditions

1. First player to win **2 rounds** wins the game
2. If the score is 1-1 after round 3 (draw):
   - **Tiebreaker**: Player with more cards remaining in hand wins

## AI Agent Specifications

### Agent 1: Fuzzy Inference System (FIS)

#### Architecture

Uses **Mamdani Fuzzy Inference** with fuzzification, rule evaluation, and defuzzification.

#### Fuzzy Input Variables

1. **Strength Difference** (My Strength - Opponent Strength)
   - Losing Big: [-50, -15]
   - Losing Small: [-20, -5]
   - Even: [-5, 5]
   - Winning Small: [5, 20]
   - Winning Big: [15, 50]

2. **Cards Left in Hand**
   - Few: [0, 2]
   - Medium: [2, 4]
   - Many: [4, 8]

3. **Round Number**
   - First: [1, 1.3]
   - Second: [1.7, 2.3]
   - Final: [2.7, 3]

4. **Opponent Passed Status**
   - Not Passed: [0, 0.3]
   - Passed: [0.7, 1]

5. **Opponent Hand Threat** (Perfect Information)
   - Low Threat: [0, 5] - Opponent's strongest card ≤ 5
   - Medium Threat: [4, 8] - Opponent's strongest card 5-8
   - High Threat: [7, 10] - Opponent's strongest card ≥ 8

#### Fuzzy Output Variables

**Action Priority** (0-100 scale for each action type):

- Play Strongest Unit
- Play Weakest Unit
- Play Medium Unit
- Play Row Debuff
- Play Scorch
- Pass

#### Fuzzy Rules (35 rules)

**Conservative Play (First Round)**

1. IF First Round AND Many Cards → Play Weakest Unit
2. IF First Round AND Losing Small → Play Medium Unit
3. IF First Round AND Losing Big → Pass

**Aggressive Play (Final Round)**
4. IF Final Round AND Losing → Play Strongest Unit
5. IF Final Round AND Winning Small → Play Medium Unit
6. IF Final Round AND Many Cards AND Losing → Play Strongest Unit

**Passing Strategy**
7. IF Winning Big AND Opponent Passed → Pass
8. IF Winning Small AND Opponent Passed AND Final Round → Pass
9. IF Losing Big AND Few Cards → Pass
10. IF Second Round AND Winning AND Few Cards → Pass

**Special Card Usage**
11. IF Losing Big AND Opponent Has Strong Row → Play Row Debuff
12. IF Even AND Opponent Has Cards with Strength ≥ 8 → Play Scorch
13. IF Final Round AND Losing AND Has Scorch → Play Scorch
14. IF Opponent Passed AND Losing AND Has Row Debuff → Play Row Debuff

**Perfect Information Rules (Opponent Hand Awareness)**
15. IF High Opponent Threat AND Final Round AND Winning Small → Play Strongest Unit
16. IF Low Opponent Threat AND Losing Small → Play Medium Unit (save strongest)
17. IF High Opponent Threat AND Has Scorch AND Even → Play Scorch
18. IF Medium Opponent Threat AND Opponent Not Passed AND Round 2 → Play Medium Unit
19. IF High Opponent Threat AND Losing Big → Play Strongest Unit or Scorch

**Mid-Game Strategy**
15. IF Second Round AND Even AND Medium Cards → Play Medium Unit
16. IF Second Round AND Winning Big → Pass
17. IF Second Round AND Losing Small AND Many Cards → Play Strongest Unit

**Card Conservation**
18. IF Winning AND Many Cards AND First Round → Play Weakest Unit
19. IF Winning Small AND Few Cards → Pass
20. IF Even AND Few Cards AND NOT Final Round → Pass

**Reactive Play**
21. IF Opponent Passed AND Winning → Pass
22. IF Opponent Passed AND Losing AND Has Cards → Play Strongest Unit
23. IF Opponent Passed AND Even → Play Weakest Unit

**Resource Management**
24. IF Many Cards AND First Round AND Even → Play Weakest Unit
25. IF Few Cards AND Second Round AND Losing → Play Strongest Unit
26. IF Medium Cards AND Final Round → Play Strongest Unit

**Additional Strategic Rules**
27. IF Losing Small AND Medium Cards AND Second Round → Play Medium Unit
28. IF Winning Big AND Final Round → Pass
29. IF Even AND Many Cards AND Second Round → Play Medium Unit
30. IF First Round AND Opponent Passed AND Winning → Pass

#### Decision Process

1. Fuzzify all input variables
2. Evaluate all 30 rules
3. Aggregate outputs for each action type
4. Defuzzify to get priority scores
5. Select valid action with highest priority score

---

### Agent 2: Constraint Satisfaction Problem (CSP)

#### Problem Formulation

**Variables**

- Action for current turn: {Play Unit Card X, Play Special Card Y, Pass}

**Domains**

- All legal moves from current hand state

**Constraints** (Hard Constraints - Must Satisfy)

1. **Card Availability**: Cannot play cards not in hand
2. **Special Card Limit**: Each special card type used at most twice per game
3. **Pass Irreversibility**: Once passed, cannot play cards in current round
4. **Card Preservation**: Must keep at least 1 card if not in final round (unless winning big)
5. **Round Limit**: Cannot play more cards than remaining in hand across future rounds

**Soft Constraints** (Optimization Goals)

- Minimize cards played in early rounds
- Maximize board advantage
- Save special cards for critical moments

#### Objective Function

For each valid move, calculate a **utility score**:

```text
Utility = α₁×StrengthAdvantage + α₂×CardEfficiency + α₃×SpecialCardValue 
          - α₄×Risk + α₅×WinProbability + α₆×OpponentThreatMitigation

Where:
- StrengthAdvantage = (MyStrength - OpponentStrength) after move
- CardEfficiency = (RemainingCards / MaxCards) × RoundImportance
- SpecialCardValue = Bonus for optimal special card timing
- Risk = Penalty for exposing strong cards early
- WinProbability = Sigmoid function of strength difference
- OpponentThreatMitigation = Response to opponent's known strongest cards (Perfect Info)
```

**Weight Parameters**:

- Round 1: α₁=10, α₂=5, α₃=20, α₄=5, α₅=8, α₆=3
- Round 2: α₁=15, α₂=3, α₃=25, α₄=2, α₅=12, α₆=6
- Round 3: α₁=25, α₂=1, α₃=30, α₄=0, α₅=20, α₆=10

**Perfect Information Advantage**: OpponentThreatMitigation component uses knowledge of opponent's exact remaining cards to prepare appropriate responses.

#### CSP Solving Algorithm

**Algorithm**: Backtracking with Forward Checking and Constraint Propagation

```text
function CSP_SelectMove(gameState):
    validMoves = GetLegalMoves(gameState)
    
    # Filter by hard constraints
    feasibleMoves = []
    for move in validMoves:
        if SatisfiesAllConstraints(move, gameState):
            feasibleMoves.append(move)
    
    # If no feasible moves, must pass
    if len(feasibleMoves) == 0:
        return PASS
    
    # Evaluate utility for each feasible move
    bestMove = None
    bestUtility = -infinity
    
    for move in feasibleMoves:
        utility = CalculateUtility(move, gameState)
        if utility > bestUtility:
            bestUtility = utility
            bestMove = move
    
    return bestMove
```

#### Special Card Timing (CSP Logic)

**Row Debuff Optimal Conditions**:

- Target row has net positive value (opponent cards > your cards in strength)
- Opponent has more high-strength cards in target row than you
- Net strength gain after debuff is positive
- Example: If opponent has 3 cards (strength 7,6,5) and you have 1 card (strength 4) in Melee:
  - Before: Opponent=18, You=4, Net=-14
  - After: Opponent=3, You=1, Net=-2
  - Gain = 12 points improvement

**Scorch Optimal Conditions**:

- Highest card(s) on battlefield belong to opponent OR tie
- Scorch would improve your position
- Risk of losing own high card is acceptable
- Note: Scorch destroys ALL cards with highest strength (both players)

---

### Agent 3: Minimax with Alpha-Beta Pruning

#### Algorithm Overview

Uses **adversarial search** to explore the game tree and find optimal moves by assuming opponent plays optimally.

#### Game Tree Representation

**Node Structure**:

```text
Node:
  - gameState (board, hands, passed status, round number)
  - player (current player to move)
  - depth (remaining search depth)
  - alpha (best value for maximizer)
  - beta (best value for minimizer)
```

**Terminal States**:

- Both players have passed (round ends)
- Depth limit reached
- Game over (2 rounds won by a player)

#### Evaluation Function

```text
Eval(state) = w1 × RoundScore + w2 × HandValue + w3 × RoundControl + w4 × GameScore

Components:

1. RoundScore = MyBoardStrength - OpponentBoardStrength
   
2. HandValue = Average strength of remaining cards × cards_in_hand
   
3. RoundControl = 
   - +50 if opponent passed and I haven't
   - -50 if I passed and opponent hasn't
   - 0 if both passed or both active
   
4. GameScore = (MyRoundsWon - OpponentRoundsWon) × 100

Weights by Round:
Round 1: w1=1.0, w2=0.8, w3=0.5, w4=2.0
Round 2: w1=1.5, w2=0.6, w3=0.7, w4=2.5
Round 3: w1=2.0, w2=0.3, w3=1.0, w4=3.0
```

#### Minimax Algorithm with Alpha-Beta Pruning

```python
function Minimax(state, depth, alpha, beta, maximizingPlayer):
    # Base cases
    if depth == 0 OR state.isTerminal():
        return Evaluate(state), None
    
    if maximizingPlayer:
        maxEval = -infinity
        bestMove = None
        
        for move in GetLegalMoves(state):
            newState = ApplyMove(state, move)
            eval, _ = Minimax(newState, depth-1, alpha, beta, False)
            
            if eval > maxEval:
                maxEval = eval
                bestMove = move
            
            alpha = max(alpha, eval)
            if beta <= alpha:
                break  # Beta cutoff
        
        return maxEval, bestMove
    
    else:  # Minimizing player
        minEval = +infinity
        bestMove = None
        
        for move in GetLegalMoves(state):
            newState = ApplyMove(state, move)
            eval, _ = Minimax(newState, depth-1, alpha, beta, True)
            
            if eval < minEval:
                minEval = eval
                bestMove = move
            
            beta = min(beta, eval)
            if beta <= alpha:
                break  # Alpha cutoff
        
        return minEval, bestMove
```

#### Depth Limits

To manage computational complexity:

- **Round 1**: Depth = 3 (explores 3 moves ahead)
- **Round 2**: Depth = 4
- **Round 3**: Depth = 5 (deeper search in critical round)

#### Move Ordering Optimization

To improve alpha-beta pruning efficiency, prioritize moves:

1. **Special cards** (high impact)
2. **High strength unit cards** (when losing)
3. **Medium strength unit cards**
4. **Low strength unit cards** (when winning)
5. **Pass** (last resort)

#### Iterative Deepening (Optional Enhancement)

```python
function IterativeDeepening(state, maxDepth, timeLimit):
    bestMove = None
    
    for depth in range(1, maxDepth+1):
        eval, move = Minimax(state, depth, -infinity, +infinity, True)
        bestMove = move
        
        if timeExpired(timeLimit):
            break
    
    return bestMove
```

---

## Implementation Guide

### Project Structure

```text
nano-gwent/
│
├── README.md
├── requirements.txt
├── main.py                # Game launcher
│
├── assets/                # Game assets (images, sounds)
│
├── game/
│   ├── __init__.py
│   ├── card.py            # Card class definitions
│   ├── deck.py            # Deck management
│   ├── board.py           # Game board state
│   ├── game_engine.py     # Game logic and rules
│   └── round_manager.py   # Round management
│
├── agents/
│   ├── __init__.py
│   ├── base_agent.py      # Abstract agent class
│   ├── fis_agent.py       # Fuzzy Inference System
│   ├── csp_agent.py       # CSP solver
│   └── minimax_agent.py   # Minimax with alpha-beta
│
├── ai/
│   ├── __init__.py
│   ├── fuzzy_system.py    # Fuzzy logic implementation
│   ├── csp_solver.py      # CSP constraint solver
│   └── minimax.py         # Minimax algorithm
│
├── gui/
│   ├── __init__.py
│   ├── game_window.py     # Main pygame window
│   ├── board_renderer.py  # Board visualization
│   └── animations.py      # Card animations
│
└── utils/
    ├── __init__.py
    ├── constants.py       # Game constants
    └── logger.py          # Game logging
```

### Key Classes

#### Card Class

```python
class Card:
    def __init__(self, id, card_type):
        self.card_type = card_type  # 0 = melee, 1 = ranged, 2 = siege, -1 = row_debuff, -2 = scorch
        self.id = id
        self.is_debuffed = False
        self.strength = constants.CARD_STRENGTHS[id - 1] if id - 1 < len(constants.CARD_STRENGTHS) and id - 1 >= 0 else 0
```

### Player State

```python
# Example PlayerState class structure
class PlayerState:
    def __init__(self, player_id):
       self.id = player_id
       self.hand = []
       self.board = {"melee": [], "ranged": [], "siege": []}
       self.passed = False
       self.rounds_won = 0
```

### Game State

```python
# Example GameState class structure
class GameState:
    def __init__(self):
        self.initial_hand = []  # The initial 10 cards dealt to both players
        self.round_number = 1
        self.current_player = 0 # 0 = Player 1, 1 = Player 2, player 1 starts first
        self.players = {
            0: PlayerState(0),
            1: PlayerState(1)
        }
    
   def initialize(self):
        """This function initializes the game state at the start of the game"""
        import random
        card_pool = constants.CARD_POOL
        self.initial_hand = random.sample(card_pool, 10)
        self.p1_hand = self.initial_hand.copy()
        self.p2_hand = self.initial_hand.copy()

    def clone(self):
        """Deep copy for AI simulation"""
        return copy.deepcopy(self)

   def player(self):
      """Returns the current player's state"""
      return self.players[self.current_player]
   
   def opponent(self):
      """Returns the opponent's state"""
      return self.players[1 - self.current_player]
```

```python
class GameState:
    def __init__(self):
        self.initial_hand = []  # Initial hand, this is copied to both players at game start
        self.round_number = 1
        self.current_player = 1
    
    def initialize(self):
        # This function initializes the game state at the start of the game
        import random
        card_pool = constants.CARD_POOL
        self.initial_hand = random.sample(card_pool, 10)
        self.p1_hand = self.initial_hand.deepcopy()
        self.p2_hand = self.initial_hand.deepcopy()

    def clone(self):
        """Deep copy for AI simulation"""
        return copy.deepcopy(self)
```

### Agent Interface

```python
# Example base agent class
class BaseAgent:
    def __init__(self, player_id):
        self.player_id = player_id
    
    def decide_action(self, game_state):
        """
        Given a game state, return chosen action
        Returns: Action object (play card, pass, etc.)
        """
        raise NotImplementedError
```

### Development Phases

1. **Phase 1**: Core game engine (cards, board, rules)
2. **Phase 2**: Agent 1 - FIS implementation
3. **Phase 3**: Agent 2 - CSP solver
4. **Phase 4**: Agent 3 - Minimax algorithm
5. **Phase 5**: GUI with pygame
6. **Phase 6**: Testing and balancing

### Required Libraries

```text
pygame==2.5.2
numpy==1.24.3
scikit-fuzzy==0.4.2
matplotlib==3.7.2
```

## Testing Strategy

### Unit Tests

- Card mechanics
- Board state transitions
- Rule enforcement
- Each AI agent decision-making

### Integration Tests

- Full game simulations
- Agent vs Agent matchups
- Edge cases (empty deck, all cards played)

### Performance Tests

- Minimax depth analysis
- FIS rule evaluation time
- CSP constraint solving speed

## Expected Outcomes

### Agent Performance Characteristics

**FIS Agent**:

- Fast decision-making
- Consistent strategy
- Rule-based transparency
- May miss complex multi-turn strategies

**CSP Agent**:

- Optimal single-turn decisions
- Resource-efficient
- Constraint-aware play
- Limited lookahead

**Minimax Agent**:

- Strong multi-turn planning
- Adapts to opponent
- Computationally intensive
- Most competitive in testing

### Comparison Metrics

- Win rate (head-to-head)
- Average cards played per game
- Round win distribution
- Decision time per move

## References

1. CD Projekt Red. (2015). *Gwent: The Witcher Card Game – Official Rules*
2. [pygame Documentation.](https://www.pygame.org)
3. Kose, U. (2012). "Developing a fuzzy logic-based game system"
4. Russell, S., & Norvig, P. (2020). *Artificial Intelligence: A Modern Approach* (4th ed.)
5. [Scikit-fuzzy Documentation.](https://pythonhosted.org/scikit-fuzzy/)
6. Dechter, R. (2003). *Constraint Processing*
7. Knuth, D. E., & Moore, R. W. (1975). "An analysis of alpha-beta pruning"

---

## License

This project is for educational purposes as part of CSE 4110 – Artificial Intelligence Laboratory.

## Authors

Built as part of CSE 4110 AI Lab Project
