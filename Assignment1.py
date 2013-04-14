"""
Evan Simpson
March 26, 2013
Coursera Natural Language Processing
Assignment 1
"""
import re

class Tagger():
	"""
	Wraps data files to build vocabularies and perform PoS tagging.
	"""
	def __init__(self, trainFile, targetFile,outFile):
		self.trainingFile = trainFile
		self.targetFile = targetFile
		self.outFile = outFile
		self.TagCounts = {"I-GENE":{},"O":{}}
		self.gramCounts = {"1-GRAM":{},"2-GRAM":{},"3-GRAM":{}}
		self.tags = ("I-GENE", "O")
		self.words = set()

	def processTrain(self):
		"""
		Process the input file and build a vocabulary.
		"""
		with open(self.trainingFile, 'r') as z:
			for line in z:
				lst = line.split()
				if lst[1] == "WORDTAG":
					count, style, tag, word = lst
					if int(count) < 5:
						word = classifyRare(word)
						self.TagCounts[tag][word] = self.TagCounts[tag].get(word, 0) + float(count)
					else:
						self.TagCounts[tag][word] = float(count)
						self.words.add(word)
				else:
					count = lst[0]
					style = lst[1]
					seq = tuple(lst[2:])
					self.gramCounts[style][seq] = float(count)

	def outputUniFile(self):
		"""
		Write output of unigram tagger to output file.
		"""
		with open(self.targetFile, 'r') as inp, open(self.outFile, 'w') as out:
			for line in inp:
				if line != "\n":
					scores = self.getHighScores(line)
					out.write(line.strip()+" "+scores[1][1]+"\n")
				else:
					out.write("\n")

	def outputTriFile(self):
		"""
		Write output of trigram tagger to output file.
		"""
		sentences = self.getSentences()
		count = 0
		with open(self.outFile, 'w') as out:
			for sentence in sentences:
				v = Viterbi(self.TagCounts, self.gramCounts, self.tags, self.words, sentence)
				tag_seq = v.main()
				for word, tag in zip(sentence, tag_seq):
					out.write(word + " " + tag + "\n")
				out.write("\n")


	def getSentences(self):
		"""
		Parse sentences from input file.
		"""
		sentences = []
		with open(self.targetFile, 'r') as inp:
			sentence = []
			for line in inp:
				if line != "\n":
					sentence.append(line.strip())
				else:
					sentences.append(sentence)
					sentence = []
		return sentences

	def getHighScores(self, line):
		"""
		Find most liekly tag for word using a unigram model.
		"""
		scores = []
		for tag in self.tags:
			word = line.strip()
			if word not in self.words:
				word ="_RARE_"
			scores.append((self.e(word,tag),tag))
		scores.sort()
		return scores

	def e(self,x,y):
		"""
		Compute emission parameters.
		"""
		if x not in self.words:
				x =classifyRare(x)
		e = self.TagCounts[y].get(x, 0) / self.gramCounts["1-GRAM"][tuple([y])]
		return e




class Viterbi():
	"""
	Class holds state of Viterbi algorithm parameters for one sentence.
	Used for PoS tagging of a sentence (list of words).
	"""
	def __init__(self, tagMap, gramMap, tagSet, wordSet, sentence):
		self.sentence = sentence
		self.tagMap = tagMap
		self.gramMap = gramMap
		self.bpMap = {}
		self.kappa = {-1:"*", 0:"*"}
		self.n = len(sentence)
		self.tags = {}
		self.words = wordSet
		for i in range(self.n):
			self.kappa[i+1] = tagSet

	def e(self, x, y):
		"""
		Calculate emission paramter of x,y.
		"""
		if x not in self.words:
			x = classifyRare(x)
		e = self.tagMap[y].get(x, 0) / self.gramMap["1-GRAM"][tuple([y])]
		return e

	def q(self, u, v, s):
		"""
		Calculate maximum likelihood estimate of s given u,v.
		"""
		tri_seq = tuple([u, v, s])
		bi_seq = tuple([u, v])
		q = self.gramMap["3-GRAM"][tri_seq] / self.gramMap["2-GRAM"][bi_seq]
		return q

	def pi(self, k, u, v, depth):
		"""
		Recursive function for determining probability of given tag sequence.
		Uses a trigram model.
		"""
		blah = self.bpMap.get(tuple([k, u, v]), 0)
		if blah != 0:
			return blah[0]
		if k == 0:
			return 1
		scores = []
		for w in self.kappa[k-2]:
			piScore = self.pi(k-1, w, u, depth+1)
			score = piScore * self.q(w, u, v) * self.e(self.sentence[k-1], v)
			scores.append((score, w))
		scores.sort()
		self.bpMap[tuple([k, u, v])] = scores[-1]
		return scores[-1][0]

	def main(self):
		"""
		Entry piont for recursive algorithm.
		"""
		scores = []
		for u in self.kappa[self.n-1]:
			for v in self.kappa[self.n]:
				score = self.pi(self.n, u, v, 0) * self.q(u, v, "STOP")
				scores.append((score, (u,v)))
		scores.sort()
		self.tags[self.n-1] = scores[-1][1][0]
		self.tags[self.n] = scores[-1][1][1]
		for k in reversed(range(1, self.n-1)):
			self.tags[k] = self.bpMap[(k+2, self.tags[k+1], self.tags[k+2])][1]
		return self.generateTags()

	def generateTags(self):
		"""
		Use backpointer tags to construct ordered list of PoS tags matching 
		corresponding words in sentence.
		"""
		keys = self.tags.keys()
		keys.sort()
		tags = []
		for key in keys:
			tags.append(self.tags[key])
		return tags


def classifyRare(strng):
	"""
	Use regex matches to classify different types of rare words.
	"""
	if re.search(r'\A\d+\Z', strng):
		return "_NUMERIC_"
	if re.search(r'\d', strng):
		return "_ALPHANUM_"
	elif re.search(r'\A[A-Z]*\Z',strng):
		return "_ALLCAPS_"
	elif re.search(r'.*[A-Z]\Z', strng):
		return "_LASTCAP_"
	else:
		return "_RARE_"



if __name__ == "__main__":
	Tagger = Tagger("test.t", "gene.test", "gene_test.p3.out")
	Tagger.processTrain()
	Tagger.outputTriFile()