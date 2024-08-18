# agent.py
# =============================================================================
#  Description to be updated.
# =============================================================================

import itertools
import random
from queue import PriorityQueue

from . import Knowledge
from . import Node

class Agent:
# Constructor
	def __init__(self):
		self.size = 10
		self.KB = Knowledge(self.size)

		self.position = (1, 1)
		self.direction = 0
		self.score = 0
		self.health = 100
		self.has_potion = False

		self.history = []
		self.visited = set({(1, 1)})

# Private
	def __update(self, properties):
		all_properties = ['B', 'S', 'W_H', 'G_L', 'P', 'W', 'P_G', 'H_P', 'G']

		# Clear previous percepts
		for property in all_properties:
			self.KB.remove(property, *self.position, True)
			self.KB.remove(property, *self.position, False)

		# Add new percepts
		for property in all_properties:
			self.KB.add(property, *self.position, property in properties)

		# Update agent stats
		for property in properties:
			if property == 'P_G': self.health = max(0, self.health - 25)
			if property == 'P':
				self.health = 0
				self.score -= 10000
			if property == 'W':
				self.health = 0
				self.score -= 10000
			if property == 'G':
				self.score += 5000

	def __safe(self, x, y):
		return not(self.KB.possible('W', x, y) or self.KB.possible('P', x, y) or self.KB.possible('P_G', x, y))

	def __search(self):
		goal = [pos for pos in itertools.product(range(1, self.size + 1), repeat = 2) if self.__safe(*pos) and pos not in self.visited]
		if len(goal) == 0: goal = [(0, 0)]
		
		visited = set()
		predecessor = dict()
		frontier = PriorityQueue()

		frontier.put(Node(
			(self.position, self.direction, self.health, self.has_potion),
			None,
			None,
			self.direction,
			self.score,
			self.health,
			self.has_potion
		))

		while not frontier.empty():
			node = frontier.get()
			state, par, act, dir, score, health, potion = node.state, node.parent, node.action, node.dir, node.score, node.health, node.potion

			if state in visited: continue
			if health <= 0: continue
			
			visited.add(state)
			if predecessor.get(state) is None: predecessor[state] = (par, act)

			if state[0] in goal:
				return self.__trace(predecessor, state)
			
			directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
			action_cost = {
				'F': -10,
				'L': -10,
				'R': -10,
				'G': -10,
				'S': -100,
				'C': +10,
				'H': -10,
			}

			for action in action_cost:
				x, y = state[0]
				dx, dy = directions[dir]

				new_dir = dir
				new_score = score
				new_health = health
				new_potion = potion

				if action == 'F':
					x, y = x + dx, y + dy
					if x < 1 or x > self.size or y < 1 or y > self.size: continue
				elif action == 'L':
					new_dir = (dir + 3) % 4
				elif action == 'R':
					new_dir = (dir + 1) % 4
				elif action == 'G':
					if not self.KB.certain('H_P', x, y): continue
					new_potion = True
				elif action == 'C':
					if (x, y) != (10, 1): continue
					x, y = 0, 0
				elif action == 'H':
					if not potion: continue
					new_health = min(100, health + 25)
					new_potion = False

				if self.KB.certain('G', x, y): new_score += 5000
				if self.KB.possible('P_G', x, y): new_health = max(0, health - 25)
				if self.KB.possible('P', x, y) or self.KB.possible('W', x, y):
					new_score -= 10000
					new_health = 0

				new_score += action_cost[action]
				frontier.put(Node(
					((x, y), new_dir, new_health, new_potion),
					state,
					action,
					new_dir,
					new_score,
					new_health,
					new_potion
				))

	def __trace(self, predecessor: dict, end):
		actions = []

		while end != None:
			actions.append(predecessor[end][1])
			end = predecessor[end][0]

		while len(actions) > 0 and actions[-1] is None: actions.pop()
		return actions[-1]
	
	def __take_action(self, action):
		if action == 'F':
			dx, dy = [(0, 1), (1, 0), (0, -1), (-1, 0)][self.direction]
			self.position = (self.position[0] + dx, self.position[1] + dy)
		elif action == 'L':
			self.direction = (self.direction + 3) % 4
		elif action == 'R':
			self.direction = (self.direction + 1) % 4
		elif action == 'G':
			self.has_potion = True
		elif action == 'C':
			self.position = (0, 0)
		elif action == 'H':
			self.health = min(100, self.health + 25)
			self.has_potion = False

		cost = {
			'F': -10,
			'L': -10,
			'R': -10,
			'G': -10,
			'S': -100,
			'C': +10,
			'H': -10,
		}[action]

		self.score += cost
		self.visited.add(self.position)
		self.history.append(action)

# Public
	def move(self, properties):
		self.__update(properties)
		action = self.__search()
		self.__take_action(action)
		return action