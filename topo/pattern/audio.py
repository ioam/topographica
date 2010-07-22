"""
Pattern generators for audio signals.


$Id$
"""
__version__='$Revision$'

# JABALERT: Needs cleanup so that default parameters, etc. are reasonable

import numpy
import param
import os

from param.parameterized import ParamOverrides
from topo.base.sheetcoords import SheetCoordinateSystem

from topo.pattern.basic import Spectrogram
from numpy import float32, multiply, round, shape, hstack
from numpy import hanning, fft, log10, logspace

try:
    import scikits.audiolab as pyaudiolab

except ImportError:
    param.Parameterized().warning("audio.py classes will not be usable; scikits.audiolab (pyaudiolab) is not available.")


# CEBALERT: should make super's window_length, window_overlap, sample_rate, 
# and windowing_function be read-only/hidden for users of this class.
class AudioFile(Spectrogram):
    """
    Returns a spectrogram, i.e. the spectral density over time 
    of a rolling window of the input audio signal.
    """
 
    filename=param.Filename(default='sounds/complex/daisy.wav', doc="""
        File path (can be relative to Topographica's base path) to an
        audio file. The audio can be in any format accepted by pyaudiolab, 
        e.g. WAV, AIFF, or FLAC.""")
        
    amplify_from_frequency=param.Number(default=1500.0, doc="""
        The lower bound of the frequency range to be amplified.""")

    amplify_till_frequency=param.Number(default=7000.0, doc="""
        The upper bound of the frequency range to be amplified.""")
    
    amplify_by=param.Number(default=5.0, doc="""
        The percentage by which to amplify the signal between the specified
        frequency range.""")
            
    def __init__(self, **params):
        for parameter,value in params.items():
            if parameter == "filename" or\
               parameter == "amplify_from_frequency" or \
               parameter == "amplify_till_frequency" or \
               parameter == "amplify_by":
                setattr(self,parameter,value)
                
        self._source = pyaudiolab.Sndfile(self.filename, 'r')
        super(AudioFile, self).__init__(signal=self._source.read_frames(self._source.nframes, dtype=float32), 
                                        sample_rate=self._source.samplerate, **params)

    def _create_spacing(self, mini, maxi): 
        # frequency spacing to use, i.e. mapping of frequencies to sheet rows,
        self._frequency_indices = round(logspace(log10(maxi), log10(mini), num=(maxi-mini), 
                                                 endpoint=True, base=10)).astype(int)        

    def __call__(self, **params_to_override):
        # override defaults with user defined parameters.
        p = ParamOverrides(self, params_to_override)
         
        # get the dimensions of the generator sheet.
        self._sheet_dimensions = SheetCoordinateSystem(p.bounds, p.xdensity, p.ydensity).shape
        
        # calculate frequency bin divisions.
        self._create_indices(p)
                
        # perform a fft to get amplitudes of the composite frequencies.
        amplitudes = self._get_amplitudes(p)
        
        # convert output to decibels
        for frequency in range(shape(amplitudes)[0]):
            if amplitudes[frequency] > 0.0:
                multiply(20.0,log10(amplitudes[frequency]))
                
        # amplifies specified frequency range by a hanning smoothed dB window, 
        if self.amplify_by > 0.0:
            if (self.amplify_from_frequency < self.min_frequency) or (self.amplify_from_frequency > self.max_frequency):
                raise ValueError("Lower bound of frequency to amplify is outside the global frequency range.")
 
            if (self.amplify_till_frequency < self.min_frequency) or (self.amplify_till_frequency > self.max_frequency):
                raise ValueError("Upper bound of frequency to amplify is outside the global frequency range.")
            
            amplify_indices = [0,0]
            frequency_bins = logspace(log10(self.max_frequency), log10(self.min_frequency), 
                                      num=shape(amplitudes)[0], endpoint=True, base=10)
            frequency_indices = range(shape(frequency_bins)[0])
                    
            # index of end point (highest freq)
            for index in frequency_indices:
                if frequency_bins[index] <= self.amplify_till_frequency:
                    amplify_indices[1] = index; break
                    
            # index of start point (lowest freq)
            for index in reversed(frequency_indices):
                if frequency_bins[index] >= self.amplify_from_frequency:
                    amplify_indices[0] = index; break
            
            # get a smoothed amplification window of the correct size      
            amplify_indices.sort()
            assert amplify_indices[1] > amplify_indices[0]
            amplification = hanning(amplify_indices[1]-amplify_indices[0])*self.amplify_by
            
            # add it to current amplitudes if not 0, 
            # (practically - above a minimum threshold, 0.1)
            for unit in range(shape(amplification)[0]):
                amplitudes[amplify_indices[0]+unit] *= amplification[unit]+1.0

        # first make sure arrays are of compatible size, then add on 
        # latest spectral information to the spectrograms leftmost edge.
        assert shape(amplitudes)[0] == shape(self._spectrogram)[0]
        self._spectrogram = hstack((amplitudes, self._spectrogram))
                
        # knock off the column on the spectrograms right-most edge,
        # i.e. the oldest spectral information.
        self._spectrogram = self._spectrogram[0:, 0:self._spectrogram.shape[1]-1]
        
        # the following print statements are very useful when calibrating sheets,
        # allowing you to calculate how much time history a particular generator
        # sheets x dimension corresponds to.
        #print shape(amplitudes); print shape(self._spectrogram)
        
        return self._spectrogram



