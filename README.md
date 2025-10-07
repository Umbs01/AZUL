# Azul-lite

This project is a Python implementation of a simplified version of the board game Azul, called "Azul-lite". The game supports 2-4 players, which can be a mix of human and AI agents.

The game logic, including move validation and scoring, is handled by a Prolog backend, which is queried from Python using `pyswip`.

## Getting Started

### Prerequisites

- Python 3.x
- SWI-Prolog: The game's logic engine requires a Prolog environment. You can download it from the [SWI-Prolog website](https://www.swi-prolog.org/download/stable).

### Installation

1. **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd AZUL
    ```

2. **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    The required packages are `pygame` and `pyswip`.

## Agent Design

The AI agents are designed based on a goal-based approach. The `README_PEAS.md` file in the repository provides a detailed breakdown of the agent's design using the PEAS (Performance, Environment, Actuators, Sensors) framework.

- **Greedy Agent:** A simple 1-ply agent that maximizes a heuristic utility based on immediate tile placement value and minimizing penalties.
- **Minimax Agent:** A more complex agent that can perform a deeper search to find the optimal move against an opponent.

## Technical Details

- **Frontend:** The GUI is built with **Pygame**.
- **Backend Logic:** Core game rules, move legality, and scoring are defined in **Prolog** (`src/agent/azul.pl`).
- **Bridge:** **PySWIP** is used to connect the Python code with the Prolog engine, allowing the game to query for rule validation.

## Project Structure
```
├── config.json             # Player configuration
├── requirements.txt        # Python package dependencies
├── README.md               # This file
├── README_PEAS.md          # Technical design document for the AI agent
└── src/
    ├── agent/
    │   ├── agents.py       # AI agent implementations (Random, Greedy, Minimax)
    │   └── azul.pl         # Prolog file with game rules and logic
    └── game/
        ├── game.py         # Core game loop and state management
        └── components/
            └── baseUI.py   # UI components for the Pygame
```
