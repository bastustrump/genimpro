import recordings as recordings
import numpy as np
import operator

newSequenceThreshold = 0.6

durationFactor = 1.25

def soniceventHash(features):

	#hex_string = []
	#hex_string.append(int(sonicevent[4]*100))
	#hex_string.append("%f5.0" % sonicevent[5]*100)

	return "%08d%08d" % (features["effZCR"]*100,features["effLoudness"]*100) #''.join(hex_string)

def hamming_distance(s1, s2):
    #"""Return the Hamming distance between equal-length sequences"""
    if len(s1) != len(s2):
        raise ValueError("Undefined for sequences of unequal length")
    return sum(ch1 != ch2 for ch1, ch2 in zip(s1, s2))

def getSequencesForSonicevents(sonicevents):

	sequences = []
	
	sequenceCount = 0
	sequenceEventsCount = 0
	sequenceHypothesis = []
	test=0

	maxDurationRatio = 1.0

	for n in range(len(sonicevents)):
		(eventindex,eventindexEnd,features) = map(sonicevents[n].get, ('start', 'end','features'))
		#sonicevent_hash = soniceventHash(feature)

		if (n<len(sonicevents)-1):
			(eventindexN,eventindexEndN,featuresN) = map(sonicevents[n+1].get, ('start', 'end','features'))
			#sonicevent_hashN = soniceventHash(featureN)

		#check for new sequence
		
		duration = eventindexEnd-eventindex
		durationN = eventindexEndN-eventindexN
		
		#proximity
		durationRatio = duration / (durationFactor * durationN)
		proximityEndProbability = durationRatio / 10.0


		#similarity

		
		similarityEndProbability = (abs(features["effLoudness"]-featuresN["effLoudness"]) + abs(features["effZCR"]-featuresN["effZCR"])) / 5.0
		
		#= hamming_distance(sonicevent_hash,sonicevent_hashN) / 7.0
		
		sequenceEndProbability = proximityEndProbability #(proximityEndProbability * 3.0 + similarityEndProbability + 1.0) / 5.0
		print sequenceEndProbability
		
		sequenceHypothesis.append(n)
			
		if (sequenceEndProbability>=newSequenceThreshold):
			sequenceCount += 1
			
			sequences.append(sequenceHypothesis)

			sequenceHypothesis = []
			
			

	return sequences