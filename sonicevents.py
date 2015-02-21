#! /usr/bin/env python

import sys
from aubio import *
from essentia.standard import *
from essentia import Pool, array
import numpy as np
import matplotlib.pyplot as plt
import sqlite3 as lite
import os
import aifc
import uuid, datetime
import recordings as recordings


win_s = 512/2             # fft size
hop_s = win_s/2           # hop size
onset_mode = "hfc" 			#complex

def getOnsetsForFile(filename):

	global samplerate
	samplerate = 0
	s = source(filename, samplerate, hop_s)
	samplerate = s.samplerate

	o = onset(onset_mode, win_s, hop_s, samplerate)
	o.set_threshold(0.4)
	
	onsets = []
	total_frames = 0
	
	while True:
	    samples, read = s()
	    
	    if o(samples):
	        #print "%f" % o.get_last_s()
	        onsets.append(o.get_last())
	    total_frames += read
	    if read < hop_s: break
	return onsets



def getOnsetsForFile2(filename):

	global samplerate
	print 'Loading audio file...'
	loader = essentia.standard.AudioLoader(filename=filename)
	audio,samplerate,x,x,x,x = loader()
	mono_audio = np.asarray([audio[i][0] for i in range(0,len(audio)-1)])
	audio = mono_audio  * 4.0 #normalize
	
	# Phase 1: compute the onset detection function
	# The OnsetDetection algorithm tells us that there are several methods available in Essentia,
	# let's do two of them
	
	od1 = OnsetDetection(method = 'hfc')
	od2 = OnsetDetection(method = 'complex')
	
	# let's also get the other algorithms we will need, and a pool to store the results
	
	w = Windowing(type = 'hann')
	fft = FFT() # this gives us a complex FFT
	c2p = CartesianToPolar() # and this turns it into a pair (magnitude, phase)
	
	pool = Pool()
	
	# let's get down to business
	print 'Computing onset detection functions...'
	for frame in FrameGenerator(audio, frameSize = 1024, hopSize = 512):
	    mag, phase, = c2p(fft(w(frame)))
	    pool.add('features.hfc', od1(mag, phase))
	    pool.add('features.complex', od2(mag, phase))
	
	
	# Phase 2: compute the actual onsets locations
	onsets = Onsets()
	
	print 'Computing onset times...'
	onsets_hfc = onsets(# this algo expects a matrix, not a vector
	                    array([ pool['features.hfc'] ]),
	
	                    # you need to specify weights, but as there is only a single
	                    # function, it doesn't actually matter which weight you give it
	                    [ 1 ])
	
	onsets_complex = onsets(array([ pool['features.complex'] ]), [ 1 ])

	retVal = [int(i) for i in onsets_hfc * samplerate]
	return retVal




def getOnsetsForTrack(track):

	print "    %s (%s): %s" % (track[0],track[1],track[2])

	onsets=[]
	onsets = getOnsetsForFile(track[2])
	print "    " + str(len(onsets)) + " onsets found for %s (%s)" % (track[0],track[1])
	
	return (onsets)
	
def showAndPlay(events,audio,sequence=[]):
	from utility import float2pcm
	import pyaudio
	
	p = pyaudio.PyAudio()

	stream = p.open(format=2,channels=1,rate=int(samplerate),output=True)

	samples = audio[events[0]["start"]:events[len(events)-1]["end"]]
	startsample = events[0]["start"]
	plt.plot(samples,"b")

	for i in range (0,len(events)):
		print "mark %i from %i to %i" % (sequence[i],events[i]["start"],events[i]["end"])
		plt.text(events[i]["start"], .05, str(sequence[i]))
		plt.axvspan(events[i]["start"]-startsample, events[i]["end"]-startsample, color='red', alpha=(((i+1)%2)*0.5))
	
	pcmaudio = float2pcm(samples)
	data = struct.pack(str(len(pcmaudio)) + 'h',*pcmaudio)
	stream.write(data)
	
	plt.show() #block=False		

	stream.stop_stream()
	stream.close()
	
	p.terminate()
	

	