class AudioFolder(AudioFile):
    """
    Returns a spectrogram, i.e. the spectral density over time 
    of a rolling window of the input audio signal, for all files 
    in the specified folder.
    """
       
    folderpath=param.String(default='sounds/complex/', doc="""
        Folder path (can be relative to Topographica's base path) to a
        folder containing audio files. The audio can be in any format 
        accepted by pyaudiolab, e.g. WAV, AIFF, or FLAC.""")
         
    gap_between_sounds=param.Number(default=0.0, doc="""
        The gap in seconds to insert between consecutive soundfiles.""")
                 
    def __init__(self, **params):
        for parameter,value in params.items():
            if parameter == "folderpath" or \
               parameter == "gap_between_sounds":
                setattr(self,parameter,value)
                 
        all_files = os.listdir(self.folderpath)
        self._sound_files = []
        for file in all_files:
            if file[-4:]==".wav" or file[-3:]==".wv" or \
               file[-5:]==".aiff" or file[-4:]==".aif" or \
               file[-5:]==".flac":
                self._sound_files.append(self.folderpath+file) 

        self._next_file = 1
        super(AudioFolder, self).__init__(filename=self._sound_files[0], **params)

    def _extract_sample_window(self, p):
        # add inter-signal gap to end of current signal
        if self._window_start == 0:
            self.signal = hstack((self.signal, [0.0]*int(self.gap_between_sounds*self.sample_rate)))
            
        start = self._window_start
        end = start+self._samples_per_window
                           
        # move window forward for next cycle
        self._window_start += int(self.window_increment * self.sample_rate) 
        
        if (end > self.signal.size) and (self._next_file < len(self._sound_files)):
            next_source = pyaudiolab.Sndfile(self._sound_files[self._next_file], 'r')
            self._next_file = self._next_file + 1
 
            if next_source.samplerate != self.sample_rate:
                raise ValueError("All sound files must be of the same sample rate")
        
            next_signal = next_source.read_frames(next_source.nframes, dtype=float32)                                   
            self.signal = hstack((self.signal[start:len(self.signal)], next_signal))
            
            self._window_start = 0
            return self.signal[0:end-start]
        
        elif end > self.signal.size:
            raise ValueError("Reached the end of the signal.")
            
        return self.signal[start:end]




if __name__=='__main__' or __name__=='__mynamespace__':

    from topo import sheet
    import topo

    topo.sim['C']=sheet.GeneratorSheet(
        input_generator=AudioFile(filename='sounds/sine_waves/20000.wav',sample_window=0.3,
            seconds_per_timestep=0.1,min_frequency=20,max_frequency=20000),
            nominal_bounds=sheet.BoundingBox(points=((-0.1,-0.5),(0.0,0.5))),
            nominal_density=10,period=1.0,phase=0.05)


