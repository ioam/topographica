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
from topo.pattern.basic import Spectrogram

from numpy import array, float32, multiply, round, shape, hstack, hanning, fft, log10, logspace, where, \
    concatenate, reshape

try:
    import scikits.audiolab as pyaudiolab
except ImportError:
    param.Parameterized().warning("audio.py classes will not be usable;" & 
        "scikits.audiolab (pyaudiolab) is not available.")
        
        
class AudioFile(Spectrogram):
    """
    Returns a spectrogram, i.e. the spectral density over time 
    of a rolling window of the input audio signal.
    """
    
    window_increment = param.Number(precedence=(-1))
    window_length = param.Number(precedence=(-1))
    sample_rate = param.Number(precedence=(-1))
    windowing_function = param.Parameter(precedence=(-1))
    
    filename=param.Filename(default='sounds/complex/daisy.wav', doc="""
        File path (can be relative to Topographica's base path) to an
        audio file. The audio can be in any format accepted by pyaudiolab, 
        e.g. WAV, AIFF, or FLAC.""")
        
    amplify_from_frequency=param.Number(default=1500.0, doc="""
        The lower bound of the frequency range to be amplified.""")

    amplify_till_frequency=param.Number(default=7000.0, doc="""
        The upper bound of the frequency range to be amplified.""")
    
    amplify_by_percentage=param.Number(default=5.0, doc="""
        The percentage by which to amplify the signal between the specified
        frequency range.""")
            
    def __init__(self, **params):
        for parameter,value in params.items():
            if parameter == "filename" or ("amplify" in parameter):
                setattr(self, parameter, value)
                
        self._source = pyaudiolab.Sndfile(self.filename, 'r')
        super(AudioFile, self).__init__(signal=self._source.read_frames(self._source.nframes, dtype=float32), 
            sample_rate=self._source.samplerate, **params)

    def _map_frequencies_to_rows(self, index_min_freq, index_max_freq): 
        """
        Frequency spacing to use, i.e. how to map the available frequency range
        to the discrete sheet rows.

        Overload if custom frequency spacing is required.
        """
        self._frequency_spacing_indices = round(logspace(log10(index_max_freq), log10(index_min_freq), 
            num=(index_max_freq-index_min_freq), endpoint=True, base=10)).astype(int)
            
    def __call__(self, **params_to_override):
        p = ParamOverrides(self, params_to_override)
         
        self._sheet_dimensions = SheetCoordinateSystem(p.bounds, p.xdensity, p.ydensity).shape

        self._create_frequency_indices(p)
                
        amplitudes = self._get_amplitudes(p)
                
        if self.amplify_by_percentage > 0.0:
            if (self.amplify_from_frequency < self.min_frequency) or \
               (self.amplify_from_frequency > self.max_frequency):
                raise ValueError("Lower bound of frequency to amplify is outside the global frequency range.")
 
            elif (self.amplify_till_frequency < self.min_frequency) or \
                    (self.amplify_till_frequency > self.max_frequency):
                raise ValueError("Upper bound of frequency to amplify is outside the global frequency range.")
            
            else:
                frequency_bins = logspace(log10(self.max_frequency), log10(self.min_frequency), 
                    num=shape(amplitudes)[0], endpoint=True, base=10)
                                                    
                amplify_between = [frequency for frequency in frequency_bins \
                    if frequency <= self.amplify_till_frequency and frequency >= self.amplify_from_frequency]
                                
                # the larger the index, the lower the frequency.
                amplify_start = where(frequency_bins == max(amplify_between))[0][0]
                amplify_end = where(frequency_bins == min(amplify_between))[0][0]
                
                # build an array, of equal length to amplitude array, containing percentage amplifications.
                amplify_by = 1.0 + hanning(amplify_end-amplify_start+1)*self.amplify_by_percentage/100                
                amplify_by = concatenate((array([1.0]*amplify_start, dtype=float32), amplify_by, \
                    array([1.0]*(len(frequency_bins)-amplify_end-1), dtype=float32))).reshape((-1, 1))

                amplitudes = multiply(amplitudes, amplify_by)
        
        # convert amplitudes to decibels
        amplitudes = array(map(lambda amplitude: 20.0*log10(amplitude) if amplitude > 0.0 else 0.0, amplitudes))
                
        assert shape(amplitudes)[0] == shape(self._spectrogram)[0]
        self._spectrogram = hstack((amplitudes, self._spectrogram))
        
        # knock off old spectral information, right-most column.
        self._spectrogram = self._spectrogram[0:, 0:self._spectrogram.shape[1]-1]
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