def getFeaturesForOnsets(onsets,filename,t_duration=0.02):	
	loader = essentia.standard.AudioLoader(filename=filename)
	audio,samplerate,x,x,x,x = loader()
	mono_audio = np.asarray([audio[i][0] for i in range(0,len(audio)-1)])
	mono_audio = mono_audio  * 4.0 #normalize

	effectiveDuration = essentia.standard.EffectiveDuration(sampleRate=samplerate,thresholdRatio=0.000)
	loudness = essentia.standard.Loudness()
	zerocrossingrate = essentia.standard.ZeroCrossingRate()
	w = essentia.standard.Windowing()
	spec = essentia.standard.Spectrum()
	centroid = essentia.standard.Centroid()
	SpectralComplexity = essentia.standard.SpectralComplexity()
	Pitch = essentia.standard.PitchYinFFT()
    
	sonicevents = []
	lastDuration_ratio = 0
	onsetStart = onsets[0]
	
	
	for i in range(0,len(onsets)-2):
		if i < len(onsets)-1:
			onsetEnd = onsets[i+1]
		else:
			onsetEnd = len(mono_audio)

		duration = (onsetEnd - onsetStart)/samplerate
		durationAdd = (onsetEnd - onsets[i])/samplerate
		

		
		frame = mono_audio[onsetStart:onsetEnd]
		eff_duration = effectiveDuration(frame)

		length_samples = int(eff_duration * samplerate)
		eff_frame = mono_audio[onsetStart:onsetStart+length_samples]
		duration_ratio =  eff_duration / duration
		
		featurelist = ["Loudness","ZCR","SpectralCentroid","SpectralComplexity"]
		features = {}
		features["effLength"]=length_samples
		features["durationRatio"]=duration_ratio
		
		for feature in featurelist:
			features[feature] = {}
			features[feature]["raw"]=[]
		
		for featureframe in FrameGenerator(eff_frame, frameSize = win_s, hopSize = hop_s):
		    features["Loudness"]["raw"].append(loudness(featureframe))
		    features["ZCR"]["raw"].append(zerocrossingrate(featureframe))
		    spectrum = spec(w(featureframe))
		    features["SpectralCentroid"]["raw"].append(centroid(spectrum))
		    features["SpectralComplexity"]["raw"].append(SpectralComplexity(spectrum))
		    #features["Pitch"]["raw"].append(Pitch(spectrum))

		for feature in featurelist:
			t = np.linspace(0, len(features[feature]["raw"]), num=len(features[feature]["raw"]))
			features[feature]["median"]=np.median(features[feature]["raw"])
			features[feature]["mean"]=np.mean(features[feature]["raw"])
			features[feature]["max"]=np.amax(features[feature]["raw"])
			features[feature]["min"]=np.amin(features[feature]["raw"])
			features[feature]["variance"]=np.var(features[feature]["raw"])
			features[feature]["stdev"]=np.std(features[feature]["raw"])
			features[feature]["corrcoef"]=np.corrcoef(t,features[feature]["raw"])[0][1]
		
		if (onsetEnd+1500) < len(mono_audio):
			frameEnd = mono_audio[onsetEnd-1500:onsetEnd]
			loudnessEnd = loudness(frameEnd)
			frameNext = mono_audio[onsetEnd:onsetEnd+1500]
			loudnessNext = loudness(frameNext)
			loudnessDiff = abs(loudnessEnd - loudnessNext)

		if (features["Loudness"]["mean"] > 0.001) & (durationAdd > t_duration):# & (loudnessDiff>0.03):
			
			sonicevents.append({"start":onsetStart,"end":onsetEnd,"features":features,"audio":eff_frame})
			onsetStart = onsets[i+1]

	return (sonicevents, mono_audio)

	
	


