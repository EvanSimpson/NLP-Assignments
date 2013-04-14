"""
Evan Simpson
April 14, 2013
Coursera Natural Language Processing
Assignment 2
"""
import re
import json

class FixCount():
	"""
	Class for processing training data and consolidating uncommon words into _RARE_
	"""
	def __init__(self, countfile, trainfile, outfile):
		self.countFile = countfile
		self.trainingFile = trainfile
		self.outFile = outfile
		self.wordCounts = {}
		self.rareWords = set()


	def getCounts(self):
		"""
		Process the count file and count the frequency of words independent of PoS.
		"""
		with open(self.countFile, 'r') as z:
			for line in z:
				lst = line.split()
				if lst[1] == "UNARYRULE":
					self.wordCounts[lst[-1]] = self.wordCounts.get(lst[-1], 0) + int(lst[0])

	def getRares(self):
		"""
		Find all of the rare words and add them to the rare word set.
		"""
		for k,v in self.wordCounts.iteritems():
			if v < 5:
				self.rareWords.add(k)

	def buildNewTrees(self):
		"""
		Read the training file and write new trees to output file.
		"""
		with open(self.trainingFile, 'r') as inp, open(self.outFile, 'w') as out:
			for line in inp:
				newLine = json.dumps(self.recurReplace(json.loads(line)))
				out.write(newLine)
				out.write("\n")


	def recurReplace(self, lst):
		"""
		Recursively replace all rare words in parse tree with _RARE_.
		"""
		if type(lst[-1]) == list:
			lst[1] = self.recurReplace(lst[1])
			lst[2] = self.recurReplace(lst[2])
		else:
			if lst[1] in self.rareWords:
				lst[1] = "_RARE_"
		return lst


class Parser():
	"""
	Used to build a grammar and parse sentences one at a time.
	"""
	def __init__(self, countfile, targetfile, outfile):
		self.countFile = countfile
		self.targetFile = targetfile
		self.outFile = outfile
		self.grammar = PCFG(countfile)

	def outPut(self):
		"""
		Write parse tree output to file.
		"""
		with open(self.targetFile, 'r') as inp, open(self.outFile, 'w') as out:
			for line in inp:
				sentence = line.split()
				tree = CKY(self.grammar, sentence)
				tree.main()
				newLine = json.dumps(tree.tree)
				out.write(newLine)
				out.write("\n")



class PCFG():
	"""
	Contains all state necessary for a Probabilistic Context Free Grammar
	"""
	def __init__(self, countfile):
		self.countFile = countfile
		self.non_terminals = {}
		self.words = {}
		self.start = "SBARQ"
		self.rules = {"UNARYRULE":{},"BINARYRULE":{}}
		self.buildGrammar()

	def buildGrammar(self):
		"""
		read an input file and build a Probabilistic Context Free Grammar.
		"""
		with open(self.countFile, 'r') as z:
			for line in z:
				lst = line.split()
				if lst[1] == "NONTERMINAL":
					self.non_terminals[lst[-1]] = float(lst[0])
				elif lst[1] == "UNARYRULE":
					self.words[lst[-1]] = self.words.get(lst[-1], 0) + float(lst[0])
					d = self.rules[lst[1]].get(lst[2], {})
					d[lst[-1]] = float(lst[0])
					self.rules[lst[1]][lst[2]] = d
				else:
					d = self.rules[lst[1]].get(lst[2], {})
					d[tuple(lst[-2:])] = float(lst[0])
					self.rules[lst[1]][lst[2]] = d


class CKY():
	"""
	Contains all state necessary for CKY algorithm.
	Builds parse tree for single sentence (list of words).
	"""
	def __init__(self, pcfg, sentence):
		self.grammar = pcfg
		self.sentence = sentence
		self.n = len(sentence)
		self.bpMap = {}
		self.tree = []

	def q(self, x, y):
		"""
		Calculate maximum likelihood of rule x -> y where y is either
		unary or binary.
		"""
		if type(y) == tuple:
			return self.grammar.rules["BINARYRULE"][x][y]/self.grammar.non_terminals[x]
		else:
			if y not in self.grammar.words.keys():
				y = "_RARE_"
			if x not in self.grammar.rules["UNARYRULE"].keys():
				return 0
			return self.grammar.rules["UNARYRULE"][x].get(y,0)/self.grammar.non_terminals[x]

	def main(self):
		"""
		Used as entry point for recursive algorithm and recursive tree builder.
		"""
		self.pi(1, self.n, self.grammar.start)
		self.tree = self.recurseBuildTree(1, self.n, self.grammar.start)


	def recurseBuildTree(self, i, j, x):
		"""
		Uses backpointer values to recursively construct a parse tree.
		"""
		if i == j:
			return [x, self.bpMap[tuple([i,j,x])][1][0]]
		else:
			stuff = self.bpMap[tuple([i,j,x])]
			rh = stuff[1][0]
			split = stuff[1][1]
			return [x]+[self.recurseBuildTree(i, split, rh[0]), self.recurseBuildTree(split+1, j, rh[1])]

	def pi(self, i, j, x):
		"""
		Recursive portion of CKY algorithm.
		"""
		high = self.bpMap.get(tuple([i,j,x]), 0)
		if high != 0:
			return high[0]
		if i == j:
			q = self.q(x, self.sentence[i-1])
			self.bpMap[tuple([i,j,x])] = (q, (self.sentence[i-1],i))
			return q
		scores = []
		for rh in self.grammar.rules["BINARYRULE"].get(x, {}).keys():
			for s in range(i, j):
				q = self.q(x, rh)
				if q !=0:
					score =  q * self.pi(i, s, rh[0]) * self.pi(s+1, j, rh[1])
					scores.append((score, (rh,s)))
		if scores == []:
			return 0
		scores.sort()
		self.bpMap[tuple([i,j,x])] = scores[-1]
		return scores[-1][0]


if __name__ == "__main__":
	p = Parser("new_vert.counts", "parse_test.dat", "parse_test.p3.out")
	p.outPut()