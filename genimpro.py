import sys
import sonicevents as se
import grouping as grouping
import recordings as recordings
import numpy as np
#import matplotlib.pyplot as plt
import os
from essentia.standard import *
import json

onsets1=[]
onsets2=[]

#samplerate=48000.0
samplerate=44100.0
tuningFrequency = 440


getVar = lambda searchList, ind: [searchList[i] for i in ind]


def geneticsForVisualisation(recordingID):
    soundcellIDs = []
    startSample =[]
    groups = []
    durations = []
    genotypes = []
    phenotypes = []
    lineageIDs = []
    fitness = []

    recordingDetails = recordings.getRecordingDetails(recordingID)

    for g,track in enumerate(recordingDetails[4]):
        ids,trackGenotypes,start,lineages,fitnessValues = recordings.getGenotypesForTrack(track)
        ids,trackPhenotypes,duration = recordings.getPhenotypesForTrack(track)
        fitness.extend(fitnessValues)
        genotypes.extend(trackGenotypes)
        lineageIDs.extend(lineages)
        phenotypes.extend(trackPhenotypes)
        soundcellIDs.extend(ids)
        startSample.extend(start)
        durations.extend(duration)
        groups.extend([g+1]*len(genotypes))

    genetics = recordings.getGeneticsForRecording(recordingID)

    lin = []
    for i,soundcellID in enumerate(soundcellIDs):
        for l,lineage in enumerate(genetics):
            soundcellsInLineage = [lineage[x][0] for x in range(len(lineage))]
            if soundcellID in soundcellsInLineage:
                lin.append(l)

    nodes = []
    for i,idx in enumerate(soundcellIDs):
        nodes.append({"id":idx,"startTime":startSample[i]/samplerate,"duration":durations[i]/samplerate,"group":groups[i],"lineage":lin[i],"fitness":fitness[i],"genotype":genotypes[i],"phenotype":phenotypes[i],"lineageID":lineageIDs[i]})

    links = []
    for l,lineage in enumerate(genetics):

        for i in range(0,len(lineage)-1):
            links.append({"source":lineage[i][0],"target":lineage[i+1][0],"distance":lineage[i+1][1]} )
            #print ({"source":lineage[i][0],"target":lineage[i+1][0],"distance":lineage[i+1][1]} )

        if lineage[0][1] != 0:
            links.append({"source":lineage[0][1][0],"target":lineage[0][0],"distance":lineage[0][1][1]*2.0,"descendant":True})

    return {"nodes":nodes,"links":links}




def soniceventsForTrack(track):

	audiofile = track[2]
	onsets = se.getOnsetsForTrack(track)
	audio = recordings.getAudioForTrack(track)
	sonicevents = se.soniceventsForOnsets(onsets,audio)
	sonicevents = se.featuresForSonicevents(sonicevents,audio)

	return sonicevents

def eventPlot(event,filename):
	plt.figure()
	t = np.linspace(0, len(event["audio"])/samplerate, num=len(event["audio"]))

	#t2 = np.linspace(0, len(se[0]["audio"])/48000.0, num=len(se[0]["features"]["ZCR"]["raw"]))

	plt.plot(t,event["audio"],linewidth=0.5)
	#plt.show()
	plt.savefig(filename,dpi=600)

def analyseSession(sessionID):
    recordingIDs = recordings.listRecodings(sessionID)

    for recordingID in recordingIDs:
        analyseRecording(recordingID,sessionID)

    genomeForSession(sessionID)

    for recordingID in recordingIDs:
        analyseGenetics(recordingID,sessionID)

def analyseGenetics(recordingID,sessionID,updateAll=0):

    recordingDetails = genimpro.recordings.getRecordingDetails(recordingID)

    for track in recordingDetails[4]:
        analyseGenotypes(track,sessionID)

    for track in recordingDetails[4]:
        addRelations(track)

def analysePhenotypes(track):

    audio = recordings.getAudioForTrack(track)
    cellBoundaries = grouping.groupBySilence(audio)
    recordings.updateCellsForTrack(track,cellBoundaries)

    phenotypes = phenotypesForCells(cellBoundaries,audio)
    recordings.updatePhenotypesForTrack(track,cellBoundaries,phenotypes)

def analyseGenotypes(track,sessionID):
    cellBoundaries = recordings.getSequencesForTrack(track)
    phenotypes = recordings.getPhenotypesForTrack(track)
    if type(phenotypes) <> type(None):
        genotypes = genotypesForCells(phenotypes,sessionID)
        recordings.updateGenotypesForTrack(track,cellBoundaries,genotypes)

