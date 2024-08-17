import itertools
import random

from core import Knowledge
from core import Agent

# Agent starts at (1, 1) and self updates its position every move
# Call the move() method with the percepts at CURRENT position to get the next move

agent = Agent()
percepts = ['G_L', 'W_H']

move = agent.move(percepts)
print(move)