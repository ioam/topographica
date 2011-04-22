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
    sample_rate = param.Number(precedence=(-1))
    
    filename = param.Filename(default='sounds/complex/daisy.wav', doc="""
        File path (can be relative to Topographica's base path) to an
        audio file. The audio can be in any format accepted by pyaudiolab, 
        e.g. WAV, AIFF, or FLAC.
        """)
            
    def __init__(self, **params):
        super(AudioFile, self).__init__(**params)
        self.setParams(**params)
        
        self._loadAudioFile()

    def setParams(self, **params):
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
                        
        self.sample_rate = self.source.samplerate
        self._checkSamplingRate()


class AudioFolder(AudioFile):
    """
    Returns a rolling spectrogram, i.e. the spectral density over time 
    of a rolling window of the input audio signal, for all files in the 
    specified folder.
    """
    
    # See AudioFile itself for a detailed description of abstract status
    _abstract = True
    
    filename = param.Filename(precedence=(-1))

    # BK-TODO: change to param.Foldername once it becomes availible.
    folderpath=param.String(default='sounds/complex/', doc="""
        Folder path (can be relative to Topographica's base path) to a
        folder containing audio files. The audio can be in any format 
        accepted by pyaudiolab, i.e. WAV, AIFF, or FLAC.
        """)
         
    gap_between_sounds=param.Number(default=0.0, doc="""
        The gap in seconds to insert between consecutive soundfiles.
        """)
                 
    def __init__(self, **params):
        super(AudioFolder, self).__init__(**params)
        self.setParams(**params)
        
        self._loadAudioFolder()
        self._initialiseInterSignalGap()
    
    def setParams(self, **params):
        """
        For subclasses: to specify the values of parameters on this, 
        the parent class, subclasses might first need access to their 
        own parameter values. Having the initialization in this separate 
        method allows subclasses to make parameter changes after their 
        usual super().__init__ call.
        """
        for parameter,value in params.items():
                
            if parameter == "folderpath" and self.folderpath != value:
                setattr(self,parameter,value)
                self._loadAudioFolder()
                
            elif parameter == "gap_between_sounds" and self.gap_between_sounds != value:
                setattr(self,parameter,value)
                self._initialiseInterSignalGap()
                          
    def _loadAudioFolder(self):
        if self.folderpath[-1] != "/":
            self.folderpath = self.folderpath+"/"
            
        folder_contents = os.listdir(self.folderpath)
        self.sound_files = []
        
        for file in folder_contents:
            if file[-4:]==".wav" or file[-3:]==".wv" or \
               file[-5:]==".aiff" or file[-4:]==".aif" or \
               file[-5:]==".flac":
                self.sound_files.append(self.folderpath+file) 

        super(AudioFolder, self).setParams(filename=self.sound_files[0])
        self.next_file = 1
        
    def _initialiseInterSignalGap(self):
        self.inter_signal_gap = zeros(int(self.gap_between_sounds*self.sample_rate), dtype=float64)
        
    def _extractNextInterval(self):
        interval_start = self._next_interval_start
        interval_end = interval_start + self.samples_per_interval

        if interval_end > self.time_series.size:
        
            if self.next_file < len(self.sound_files):
                next_source = pyaudiolab.Sndfile(self.sound_files[self.next_file], 'r')
                self.next_file += 1
     
                if next_source.samplerate != self.sample_rate:
                    raise ValueError("All sound files must be of the same sample rate")
            
                next_time_series = hstack((self.time_series[interval_start:self.time_series.size], self.inter_signal_gap))
                next_time_series = hstack((next_time_series, next_source.read_frames(next_source.nframes, dtype=float64)))
                self.time_series = next_time_series
                
                self._next_interval_start = interval_start = 0   
                interval_end = self.samples_per_interval
        
            else:
                if interval_start < self.time_series.size:
                    self.warning("Returning last interval of the time series.")
                    
                    remaining_signal = self.time_series[interval_start:self.time_series.size]
                    self._next_interval_start = self.time_series.size
                    return hstack((remaining_signal, zeros(self.samples_per_interval-remaining_signal.size)))
                
                else:
                    raise ValueError("Reached the end of the time series.")
        
        self._next_interval_start += int(self.seconds_per_iteration*self.sample_rate)
        return self.time_series[interval_start:interval_end]
        

if __name__=='__main__' or __name__=='__mynamespace__':

    from topo import sheet
    import topo

    topo.sim['C']=sheet.GeneratorSheet(
        input_generator=AudioFile(filename='sounds/complex/daisy.wav',sample_window=0.3,
            seconds_per_timestep=0.3,min_frequency=20,max_frequency=20000),
            nominal_bounds=sheet.BoundingBox(points=((-0.1,-0.5),(0.0,0.5))),
            nominal_density=10,period=1.0,phase=0.05)
