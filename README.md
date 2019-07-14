# Minesweeper
Python version of the classic Minesweeper game

## Dependencies
- Python 3.6.1 or higher
- Pygame 1.9.6 or higher (available via pip)
- ThorPy 1.6.2 or higher (available via pip)

## Run The Game
```
python ./minesweeper.py
```

## Design notes
- ThorPy elements are used to make the main menu easy to implement
- The ThorPy Application class is not used because it forces a strange rigid design
- Ideally there'd be a way to use the ThorPy paradigm for the menu then leave it behind once the game is launched...
