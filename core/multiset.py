# multiset.py
# =============================================================================
#  Description to be updated.
# =============================================================================

from collections import Counter

class Multiset:
	def __init__(self, *args):
		self.__data = Counter(args)

	def __str__(self):
		str = '{'
		for item, count in self.__data.items():
			for i in range(count):
				str += f'{item}, '

		if len(str) > 1:
			str = str[:-2]
		
		str += '}'
		return str
	
	def __len__(self):
		return sum(self.__data.values())
	
	def __contains__(self, item):
		return item in self.__data
	
	def __iter__(self):
		return iter(self.__data)
	
	def add(self, item):
		self.__data[item] += 1

	def remove(self, item):
		if item in self.__data:
			self.__data[item] -= 1
			if self.__data[item] == 0:
				del self.__data[item]