def addRelations(track):
    (genotypes,sequenceData) = recordings.prepareDataForRelations(track[3])
    sequences = recordings.getSequencesForTrack(track)
    if type(genotypes) <> type(None):
        relations = calculateRelationsForGenotypes(genotypes,sequenceData)
        relations = relations[0:len(sequences)]
        recordings.updateRelationsForTrack(track,sequences,relations)

def analyseRecording(recordingID,sessionID,updateAll=0):

    recordingDetails = recordings.getRecordingDetails(recordingID)
    print "Analysing ID %i: %s on %s:" % (recordingDetails[0],recordingDetails[1],recordingDetails[2])

    for track in recordingDetails[4]:
        analysePhenotypes(track)



def isEven(number):
        return number % 2 == 0

# def phenotypeForSequence--OLD(sequence,sonicevents,audio):

#     events = sonicevents[sequence[0]:sequence[-1]]

#     eventEndsample = events[-1]["end"]

#     #always even framesize
#     #if (((events[-1]["end"] - events[0]["start"]) % 2) == 0):

#     if not isEven(events[-1]["end"] - events[0]["start"]):
#         eventEndsample = eventEndsample + 1


#     sequenceAudio = audio[events[0]["start"]:eventEndsample]

#     sequenceFeatures = {}
#     sequenceFeatures["duration"] = []
#     for feature in events[0]["features"]:
#         sequenceFeatures[feature] = []


#     for event in events:
#         sequenceFeatures["duration"].append((event["end"]-event["start"])/samplerate)
#         for feature in event["features"]:
#             if (type(event["features"][feature])==type(dict())):
#                 value = event["features"][feature]["mean"]
#             else:
#                 value = event["features"][feature]

#             sequenceFeatures[feature].append(value)

#     attributesList = ["dynamics","rhythmics","melodics","harmonics","timbre"]
#     attributes = {}

#     for attribute in attributesList:
#         attributes[attribute] = {}

#     attributes["dynamics"]["range"] = abs(np.amax(sequenceFeatures["Loudness"])-np.amin(sequenceFeatures["Loudness"]))
#     attributes["dynamics"]["median"] = np.median(sequenceFeatures["Loudness"])


#     microtime = np.amin(sequenceFeatures["duration"])
#     hist,bins = np.histogram(sequenceFeatures["duration"]/microtime)
#     attributes["rhythmics"]["variance"] = float(len(hist[np.nonzero(hist)])) / len(sequenceFeatures["duration"])
#     attributes["rhythmics"]["tempo"] = 60 / ((bins[np.argmax(hist)] + bins[np.argmax(hist)+1]) / 2.0)

#     pitches = np.asarray(sequenceFeatures["Pitch"])
#     detectedPitches = pitches[np.nonzero(sequenceFeatures["Pitch"])]
#     Pitches = (np.log(detectedPitches) - np.log(tuningFrequency)) / np.log(2) * 12 + 69
#     if len(Pitches)>0:
#     	hist,bins = np.histogram(Pitches)
#     	attributes["melodics"]["variance"] = float(len(hist[np.nonzero(hist)])) / len(Pitches)
#     	attributes["melodics"]["range"] = abs(np.amax(Pitches)-np.amin(Pitches))
#     	attributes["melodics"]["median"] = np.median(Pitches)
#     else:
#     	attributes["melodics"]["variance"] = np.nan
#     	attributes["melodics"]["range"] = np.nan
#     	attributes["melodics"]["median"] = np.nan

#     spec = essentia.standard.Spectrum()
#     SpectralPeaks = essentia.standard.SpectralPeaks(sampleRate=samplerate)
#     HPCP = essentia.standard.HPCP(sampleRate=samplerate)
#     Key = essentia.standard.Key()

#     spectrum = spec(sequenceAudio)
#     peaks = SpectralPeaks(spectrum)
#     chroma = HPCP(peaks[0],peaks[1])
#     key = Key(chroma)

#     from scipy.signal import argrelmax

#     chromaMaxima = argrelmax(chroma, order=2)
#     attributes["harmonics"]["variance"] = float(len(chromaMaxima)) / len(chroma)

#     attributes["timbre"]["roughness"] = np.median(sequenceFeatures["Roughness"])
#     attributes["timbre"]["brightness"] = np.median(sequenceFeatures["SpectralCentroid"])

#     return attributes


from essentia.standard import *
from essentia import Pool, array
import numpy as np
from scipy.ndimage.interpolation import zoom


win_s = 512             # fft size
hop_s = win_s/2           # hop size
onset_mode = "hfc"          #complex

