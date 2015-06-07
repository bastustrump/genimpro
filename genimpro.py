import sys
import sonicevents as se
import grouping as grouping
import recordings as recordings
import numpy as np
import matplotlib.pyplot as plt
import os
from essentia.standard import *

onsets1=[]
onsets2=[]

samplerate=48000.0
tuningFrequency = 440


getVar = lambda searchList, ind: [searchList[i] for i in ind]


def soniceventsForTrack(track):

	audiofile = track[2]
	onsets = se.getOnsetsForTrack(track)
	audio = recordings.getAudioForTrack(track)
	sonicevents = se.soniceventsForOnsets(onsets,audio)
	sonicevents = se.featuresForSonicevents(sonicevents,audio)

	return sonicevents


def analyseTrack(track,updateAll=0):
    
    audio = recordings.getAudioForTrack(track)
    sonicevents = recordings.getSoniceventsForTrack(track)
    sequences = recordings.getSequencesForTrack(track)
    phenotypes = recordings.getPhenotypesForTrack(track)
    genotypes = recordings.getGenotypesForTrack(track)
    
    if (sonicevents==None) | updateAll:
        sonicevents = soniceventsForTrack(track)
        recordings.updateSoniceventsForTrack(track,sonicevents)
        
        sequences = grouping.sequencesForSonicevents(sonicevents)
        recordings.updateSequencesForTrack(track,sequences,sonicevents)
        
        phenotypes = phenotypesForSequences(sequences,sonicevents,audio)
        recordings.updatePhenotypesForTrack(track,sequences,phenotypes)

        genotypes = genotypesForSequences(sequences)
        recordings.updateGenotypesForTrack(track,sequences,genotypes)

        return
        
    if (sequences==None) | updateAll:
        sequences = grouping.sequencesForSonicevents(sonicevents)
        recordings.updateSequencesForTrack(track,sequences,sonicevents)
    
        phenotypes = phenotypesForSequences(sequences,sonicevents,audio)
        recordings.updatePhenotypesForTrack(track,sequences,phenotypes)

        genotypes = genotypesForSequences(sequences)
        recordings.updateGenotypesForTrack(track,sequences,genotypes)
        
        return
        
    if (phenotypes==None) | updateAll:
        phenotypes = phenotypesForSequences(sequences,sonicevents,audio)
        recordings.updatePhenotypesForTrack(track,sequences,phenotypes)   

        genotypes = genotypesForSequences(phenotypes)
        recordings.updateGenotypesForTrack(track,sequences,genotypes)


    if (genotypes==None) | updateAll: 

        genotypes = genotypesForSequences(phenotypes)
        recordings.updateGenotypesForTrack(track,sequences,genotypes)        
        
        return


def eventPlot(event,filename):
	plt.figure()
	t = np.linspace(0, len(event["audio"])/samplerate, num=len(event["audio"]))
	
	#t2 = np.linspace(0, len(se[0]["audio"])/48000.0, num=len(se[0]["features"]["ZCR"]["raw"]))
	
	plt.plot(t,event["audio"],linewidth=0.5)
	#plt.show()
	plt.savefig(filename,dpi=600)
	
def plot(events):	
	
	fig, ax = plt.subplots()
	
	durations = [(events[i]["end"] - events[i]["start"])/float(samplerate) for i in range(len(events))]
	ax.bar(range(len(events)),durations)

	#[(events[i]["end"] for i in range(len(events))]
	#ax.hist(durations, 20, normed=0, histtype='stepfilled', facecolor='g', alpha=0.75)
	plt.show()



def analyseRecording(recordingID):
	
	recordingDetails = recordings.getRecordingDetails(recordingID)
	print "ID %i: %s on %s:" % (recordingDetails[0],recordingDetails[1],recordingDetails[2])
	
	for track in recordingDetails[4]:
		analyseTrack(track)	
			


