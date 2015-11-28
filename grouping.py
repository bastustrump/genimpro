import recordings as recordings
import numpy as np
import operator
import math

from scipy.signal import argrelmax 
from essentia.standard import *

def silenceGaps(frames):

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
    maxima = argrelmax(featureArray, order=25)
    featureMaxima = maxima[0] -1
    
    silenceGaps = []
    
    for maximum in featureMaxima:
        silenceGaps.append([maximum,maximum+consecutiveNumbers[maximum+1]])
    
    return silenceGaps

def groupBySilence(audio,hopSize=4*1024,t_silence=0.05,plot=0):
    
    timestamps = len(audio)
    
    loudness = essentia.standard.Loudness()
    energy = Energy()
    
    silenceFrames = []

    for frame in FrameGenerator(audio, frameSize = hopSize*2, hopSize = hopSize):
        if loudness(frame) >= t_silence:
            silenceFrames.append(0)
        else:
            silenceFrames.append(1)
      
    gaps = silenceGaps(silenceFrames)
    
    gapFrames = []
    
    for gap in gaps:
        gapFrames.extend(range(gap[0],gap[1]+1))
    
    audioFrames = range(0,len(audio)/hopSize)
    groupFrames = [x for x in audioFrames if x not in gapFrames]
    
    from numpy import array, diff, where, split
    result= split(groupFrames, where(diff(groupFrames)>1)[0]+1)
    splitGroupFrames =  map(list, result)
    
    groups = []
    
    for group in splitGroupFrames:
        groups.append([group[0]*hopSize,((group[-1]+1)*hopSize) - 1])
        
    if plot:
        plt.figure(figsize=(16, 10))
        plt.plot(audio,'0.5',label="Audio Waveform",linewidth=0.7)
        for gap in gaps:
            plt.axvspan(gap[0]*hopSize,(gap[1]+1)*hopSize-1, color='r', alpha=0.3)
            
        for group in groups:
            plt.axvspan(group[0],group[1], color='g', alpha=0.3)
            
        wavPlayer(audio,samplerate)
        
    return groups