samplerate = 44100.0
resolution=5.0

# def phenotypeForCell(cellAudio):


#     effectiveDuration = essentia.standard.EffectiveDuration(sampleRate=samplerate,thresholdRatio=0.01)
#     loudness = essentia.standard.Loudness()
#     zerocrossingrate = essentia.standard.ZeroCrossingRate()
#     w = essentia.standard.Windowing()
#     spec = essentia.standard.Spectrum()
#     centroid = essentia.standard.Centroid()
#     SpectralComplexity = essentia.standard.SpectralComplexity(sampleRate=samplerate)
#     SpectralRolloff = essentia.standard.RollOff(sampleRate=samplerate)
#     SpectralFlux = essentia.standard.Flux()
#     Envelope = essentia.standard.Envelope()
#     TCToTotal = essentia.standard.TCToTotal()
#     LAT = essentia.standard.LogAttackTime()
#     Pitch = essentia.standard.PitchYinFFT(sampleRate=samplerate)
#     SpectralPeaks = essentia.standard.SpectralPeaks(sampleRate=samplerate)
#     Dissonance = essentia.standard.Dissonance()
#     DynamicComplexity = essentia.standard.DynamicComplexity()
#     SpectralPeaks = essentia.standard.SpectralPeaks(sampleRate=samplerate)
#     RhythmExtractor = essentia.standard.RhythmExtractor2013()
#     Key = essentia.standard.Key()
#     TuningFrequency = essentia.standard.TuningFrequency()

#     if (len(cellAudio) % 2 <> 0):
#         chromaAudio = cellAudio[0:-1]
#     else:
#         chromaAudio = cellAudio

#     spectrum = spec(chromaAudio)
#     peaks = SpectralPeaks(spectrum)
#     tuning = TuningFrequency(peaks[0],peaks[1])

#     HPCP = essentia.standard.HPCP(sampleRate=samplerate, referenceFrequency =tuning[0])
#     chroma = HPCP(peaks[0],peaks[1])


#     eff_duration = effectiveDuration(cellAudio)

#     featurelist = ["ZCR","SpectralCentroid","SpectralComplexity","Roughness","Loudness"]
#     features = {}

#     for feature in featurelist:
#         features[feature] = {}
#         features[feature]["raw"]=[0]

#     chromaKeys = ["A","A#","B","C","C#","D","D#","E","F","F#","G","G#"]

#     for i,key in enumerate(chroma.tolist()):
#         features["Chroma " + chromaKeys[i]] = key

#     features["DynamicComplexity"] = list(DynamicComplexity(cellAudio))[0]/25
#     #features["SpectralCentroidA"]= centroid(spectrum)
#     #features["SpectralRolloffA"] = SpectralRolloff(spectrum)
#     ###features["SpectralFluxA"] = SpectralFlux(spectrum)
#     #features["SpectralComplexityA"] = SpectralComplexity(spectrum)
#     #features["RoughnessA"] = Dissonance(peaks[0],peaks[1])
#     features["Rhythm"] = RhythmExtractor(cellAudio)[0]/200
#     #features["ZCRA"] = zerocrossingrate(cellAudio)
#     features["Density"] = eff_duration * samplerate / len(cellAudio)


#     for featureframe in FrameGenerator(cellAudio, frameSize = hop_s, hopSize = hop_s/2):
#         features["Loudness"]["raw"].append(loudness(featureframe))
#         features["ZCR"]["raw"].append(zerocrossingrate(featureframe))
#         #features["Loudness"]["raw"].append(loudness(featureframe))
#         spectrum = spec(w(featureframe))
#         features["SpectralCentroid"]["raw"].append(centroid(spectrum))
#         features["SpectralComplexity"]["raw"].append(SpectralComplexity(spectrum))
#         #features["SpectralRolloff"]["raw"].append(SpectralRolloff(spectrum))

#         peaks = SpectralPeaks(spectrum)
#         features["Roughness"]["raw"].append(Dissonance(peaks[0],peaks[1])*10.0)
#         #features["SpectralFlux"]["raw"].append(SpectralFlux(spectrum))

#     for feature in featurelist:
#         t = np.linspace(0, len(features[feature]["raw"]), num=len(features[feature]["raw"]))
#         features[feature + " variance"]=np.var(features[feature]["raw"])
#         #features[feature]["stdev"]=np.std(features[feature]["raw"])
#         features[feature + " corrcoef"]=np.corrcoef(t,features[feature]["raw"])[0][1]
#         features[feature] = np.median(features[feature]["raw"])
#         #zoomFactor = 1/(len(features[feature]["raw"])/resolution)
#         #features[feature +  "I"] = zoom(features[feature]["raw"],zoomFactor)
#         #features[feature].pop("raw",None)


