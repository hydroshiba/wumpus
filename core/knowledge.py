# knowledge.py
# =============================================================================
#  Description to be updated.
# =============================================================================

import itertools
import time
import copy

from pysat.formula import CNF
from pysat.solvers import Glucose3

class Knowledge:
# Constructor
	def __init__(self, size):
		self.size = size
		self.percept = {
			'P': 'B',
			'W': 'S',
			'P_G': 'W_H',
			'H_P': 'G_L'
		}
		
		self.__map = dict()
		self.__cache = dict()
		self.__clauses = set()
		self.__solver = Glucose3()
		
# Private
	def __adjacent(self, x, y):
		cells = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
		return [(i, j) for i, j in cells if 1 <= i <= self.size and 1 <= j <= self.size]

	def __symbol(self, name, x, y):
		key = (name, x, y)
		if key not in self.__map:
			self.__map[key] = len(self.__map) + 1
		return self.__map[key]
	
	def __set_rules(self):
		cnf = CNF()

		# Define starting position
		cnf.append([-self.__symbol('P', 1, 1)]) # No pit in (1, 1)
		cnf.append([-self.__symbol('W', 1, 1)]) # No wumpus in (1, 1)
		cnf.append([-self.__symbol('G', 1, 1)]) # No gold in (1, 1)
		cnf.append([-self.__symbol('P_G', 1, 1)]) # No poisonous gas in (1, 1)
		cnf.append([-self.__symbol('H_P', 1, 1)]) # No health potion in (1, 1)

		# Define rules for breeze, stench, whiff, and glow
		for x, y in itertools.product(range(1, self.size + 1), repeat=2):
			stench = self.__symbol('S', x, y)
			breeze = self.__symbol('B', x, y)
			whiff = self.__symbol('W_H', x, y)
			glow = self.__symbol('G_L', x, y)

			adjacent_cells = self.__adjacent(x, y)

			# The percept doesn't exit or one of the adjacent cells must have the property
			cnf.append([-stench] + [self.__symbol('W', i, j) for i, j in adjacent_cells])
			cnf.append([-breeze] + [self.__symbol('P', i, j) for i, j in adjacent_cells])
			cnf.append([-whiff] + [self.__symbol('P_G', i, j) for i, j in adjacent_cells])
			cnf.append([-glow] + [self.__symbol('H_P', i, j) for i, j in adjacent_cells])

			# If the percept doesn't exist, then none of the adjacent cells have the property
			for i, j in adjacent_cells:
				cnf.append([stench, -self.__symbol('W', i, j)])
				cnf.append([breeze, -self.__symbol('P', i, j)])
				cnf.append([whiff, -self.__symbol('P_G', i, j)])
				cnf.append([glow, -self.__symbol('H_P', i, j)])

		return cnf
	
	def __reset_solver(self):
		self.__solver = Glucose3(self.__set_rules())
		self.__cache.clear()
		for clause in self.__clauses:
			self.__solver.add_clause([clause])
	
	def __query(self, clause):
		if clause in self.__cache: return self.__cache[clause]
		self.__cache[clause] = not self.__solver.solve(assumptions = [-clause])
		return self.__cache[clause]
	
# Public
	def add(self, property, x, y, existence = True):
		clause = self.__symbol(property, x, y) * (1 if existence else -1)
		if clause not in self.__clauses: self.__clauses.add(clause)
		self.__reset_solver()

	def remove(self, property, x, y, existence = True):
		clause = self.__symbol(property, x, y) * (1 if existence else -1)
		if clause in self.__clauses: self.__clauses.remove(clause)
		self.__reset_solver()

	def has(self, property, x, y, existence = True):
		clause = self.__symbol(property, x, y) * (1 if existence else -1)
		return clause in self.__clauses

	# Tin chuan chua anh?

	def certain(self, property, x, y):
		return self.__query(self.__symbol(property, x, y))

	def impossible(self, property, x, y):
		return self.__query(-self.__symbol(property, x, y))
	
	def possible(self, property, x, y):
		if self.impossible(property, x, y):
			return False
		
		adjacent_cells = self.__adjacent(x, y)
		for i, j in adjacent_cells:
			if self.certain(self.percept[property], i, j):
				return True
			
		return False