"""
Evan Simpson
April 30, 2013
Coursera Natural Language Processing
Assignment 3
"""

from collections import defaultdict
import json
import codecs

class FileIterator:
	'''
	Used for iterating over a pair of files together, one line at a time.
	Implements pythons iterator interface.
	'''
	def __init__ (self, enFile, esFile):
		self.en = codecs.open(enFile, 'r', encoding='utf-8')
		self.es = codecs.open(esFile, 'r', encoding='utf-8')

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

	'''
	Contains training files, files to be analyzed, output file, 
	 the translation model to be used, and precomputed parameters.
	'''
	def __init__(self, teFile, tfFile, eFile, fFile, outFile, model, paramFile=""):
		self.eFile = eFile
		self.fFile = fFile
		self.outFile = outFile
		self.paramFile = paramFile
		self.alignments = []
		self.parameters = self.importParams()
		if model == 1:
			self.algorithm = IBM1(FileIterator(teFile, tfFile), FileIterator(eFile, fFile), 5, self.parameters)
		else:
			self.algorithm = IBM2(FileIterator(teFile, tfFile), FileIterator(eFile, fFile), 5, self.parameters)
		
	'''
	If parameters are supplied, import them. Saves lots of time.
	'''	
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

	'''
	Use the chosen model to estimate q and or t parameters.
	'''
	def countParameters(self):
		self.algorithm.paramEstimator()

	'''
	Use the chosen model to translate the test files. Get alignments in return.
	'''
	def translate(self):
		self.alignments = self.algorithm.translate()

	'''
	Write the alignments to the output file in the required format.
	'''
	def writeAlignment(self):
		with open(self.outFile, 'w') as z:
			for alignment in self.alignments:
				z.write("%d %d %d" %(alignment[0],alignment[1],alignment[2])+'\n')




class keydefaultdict(defaultdict):
	'''
	Custom defaultdict that passes key into default function.
	'''
    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError( key )
        else:
            ret = self[key] = self.default_factory(key)
            return ret




class IBM1:
	'''
	Contains iterator over training and test files, number of iterations for estimation, and parameters.
	'''
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

	'''
	Set the initial value of all t parameters.
	'''
	def initializeParameters(self):
		parameters = keydefaultdict(lambda e: 1.0/len(self.ewords[e[0]]))
		for pair in self.trainIterator:
			for i in pair[1]:
				for j in pair[0] + ["NULL"]:
					self.ewords[j].add(i)
		return parameters

	'''
	Calculate the delta from last iteration.
	'''
	def delta(self, i, j, eSentence, fSentence):
		num = self.parameters[(eSentence[j], fSentence[i])]
		denom = 0.0
		for l in range(len(eSentence)):
			denom += self.parameters[(eSentence[l], fSentence[i])]
		return num/denom

	'''
	Estimate the parameters of the model.
	'''
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
						s = self.delta(i,j,eSentence,fSentence)
						counts[(eSentence[j], fSentence[i])] += s
						counts[(eSentence[j], "TOTAL_COUNTS")] += s
			self.trainIterator.reset()
			for pair in counts.keys():
				if pair[1] != "TOTAL_COUNTS":
					self.parameters[pair] = counts[pair]/(counts[(pair[0], "TOTAL_COUNTS")]*1.0)
		print "Done estimating parameters."

	'''
	Write the parameters to a file for use later.
	'''
	def exportParameters(self):
		print "Writing parameters to file..."
		with open("parameters.txt", 'w') as z:
			for param in self.parameters.items():
				z.write(json.dumps(param) + '\n')
		print "Done writing parameters to file."

	'''
	Find the alignments between the test files.
	'''
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


