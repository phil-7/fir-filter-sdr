# use python3 -m src.capture to run

import config
import numpy as np
import sys
import SoapySDR

from SoapySDR import *


# find connected device(s) and save them to results
results = SoapySDR.Device.enumerate()
 
# open the SDR. if no devices connected, exit program
try:   
    sdr = SoapySDR.Device(results[0])
except:
    sys.exit("No Devices Found")
    
# config the SDR
sdr.setFrequency(SOAPY_SDR_RX, 0, config.FREQ) # 0 is the channel
sdr.setSampleRate(SOAPY_SDR_RX, 0, config.SAMP_RATE)
sdr.setGain(SOAPY_SDR_RX, 0, config.GAIN)
sdr.setAntenna(SOAPY_SDR_RX, 0, config.ANTENNA)

# setup the stream
rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32) # collects complex 32 samples
sdr.activateStream(rxStream) # start stream

# allocate memory
total_samples = int(config.DURATION * config.SAMP_RATE)
buff = np.empty(total_samples, dtype=np.complex64) # main capture buffer

# can't save everything at once. create temp buffer
chunk_size = 4096 # how many samples app request per read
chunk = np.empty(chunk_size, dtype=np.complex64) # temp buffer for every loop

# store chunks in buff
samples_collected = 0

while samples_collected < total_samples:  # keep streaming until you have enough samples
    sr = sdr.readStream(rxStream, [chunk], chunk_size)  # read samples
    
    if sr.ret > 0:  # sr.ret tells you how many samples were actually written
        # prevent writing past the end of buff
        if samples_collected + sr.ret > total_samples:
            sr.ret = total_samples - samples_collected

        end = samples_collected + sr.ret  # compute where new samples go
        buff[samples_collected:end] = chunk[:sr.ret]  # copy valid samples
        samples_collected = end  # update count
    else:
        break


# end stream and save to file
sdr.deactivateStream(rxStream)
sdr.closeStream(rxStream)

np.save("data/raw/capture.npy", buff[:samples_collected])
