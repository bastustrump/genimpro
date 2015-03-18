import recordings as recordings
import numpy as np
import operator
import math

from scipy.ndimage.interpolation import zoom

def similarityVector(event,resolution=5.0,tellfeatures=0):
    sV = np.array([])
    for feature in event["features"]:
        if (type(event["features"][feature])==type(dict())):# & (feature<>"Pitch"):
            zoomFactor = 1/(len(event["features"][feature]["raw"])/resolution)            
            sV = np.append(sV,zoom(event["features"][feature]["raw"],zoomFactor))
            if tellfeatures: print feature
    #for feature in event["features"]:
    #    if type(event["features"][feature])<>type(dict()):
    #        for i in range (0,int(resolution)):
    #            sV = np.append(sV,event["features"][feature])
    #        if tellfeatures: print feature
    return sV

def proximity(i,events,ritardFactor = 1.2):
	if (i==0) | (i >= len(events)):
		return 0
	proximity =  float(events[i]["end"] - events[i]["start"]) / (events[i-1]["end"] - events[i-1]["start"]) * ritardFactor
	return proximity

def similarityMatrix(i,events, norm=1):
    similarityVectors = []
    for n in range(0,(len(events))):
        similarityVectors.append(similarityVector(events[n]))
    
    similarityVectorsArray = np.asanyarray(similarityVectors)
    distances = np.sqrt((((similarityVectorsArray - similarityVectorsArray[i,:]))**2).sum(axis=1))
    if norm:
        distances = distances/np.amax(distances)
    sorted_distances_indices = np.argsort(distances)
    return (sorted_distances_indices,distances)

def similarity(i,events):
    if (i==len(events)-1):
        return 1
    (sorted_distances_indices,distances) = similarityMatrix(i,events)
    return 1-distances[i+1]


def proximityMaxima(events,order=2):
	proximityValues = []

	for i in range (0,len(events)):
	    proximityValues.append(proximity(i,events))

	from scipy.signal import argrelmax

	proximityArray = np.asarray(proximityValues)
	proximityMaxima = argrelmax(proximityArray, order=order)

	return proximityMaxima

from scipy.stats.stats import pearsonr

def continuity(sequence,sonicevents,showNumbers=0,t=0.9):
    if len(sequence)<3:
        return 0
    
    effectiveCorrelations = []
    
    for feature in sonicevents[sequence[0]]["features"]:
        x = range(0,len(sequence))
        if (type(sonicevents[sequence[0]]["features"][feature])==type(dict())):
            values = [sonicevents[sequence[i]]["features"][feature]["mean"] for i in x]
        else:
            values = [sonicevents[sequence[i]]["features"][feature] for i in x]

        logcorrelation = pearsonr(x,np.log(values))[0]
        correlation = pearsonr(x,values)[0]
        if showNumbers:
            print feature
            print correlation
            print logcorrelation
        
        if abs(logcorrelation) > t:
            effectiveCorrelations.append(abs(logcorrelation))
    
    if showNumbers:
        print effectiveCorrelations
        print "--- continuity ---"
        print sum(effectiveCorrelations)/len(effectiveCorrelations)

    if len(effectiveCorrelations) > 0:
    	return sum(effectiveCorrelations)/len(effectiveCorrelations)
    else:
    	return 0

from operator import itemgetter
from itertools import *

def groupEventsByContinuity(events,maxGroupsize=7,t=4):

    continuityMatrix = []
    
    for i in range(0,len(events)):
        eventContinuityMatrix = []
        
        for n in range (1,maxGroupsize):
            sequenceHypothesis = range(i,i+n)
            if (i+n)<len(events):
                eventContinuityMatrix.append(continuity(sequenceHypothesis,events))
        
        if len(eventContinuityMatrix)>2:
            groupSize = eventContinuityMatrix.index(max(eventContinuityMatrix)) + 1
        
        if groupSize>t:
            continuityMatrix.append(range(i,i+groupSize))
 
    flattened = [val for sublist in continuityMatrix for val in sublist]
    
    set = {}
    map(set.__setitem__, flattened, [])
    
    sortedListed = sorted(set.keys())
    sequences=[]

    for k, g in groupby(enumerate(sortedListed), lambda (i,x):i-x):
        sequences.append(map(itemgetter(1), g))
    
    return sequences

def groupEventsByProximity(events):

    eventsProximityMaxima = proximityMaxima(events)

    sequences = []
    sequenceHypothesis = []
    
    for n in range(len(events)-1):
        sequenceHypothesis.append(n)

        if (n in eventsProximityMaxima[0]):

            sequences.append(sequenceHypothesis)
            sequenceHypothesis = []

    return sequences

def groupEventsBySimilarity(events,t=0.9):

    sequences = []
    sequenceHypothesis = []
    
    for n in range(len(events)-1):
        sequenceHypothesis.append(n)

        if (similarity(n,events)<t):

            sequences.append(sequenceHypothesis)
            sequenceHypothesis = []

    return sequences

def combineGroups(sequences,events):
    groupBeginnings = {}
    groupEndings = {}
    
    for sequenceMode in sequences:
        groupBeginnings[sequenceMode] = [sequences[sequenceMode][i][0] for i in range(0,len(sequences[sequenceMode]))]
        groupEndings[sequenceMode] = [sequences[sequenceMode][i][-1] for i in range(0,len(sequences[sequenceMode]))]
        
    sequences = []
    sequenceHypothesis = []
    
    for i in range(0,len(events)):
        sequenceHypothesis.append(i)
        
        beginningsCount = 0
        for sequenceMode in groupBeginnings:
            if i in groupBeginnings[sequenceMode]:
                beginningsCount += 1

        endingsCount = 0
        for sequenceMode in groupBeginnings:
            if i in groupEndings[sequenceMode]:
                endingsCount += 1   
        
        if ((endingsCount>1) & (len(sequenceHypothesis)>1)) | (endingsCount>2):
            sequences.append(sequenceHypothesis)
            sequenceHypothesis = []
    
    return sequences

def sequencesForSonicevents(events):
	sequences = {}
	sequences["proximity"] = groupEventsByProximity(events)
	sequences["similarity"] = groupEventsBySimilarity(events,t=0.9) 
	sequences["continuity"] = groupEventsByContinuity(events,t=4) 

	return combineGroups(sequences,events)