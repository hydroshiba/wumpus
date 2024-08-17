# node.py
# =============================================================================
#  Description to be updated.
# =============================================================================

class Node:
	def __init__(self, state, par, act, dir, score, health, potion):
		self.state = state
		self.parent = par
		self.action = act
		self.dir = dir
		self.score = score
		self.health = health
		self.potion = potion

	def __lt__(self, other):
		if self.score != other.score: return self.score > other.score
		if self.health != other.health: return self.health > other.health
		return self.potion > other.potion