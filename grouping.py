import recordings as recordings
import numpy as np
import operator
import math

samplerate=44100.0

from scipy.signal import argrelmax 
from essentia.standard import *

def silenceGaps(frames,order=20):
    
    from scipy.signal import argrelmax 

    consecutiveNumbers = [0]
    for i in range(0,len(frames)-2):
        counter = 0
        j = i

        while 1:
            if j < len(frames)-1:
                if frames[j+1]==1:
                    counter+=1
                    j+=1
                else:
                    break
            else:
                break
                
        consecutiveNumbers.append(counter)
    
    featureArray = np.asarray(consecutiveNumbers)
    print order
    if order<1:
        order = 1
    maxima = argrelmax(featureArray, order=order)
    featureMaxima = maxima[0] -1
    
    silenceGaps = []
    
    for maximum in featureMaxima:
        silenceGaps.append([maximum,maximum+consecutiveNumbers[maximum+1]])
    
    return silenceGaps

def groupBySilence(audio,hopSize=1024,t_silence=0.04,plot=0,orderDivisor=15,minGapSize=8):
    
    timestamps = len(audio)
    
    loudness = essentia.standard.Loudness()
    energy = Energy()
    
    silenceFrames = []

    for frame in FrameGenerator(audio, frameSize = hopSize*2, hopSize = hopSize):
        if loudness(frame) >= t_silence:
            silenceFrames.append(0)
        else:
            silenceFrames.append(1)
    
    gaps = silenceGaps(silenceFrames,int(len(audio)/samplerate/orderDivisor))
    
    gapFrames = []
    
    for gap in gaps:
        if (gap[1]-gap[0])>minGapSize:#10
            gapFrames.extend(range(gap[0],gap[1]))
    
    
    audioFrames = range(0,len(audio)/hopSize)
    groupFrames = [x for x in audioFrames if x not in gapFrames]

    
    from numpy import array, diff, where, split
    result= split(groupFrames, where(diff(groupFrames)>2)[0]+1)
    splitGroupFrames =  map(list, result)
    
    groups = []
    
    for group in splitGroupFrames:
        if len(group) > 4:
            groups.append([group[0]*hopSize,((group[-1]+1)*hopSize)])
        
    return groups