class IBM2:
	'''
	Contains iterator over training and test files, number of iterations for estimation, and parameters.
	'''
	def __init__(self, tIterator, oIterator, iters, parameters):
		self.trainIterator = tIterator
		self.transIterator = oIterator
		self.iterations = iters
		self.ewords = defaultdict(set)
		self.export = False
		self.q = keydefaultdict(lambda q: 1.0/(q[2]+1))
		if parameters != {}:
			print "Imported parameters."
			self.parameters = parameters
		else:
			self.export = True
			print "Initializing parameters..."
			self.parameters = self.initializeParameters()
			print "Done initializing parameters."
		self.alignments = []

	'''
	Set the initial value of all t parameters.
	'''
	def initializeParameters(self):
		parameters = keydefaultdict(lambda e: 1.0/len(self.ewords[e[0]]))
		for pair in self.trainIterator:
			for i in pair[1]:
				for j in pair[0] + ["NULL"]:
					self.ewords[j].add(i)
		return parameters

	'''
	Calculate the delta from last iteration.
	'''
	def delta(self, i, j, eSentence, fSentence):
		num = self.parameters[(eSentence[j], fSentence[i])] * self.q[(j, i, len(eSentence), len(fSentence))]
		denom = 0.0
		for l in range(len(eSentence)):
			denom += (self.parameters[(eSentence[l], fSentence[i])] * self.q[(l, i, len(eSentence), len(fSentence))])
		return num/denom

	'''
	Estimate the parameters of the model.
	'''
	def paramEstimator(self):
		print "Estimating parameters..."
		for c in range(self.iterations):
			print "Iteration " + str(c)
			counts = defaultdict(int)
			qCounts = defaultdict(int)
			tCounts = defaultdict(int)
			for pair in self.trainIterator:
				eSentence = ["NULL"] + pair[0]
				fSentence = pair[1]
				for i in range(len(fSentence)):
					for j in range(len(eSentence)):	
						s = self.delta(i,j,eSentence,fSentence)
						counts[(eSentence[j], fSentence[i])] += s
						counts[(eSentence[j], "TOTAL_COUNTS")] += s
						qCounts[(j,i,len(eSentence), len(fSentence))] += s
						tCounts[(i,len(eSentence), len(fSentence))] += s
			for pair in counts.keys():
				if pair[1] != "TOTAL_COUNTS":
					self.parameters[pair] = counts[pair]/(counts[(pair[0], "TOTAL_COUNTS")]*1.0)
			for q in qCounts.keys():
				self.q[q] = qCounts[q]/(tCounts[q[1:]]*1.0)

		print "Done estimating parameters."
		if self.export:
			self.exportParameters()

	'''
	Write the parameters to a file for use later.
	'''
	def exportParameters(self):
		print "Writing parameters to file..."
		with open("parameters2.txt", 'w') as z:
			for param in self.parameters.items():
				z.write(json.dumps(param) + '\n')
			z.write("*** BEGIN Q ***\n")
			for q in self.q.items():
				z.write(json.dumps(q) + '\n')
		print "Done writing parameters to file."

	'''
	Find the alignments between the test files.
	'''
	def translate(self):
		print "Beginning translation..."
		count = 1
		for pair in self.transIterator:
			eSentence = ["NULL"] + pair[0]
			fSentence = pair[1]
			for i in range(len(fSentence)):
				maxA = (0, None)
				for j in range(len(eSentence)):
					if (self.parameters[(eSentence[j], fSentence[i])] * self.q[(j, i, len(eSentence), len(fSentence))] ) > maxA[0]:
						maxA = ((self.parameters[(eSentence[j], fSentence[i])] * self.q[(j, i, len(eSentence), len(fSentence))]),j)
				if maxA[1] != None and maxA[1] != 0:
					self.alignments.append([count, maxA[1], i+1])
			count += 1
		return self.alignments



if __name__ == '__main__':
	#trans = Translator('corpus.en', 'corpus.es', 'test.en', 'test.es', 'alignment_test.p1.out', 1)
	trans = Translator('corpus.en', 'corpus.es', 'test.en', 'test.es', 'alignment_test.p2.out', 2, 'parameters.txt')
	trans.countParameters()
	trans.translate()
	trans.writeAlignment()