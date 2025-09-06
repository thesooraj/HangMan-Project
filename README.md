# Hangman — TDD Python
### By  Suraj
This project is a Hangman game implemented in Python using a Test-Driven Development (TDD)approach with `pytest`.

The game includes two difficulty levels to choose from:

- **Basic**: Guess single words.  
- **Intermediate**: Guess phrases — spaces and punctuation are revealed by default.

---

## Features

- Words and phrases are dynamically loaded from dictionary files located in the `words/` directory.
- A 15-second timer for each guess with a visible countdown adds a layer of challenge.
- Running out of time on a guess automatically deducts one life.
- Correct letter guesses reveal all occurrences of that letter in the answer.
- Incorrect guesses deduct a life. The game ends when the player has 0 lives remaining.
- Players can guess the entire word or phrase at any time. An incorrect full guess will deduct one life.
- The project includes a comprehensive suite of unit tests, enabling continuous integration and ensuring code reliability.

---

## Project Structure

```
hangman-tdd-python/
│
├── src/
│   └── hangman.py        
│
├── tests/
│   └── test_hangman.py   
├── words/
│   ├── words_basic.txt   
│   └── phrases.txt        
│
└── README.md             
```

---

## Quick Start

Follow these steps to get the game running on your local machine.

### 1. Create and activate a virtual environment

```bash
python3 -m venv .venv
# macOS / Linux
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

> _Note:_ `requirements.txt` should include `pytest` and any other runtime dependencies your project uses.

### 3. Run tests

```bash
python -m pytest -q
```

### 4. Play the game

```bash
python src/hangman.py
```

---




