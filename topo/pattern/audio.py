"""
Pattern generators for audio signals.

$Id$
"""
__version__='$Revision$'


import numpy
import param
import os

from param.parameterized import ParamOverrides
from topo.base.sheetcoords import SheetCoordinateSystem
from topo.pattern.basic import TimeSeries, PowerSpectrum, Spectrogram
from topo.base.patterngenerator import PatternGenerator

from numpy import array, float32, multiply, round, shape, hstack, hanning, fft, log10, logspace, where, \
    concatenate, reshape, random, float128, sqrt, log, floor, zeros, arange, ones, exp, pi, size, complex256, \
    sum, cos, vstack, float64, ceil, fliplr, poly1d

try:
    import matplotlib.ticker
    import pylab
except ImportError:
    param.Parameterized(name=__name__).warning("Could not import matplotlib; module will not be useable.")
    from basic import ImportErrorRaisingFakeModule
    pylab = ImportErrorRaisingFakeModule("matplotlib")

try:
    import scikits.audiolab as pyaudiolab
except ImportError:
    param.Parameterized().warning("audio.py classes will not be usable;" \
        "scikits.audiolab (pyaudiolab) is not available.")
        
        
class AudioFile(TimeSeries):
    """
    Requires an audio file in any format accepted by pyaudiolab (wav, aiff,
    flac).
    """
    
    # See TimeSeries itself for a detailed description of abstract status
    _abstract = True
        
    time_series = param.Parameter(precedence=(-1))
    sampling_rate = param.Number(precedence=(-1))
    
    filename = param.Filename(default='sounds/complex/daisy.wav', doc="""
        File path (can be relative to Topographica's base path) to an
        audio file. The audio can be in any format accepted by pyaudiolab, 
        e.g. WAV, AIFF, or FLAC.
        """)
            
    def __init__(self, **params):
        super(AudioFile, self).__init__(**params)
        self.initialiseParams(**params)
        
        self._loadAudioFile()

    def initialiseParams(self, **params):
        """
        For subclasses: to specify the values of parameters on this, 
        the parent class, subclasses might first need access to their 
        own parameter values. Having the initialization in this separate 
        method allows subclasses to make parameter changes after their 
        usual super().__init__ call.
        """
        for parameter,value in params.items():
            # Trying to combine the following into one line fails, python 
            # will try to evaluate both logical statements at once and 
            # since 'value' could be of any type the result is often a 
            # type mismatch on comparison. 
            if parameter == "filename":
                if self.filename != value:
                    setattr(self,parameter,value)
                    self._loadAudioFile()
        
    def _loadAudioFile(self):
        self.source = pyaudiolab.Sndfile(self.filename, 'r')
        
        self.time_series = self.source.read_frames(self.source.nframes, dtype=float64)
        self._checkTimeSeries()
                        
        self.sampling_rate = self.source.samplerate
        self._checkSamplingRate()


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
                 
        self.inter_signal_gap = [0.0]*int(self.gap_between_sounds*self.sample_rate)

        all_files = os.listdir(self.folderpath)
        self._sound_files = []
        for file in all_files:
            if file[-4:]==".wav" or file[-3:]==".wv" or \
               file[-5:]==".aiff" or file[-4:]==".aif" or \
               file[-5:]==".flac":
                self._sound_files.append(self.folderpath+file) 

        super(AudioFolder, self).__init__(filename=self._sound_files[0], **params)
        self._next_file = 1
        
    def _extract_sample_window(self, p):
        window_start = self._next_window_start
        window_end = window_start+self._samples_per_window

        if window_end > self.signal.size and self._next_file < len(self._sound_files):
            next_source = pyaudiolab.Sndfile(self._sound_files[self._next_file], 'r')
            self._next_file += 1
 
            if next_source.samplerate != self.sample_rate:
                raise ValueError("All sound files must be of the same sample rate")
        
            self.signal = hstack((self.signal[window_start:self.signal.size], self.inter_signal_gap))
            self.signal = hstack((self.signal, next_source.read_frames(next_source.nframes, dtype=float32)))
            
            self._next_window_start = int(self.window_increment * self.sample_rate) 
            return self.signal[0:self._samples_per_window]
        
        elif window_end > self.signal.size:
            raise ValueError("Reached the end of the signal.")
            self.signal = hstack((self.signal[window_start:self.signal.size], [0.0]*(window_end-self.signal.size))) 
        
        self._next_window_start += int(self.window_increment * self.sample_rate) 
        return self.signal[window_start:window_end]


if __name__=='__main__' or __name__=='__mynamespace__':

    from topo import sheet
    import topo

    topo.sim['C']=sheet.GeneratorSheet(
        input_generator=AudioFile(filename='sounds/sine_waves/20000.wav',sample_window=0.3,
            seconds_per_timestep=0.1,min_frequency=20,max_frequency=20000),
            nominal_bounds=sheet.BoundingBox(points=((-0.1,-0.5),(0.0,0.5))),
            nominal_density=10,period=1.0,phase=0.05)
