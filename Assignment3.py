"""
Evan Simpson
April 30, 2013
Coursera Natural Language Processing
Assignment 3
"""

from collections import defaultdict
import json

class FileIterator:

	def __init__ (self, enFile, esFile):
		self.en = open(enFile, 'r')
		self.es = open(esFile, 'r')

	def __iter__(self):
		return self

	def next(self):
		currentEn = self.en.readline();
		currentEs = self.es.readline();
		if currentEs == '' or currentEn == '':
			self.en.seek(0)
			self.es.seek(0)
			raise StopIteration
		else:
			return [currentEn.split(), currentEs.split()]

	def reset(self):
		self.en.seek(0)
		self.es.seek(0)

class Translator:

	def __init__(self, teFile, tfFile, eFile, fFile, outFile, paramFile=""):
		self.eFile = eFile
		self.fFile = fFile
		self.outFile = outFile
		self.paramFile = paramFile
		self.alignments = []
		self.parameters = self.importParams()
		self.algorithm = IBM1(FileIterator(teFile, tfFile), FileIterator(eFile, fFile), 5, self.parameters)
		
	def importParams(self):
		print self.paramFile
		if self.paramFile == "":
			return defaultdict(int)
		else:
			params = defaultdict(int)
			with open(self.paramFile, 'r') as z:
				for line in z:
					data = json.loads(line)
					params.update({tuple(data[0]): data[1]})
			return params

	def countParameters(self):
		self.algorithm.paramEstimator()

	def translate(self):
		self.alignments = self.algorithm.translate()

	def writeAlignment(self):
		with open(self.outFile, 'w') as z:
			for alignment in self.alignments:
				z.write("%d %d %d" %(alignment[0],alignment[1],alignment[2])+'\n')

class keydefaultdict(defaultdict):
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError( key )
        else:
            ret = self[key] = self.default_factory(key)
            return ret

class IBM1:

	def __init__(self, tIterator, oIterator, iters, parameters):
		self.trainIterator = tIterator
		self.transIterator = oIterator
		self.iterations = iters
		self.ewords = defaultdict(set)
		self.export = False
		if parameters != {}:
			self.parameters = parameters
		else:
			self.export = True
			print "Initializing parameters..."
			self.parameters = self.initializeParameters()
			print "Done initializing parameters."
		self.alignments = []

	def initializeParameters(self):
		parameters = keydefaultdict(lambda e: 1.0/len(self.ewords[e[0]]))
		for pair in self.trainIterator:
			for i in pair[1]:
				for j in pair[0] + ["NULL"]:
					self.ewords[j].add(i)
		return parameters

	def sigma(self, i, j, eSentence, fSentence):
		num = self.parameters[(eSentence[j], fSentence[i])]
		denom = 0.0
		for l in [0] + range(j, len(eSentence)):
			denom += self.parameters[(eSentence[l], fSentence[i])]
		return num/denom

	def paramEstimator(self):
		print "Estimating parameters..."
		for c in range(self.iterations):
			print "Iteration " + str(c)
			counts = defaultdict(int)
			for pair in self.trainIterator:
				eSentence = ["NULL"] + pair[0]
				fSentence = pair[1]
				for i in range(len(fSentence)):
					for j in range(len(eSentence)):	
						s = self.sigma(i,j,eSentence,fSentence)
						counts[(eSentence[j], fSentence[i])] += s
						counts[(eSentence[j], "TOTAL_COUNTS")] += s
			self.trainIterator.reset()
			for pair in counts.keys():
				if pair[1] != "TOTAL_COUNTS":
					self.parameters[pair] = counts[pair]/(counts[(pair[0], "TOTAL_COUNTS")]*1.0)
		print "Done estimating parameters."

	def exportParameters(self):
		print "Writing parameters to file..."
		with open("parameters2.txt", 'w') as z:
			for param in self.parameters.items():
				z.write(json.dumps(param) + '\n')
		print "Done writing parameters to file."

	def translate(self):
		print "Beginning translation..."
		if self.export:
			self.exportParameters()
		count = 1
		for pair in self.transIterator:
			eSentence = ["NULL"] + pair[0]
			fSentence = pair[1]
			for i in range(len(fSentence)):
				maxA = (0, None)
				for j in range(len(eSentence)):
					if self.parameters[(eSentence[j], fSentence[i])] > maxA[0]:
						maxA = (self.parameters[(eSentence[j], fSentence[i])],j)
				if maxA[1] != None and maxA[1] != 0:
					self.alignments.append([count, maxA[1], i+1])
			count += 1
		self.alignments.sort()
		return self.alignments




if __name__ == '__main__':
	#trans = Translator('corpus.en', 'corpus.es', 'test.en', 'test.es', 'alignment test.p1.out', 'parameters.txt')
	trans = Translator('corpus.en', 'corpus.es', 'dev.en', 'dev.es', 'dev.out')#, 'parameters2.txt')
	trans.countParameters()
	trans.translate()
	trans.writeAlignment()