def phenotypeForSequence(sequence,sonicevents,audio):
    
    events = sonicevents[sequence[0]:sequence[-1]]
    
    sequenceAudio = audio[events[0]["start"]:events[-1]["end"]]
    
    sequenceFeatures = {}
    sequenceFeatures["duration"] = []
    for feature in events[0]["features"]:
        sequenceFeatures[feature] = []
    
    
    for event in events:
        sequenceFeatures["duration"].append((event["end"]-event["start"])/samplerate)
        for feature in event["features"]:
            if (type(event["features"][feature])==type(dict())):
                value = event["features"][feature]["mean"]
            else:
                value = event["features"][feature]
                
            sequenceFeatures[feature].append(value)
    
    attributesList = ["dynamics","rhythmics","melodics","harmonics","timbre"]
    attributes = {}
    
    for attribute in attributesList:
        attributes[attribute] = {}
        
    attributes["dynamics"]["range"] = abs(np.amax(sequenceFeatures["Loudness"])-np.amin(sequenceFeatures["Loudness"]))
    attributes["dynamics"]["median"] = np.median(sequenceFeatures["Loudness"])

        
    microtime = np.amin(sequenceFeatures["duration"])
    hist,bins = np.histogram(sequenceFeatures["duration"]/microtime)
    attributes["rhythmics"]["variance"] = float(len(hist[np.nonzero(hist)])) / len(sequenceFeatures["duration"])
    attributes["rhythmics"]["tempo"] = 60 / ((bins[np.argmax(hist)] + bins[np.argmax(hist)+1]) / 2.0)

    pitches = np.asarray(sequenceFeatures["Pitch"])
    detectedPitches = pitches[np.nonzero(sequenceFeatures["Pitch"])]
    Pitches = (np.log(detectedPitches) - np.log(tuningFrequency)) / np.log(2) * 12 + 69
    if len(Pitches)>0:
    	hist,bins = np.histogram(Pitches)
    	attributes["melodics"]["variance"] = float(len(hist[np.nonzero(hist)])) / len(Pitches)
    	attributes["melodics"]["range"] = abs(np.amax(Pitches)-np.amin(Pitches))
    	attributes["melodics"]["median"] = np.median(Pitches)
    else:
    	attributes["melodics"]["variance"] = np.nan
    	attributes["melodics"]["range"] = np.nan
    	attributes["melodics"]["median"] = np.nan     

    spec = essentia.standard.Spectrum()
    SpectralPeaks = essentia.standard.SpectralPeaks(sampleRate=samplerate)
    HPCP = essentia.standard.HPCP(sampleRate=samplerate)
    Key = essentia.standard.Key()

    spectrum = spec(sequenceAudio)
    peaks = SpectralPeaks(spectrum)
    chroma = HPCP(peaks[0],peaks[1])
    key = Key(chroma)

    from scipy.signal import argrelmax

    chromaMaxima = argrelmax(chroma, order=2)
    attributes["harmonics"]["variance"] = float(len(chromaMaxima)) / len(chroma)

    attributes["timbre"]["roughness"] = np.median(sequenceFeatures["Roughness"])
    attributes["timbre"]["brightness"] = np.median(sequenceFeatures["SpectralCentroid"])

    return attributes


def phenotypesForSequences(sequences,sonicevents,audio):

	phenotypes = []

	for i in range(0,len(sequences)):
		phenotypes.append(phenotypeForSequence(sequences[i],sonicevents,audio))

	return phenotypes


import skfuzzy as fuzz

def convertToVector(phenotypeDict,printArray=0):
    vect = []
    for attribute in phenotypeDict:
        for value in phenotypeDict[attribute]:
            vect.append(phenotypeDict[attribute][value])
            if printArray:
                print attribute + " " + value + ": " + str(phenotypeDict[attribute][value])
    return vect


def genotypeForSequence(phenotype,genome):
    if type(phenotype) is dict:
        phenotype = convertToVector(phenotype)
    phenotype = np.asarray(phenotype)
    where_are_NaNs = np.isnan(phenotype)
    phenotype[where_are_NaNs] = 0
    u_predict, d, _, _, p, fpc = fuzz.cluster.cmeans_predict(np.vstack(phenotype), genome, 2, error=0.005, maxiter=1000)
    return u_predict.flatten()


def genotypesForSequences(phenotypes):

    genotypes = []
    genome = recordings.getGenome()

    for i in range(0,len(phenotypes)):
        genotypes.append(genotypeForSequence(phenotypes[i],genome))

    return genotypes



if __name__ == '__main__':
	
	if len(sys.argv) < 2:
		print "Usage: recording ID"
		recordings.listRecodings()
		sys.exit(1)
	
	recordingID = int(sys.argv[1])
	
	if len(sys.argv) >= 3:
		trackNumber = int(sys.argv[2])
	
	analyseRecording(recordingID,trackNumber)

	
	
	

