import recordings as recordings
import numpy as np
import operator

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

def proximity(i,events,ritardFactor = 1.25):
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


def proximityMaxima(events):
	proximityValues = []

	for i in range (0,len(events)):
	    proximityValues.append(proximity(i,events))

	from scipy.signal import argrelmax

	proximityArray = np.asarray(proximityValues)
	proximityMaxima = argrelmax(proximityArray, order=2)

	return proximityMaxima