#     return features

def phenotypesForCells(cellBoundaries,audio):

    cellPhenotypes = []

    for cell in cellBoundaries:

        cellAudio = audio[cell[0]:cell[1]]
        cellPhenotype = phenotypeForCell(cellAudio)
        cellPhenotypes.append(cellPhenotype)

    return cellPhenotypes

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

def flatten(x):
    result = []
    for el in x:
        if hasattr(el, "__iter__") and not isinstance(el, basestring):
            result.extend(flatten(el))
        else:
            result.append(el)
    return result

def genotypeForCell(phenotype,genome):
    if type(phenotype) is dict:
        phenotype = flatten(phenotype.values())
    phenotype = np.asarray(phenotype)
    where_are_NaNs = np.isnan(phenotype)
    phenotype[where_are_NaNs] = 0
    u_predict, d, _, _, p, fpc = fuzz.cluster.cmeans_predict(np.vstack(phenotype), genome, 2, error=0.005, maxiter=1000)
    return u_predict.flatten()


def genotypesForCells(phenotypes,sessionID):

    genotypes = []
    genome = recordings.getGenome(sessionID)

    for i in range(0,len(phenotypes)):
        genotypes.append(genotypeForCell(phenotypes[i],genome))

    return genotypes


from scipy.spatial import distance

def calculateRelationsForGenotypes(genotypes,sequenceData,t_fitness=0.2,n_relations=10):
    matrix = distance.cdist(genotypes, genotypes, 'euclidean')
    matrix = matrix/np.amax(matrix)

    relations = []

    for i in range(len(genotypes)):
        relation = {}

        sorted_distances_indices = np.argsort(matrix[i])
        relation["children"] = []
        relation["parents"] = []

        for n in range(1,len([x for x in matrix[i] if x<t_fitness])):
            sequenceIndex = sorted_distances_indices[n]

            if sequenceData[i][2] < sequenceData[sequenceIndex][1]:
                relation["children"].append([sequenceData[sequenceIndex][0],1-matrix[i][sequenceIndex]])
            else:
                relation["parents"].append([sequenceData[sequenceIndex][0],1-matrix[i][sequenceIndex]])

        relation["fitness"] = len(relation["children"])

        relations.append(relation)

    return relations

def genomeForSession(sessionID,nGenes=10):

    allPhenotypesDicts = []

    for recordingID in recordings.listRecodings(sessionID):
        recordingDetails = recordings.getRecordingDetails(recordingID)

    for track in recordingDetails[4]:
        phenotypes = recordings.getPhenotypesForTrack(track)
        if type(phenotypes) is list:
            allPhenotypesDicts.extend(phenotypes)

    phenotypeArray = []
    keylist = allPhenotypesDicts[0].keys()
    keylist.sort()

    for phenotypeDict in allPhenotypesDicts:
        sortedDict = []
        for key in keylist:
            sortedDict.append(phenotypeDict[key])
        phenotypeArray.append(sortedDict)

    allPhenotypesVect = np.asarray(phenotypeArray)

    where_are_NaNs = np.isnan(allPhenotypesVect)
    allPhenotypesVect[where_are_NaNs] = 0

    dataByDimension = []

    for dimension in range(0,len(allPhenotypesVect[0]-1)):
        dataByDimension.append([allPhenotypesVect[i][dimension] for i in range(0,len(allPhenotypesVect)-1)])

    alldata = np.vstack((dataByDimension))

    cntr, u_orig, d, _, _, p, fpc = fuzz.cluster.cmeans(alldata, nGenes, 1.1, error=0.005, maxiter=1000)
    [u_orig[i][0] for i in range(len(d))]

    import sqlite3 as lite
    import json

    db = lite.connect('genImpro.db')
    c = db.cursor()

    genome = json.dumps(cntr.tolist())

    sqlcommand = "INSERT INTO genome (CNTR,sessionID) values (%s,%i)" % (repr(genome),sessionID)
    c.execute(sqlcommand)
    db.commit()

    print "Updated Genome for session %i" % (sessionID)


if __name__ == '__main__':

	if len(sys.argv) < 2:
		print "Usage: recording ID"
		recordings.listRecodings()
		sys.exit(1)

	recordingID = int(sys.argv[1])

	if len(sys.argv) >= 3:
		trackNumber = int(sys.argv[2])

	analyseRecording(recordingID,trackNumber)
