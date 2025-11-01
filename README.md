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
- [AI Agents](#ai-agents)
- [Project Structure](#project-structure)
- [Required Libraries](#required-libraries)
- [Expected Outcomes](#expected-outcomes)
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
- **Both players receive the SAME 10 cards**
- All 10 cards start in hand (no reserved cards)
- **Special Cards**: Each player has 1 Row Debuff and 1 Scorch card (with the 10 unit cards in hand)
- Total hand size: 12 cards (10 unit + 2 special)

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
  - Reduces **all cards currently in the selected row to strength 1**
  - **Applies to BOTH players** - affects both your cards and opponent's cards in that row
  - Example: Playing Row Debuff on Melee row reduces all Melee cards (yours and opponent's) to strength 1
  - Cards played after Row Debuff are unaffected
  
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
- If a player has no valid moves left, they will be forced to pass
- If a new round begins and a player has no cards left in hand, they automatically pass
- Passed status resets at the start of each new round

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

## AI Agents

- **Agent 1: Fuzzy Inference System (FIS)**
- **Agent 2: Constraint Satisfaction Problem (CSP)**
- **Agent 3: Minimax with Alpha-Beta Pruning**

## Project Structure

```text
nano-gwent/
│
├── README.md
├── requirements.txt
├── main.py                # Game launcher
│
├── assets/                # Game assets
│   ├── images/            # Card images, icons
│   └── sounds/            # Sound effects
│
├── core/
│   ├── __init__.py
│   ├── card.py            # Card class definitions
│   ├── action.py          # Action class definitions
│   ├── game_state.py      # Game state management
│   ├── player_state.py    # Player state management
│   └── game_engine.py     # Game logic and rules
│
├── agents/
│   ├── __init__.py
│   ├── base_agent.py      # Abstract agent class
│   ├── fis_agent.py       # Fuzzy Inference System
│   ├── csp_agent.py       # CSP solver
│   └── minimax_agent.py   # Minimax with alpha-beta
│
├── gui/
│   ├── __init__.py
│   ├── game_gui.py        # Main pygame window
│   ├── config.py          # Values and settings
│   ├── components.py      # Component classes
│   └── menu.py            # Game menu interface
│
└── utils/
    ├── __init__.py
    ├── constants.py       # Game constants
    └── logger.py          # Game logging
```

## Required Libraries

```text
pygame==2.5.2
numpy==1.24.3
scikit-fuzzy==0.4.2
matplotlib==3.7.2
```

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

## Author

Raufun Ahsan
Session: 2020-2021
Department of Computer Science and Engineering
Khulna University of Engineering & Technology (KUET)
