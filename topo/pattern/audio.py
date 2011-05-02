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
        super(AudioFile, self).setParams(**params)

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

    folderpath=param.Foldername(default='sounds/complex', doc="""
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
        folder_contents = os.listdir(self.folderpath)
        self.sound_files = []
        
        for file in folder_contents:
            if file[-4:]==".wav" or file[-3:]==".wv" or \
               file[-5:]==".aiff" or file[-4:]==".aif" or \
               file[-5:]==".flac":
                self.sound_files.append(self.folderpath+"/"+file) 

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
        

class AuditorySpectrogram(Spectrogram):
    """
    Extends Spectrogram to provide a response in decibels over an octave scale.
    """
     
    def __init__(self, **params):
        super(AuditorySpectrogram, self).__init__(**params)
    
    def _mapFrequenciesToRows(self, index_of_min_freq, index_of_max_freq):
        """
        Frequency spacing to use, i.e. how to map the available frequency range to 
        the discrete sheet rows.
        
        NOTE: We're calculating the spacing of a range between the *indicies* of the 
        highest and lowest frequencies, the actual segmentation and averaging of the 
        frequencies to fit this spacing occurs in _getAmplitudes().
        
        This method is here solely to provide a minimal overload if custom spacing is 
        required.
        """
        # octave scale
        self.frequency_index_spacing = ceil(logspace(log10(index_of_max_freq), log10(index_of_min_freq), 
            num=(index_of_max_freq-index_of_min_freq), endpoint=True, base=10))
                
    def _convertToDecibels(self, amplitudes):
        amplitudes[amplitudes==0] = 1.0
        return (20.0 * log10(abs(amplitudes)))
    
    def __call__(self, **params_to_override):        
        if self._first_run:
            self._initializeWindowParams(**params_to_override)
            self._onFirstRun(ParamOverrides(self, params_to_override))
            
        return self._updateSpectrogram(self._convertToDecibels(self._getAmplitudes()))


class AuditorySpectrogramWithSimpleOuterEar(AuditorySpectrogram):
    """
    Extends Spectrogram with a simple model of outer ear amplification. 
    One can set both the range to amplify and the amount.
    """
        
    amplify_from_frequency=param.Number(default=1500.0, doc="""
        The lower bound of the frequency range to be amplified.
        """)

    amplify_till_frequency=param.Number(default=7000.0, doc="""
        The upper bound of the frequency range to be amplified.
        """)
    
    amplify_by_percentage=param.Number(default=5.0, doc="""
        The percentage by which to amplify the signal between 
        the specified frequency range.
        """)

    def __init__(self, **params):
        super(AuditorySpectrogramWithSimpleOuterEar, self).__init__(**params)
        self._initializeAmplifyParameters(**params)

    def _initializeAmplifyParameters(self, **params):
        """
        For subclasses: to specify the values of parameters on this, 
        the parent class, subclasses might first need access to their 
        own parameter values. Having the initialization in this 
        separate method allows subclasses to make the usual call to 
        super.__init__(**params)
        """
        for parameter,value in params.items():
            # Trying to combine the following into one line fails, python 
            # will try to evaluate both logical statements at once and 
            # since 'value' could be of any type the result is often a 
            # type mismatch on comparison. 
            if parameter == "amplify_from_frequency" or \
                parameter == "amplify_till_frequency" or \
                parameter == "amplify_by_percentage":
                if value < 0:
                    raise ValueError("Cannot have a negative value for amplify_from_frequency, " +\
                        "amplify_till_frequency, or amplify_by_percentage.")
            
        if self.amplify_from_frequency > self.amplify_till_frequency:
            raise ValueError("Amplify from must be less than amplify till.")

    def __call__(self, **params_to_override):
        if self._first_run:
            self._initializeWindowParams(**params_to_override)
            self._initializeAmplifyParameters(**params_to_override)
            self._onFirstRun(ParamOverrides(self, params_to_override))
                
        amplitudes = self._getAmplitudes()
        self.frequency_divisions = logspace(log10(self.max_frequency), log10(self.min_frequency), 
            num=self._sheet_dimensions[0], endpoint=True, base=10)
            
        if self.amplify_by_percentage > 0:
            if (self.amplify_from_frequency < self.min_frequency) or \
               (self.amplify_from_frequency > self.max_frequency):
                raise ValueError("Lower bound of frequency to amplify is outside the global frequency range.")
 
            elif (self.amplify_till_frequency < self.min_frequency) or \
                (self.amplify_till_frequency > self.max_frequency):
                raise ValueError("Upper bound of frequency to amplify is outside the global frequency range.")
            
            else:
                amplify_between = [frequency for frequency in self.frequency_divisions \
                    if frequency <= self.amplify_till_frequency and frequency >= self.amplify_from_frequency]
                                
                # the larger the index, the lower the frequency.
                amplify_start = where(self.frequency_divisions == max(amplify_between))[0][0]
                amplify_end = where(self.frequency_divisions == min(amplify_between))[0][0]
                
                # build an array of equal length to amplitude array, containing percentage amplifications.
                amplified_range = 1.0 + hanning(amplify_end-amplify_start+1) * self.amplify_by_percentage/100.0                
                amplify_by = concatenate((ones(amplify_start), amplified_range, ones(len(self.frequency_divisions)-amplify_end-1))).reshape((-1, 1))

                amplitudes = multiply(amplitudes, amplify_by)
        
        return self._updateSpectrogram(self._convertToDecibels(amplitudes))
        

class LyonsCochlearModel(PatternGenerator):
    """
    Outputs a cochlear decomposition as a set of frequency responses of linear 
    band-pass filters. Employs Lyons Cochlear Model to do so.
    
    R. F. Lyon, "A computational model of filtering, detection and compression
    in the cochlea." in Proc. of the IEEE Int. Conf. Acoust., Speech, Signal
    Processing, Paris, France, May 1982.
        
    Specific implementation details can be found in: 
    
    Malcolm Slaney, "Lyon's Cochlear Model, in Advanced Technology Group,
    Apple Technical Report #13", 1988.
    """
    
    signal = param.Parameter(default=TimeSeries(),doc="""
        A TimeSeries object to be fed to the model.
        
        This can be any kind of signal, be it from audio files or live
        from a mic, as long as the values conform to a TimeSeries.
        """)
    
    quality_factor = param.Number(default=8.0,doc="""
        Quality factor controls the bandwidth of each cochlear filter.
        
        The bandwidth of each cochlear filter is a function of its 
        center frequency. At high frequencies the bandwidth is 
        approximately equal to the center frequency divided by a 
        quality constant (quality_factor). At lower frequncies the 
        bandwidth approaches a constant given by: 1000/quality_factor.
        """)
    
    stage_overlap_factor = param.Number(default=4.0,doc="""
        The degree of overlap between filters.
    
        Successive filter stages are overlapped by a fraction of their 
        bandwidth. The number is arbitrary but smaller numbers lead to 
        more computations. We currently overlap 4 stages within the 
        bandpass region of any one filter.
        """)
                
    def __init__(self, **params):
        super(LyonsCochlearModel, self).__init__(**params)
        
        self._first_run = True    
        self._initializeCochlearParameters(**params)
        self._generateCochlearFilters()

    def _initializeCochlearParameters(self, **params):
        """
        For subclasses: to specify the values of parameters on this, 
        the parent class, subclasses might first need access to their 
        own parameter values. Having the initialization in this separate 
        method allows subclasses to make parameter changes after their 
        usual super().__init__ call.
        """
        for parameter,value in params.items():
            setattr(self,parameter,value)
                                                  
        # Hardwired Parameters specific to model, which is to say changing
        # them without knowledge of the mathematics of the model is a bad idea.
        self.sample_rate = self.signal.sampling_rate
        self.half_sample_rate = float128(self.sample_rate/2.0)
        self.quart_sample_rate = float128(self.half_sample_rate/2.0)
 
        self.ear_q = float128(self.quality_factor)
        self.ear_step_factor = float128(1.0/self.stage_overlap_factor)

        self.ear_break_f = float128(1000.0)
        self.ear_break_squared = self.ear_break_f*self.ear_break_f

        self.ear_preemph_corner_f = float128(300.0)
        self.ear_zero_offset = float128(1.5)
        self.ear_sharpness = float128(5.0)
    
    def _earBandwidth(self, cf):
        return sqrt(cf*cf + self.ear_break_squared) / self.ear_q
        
    def _maxFrequency(self):
        bandwidth_step_max_f = self._earBandwidth(self.half_sample_rate) * self.ear_step_factor    
        return self.half_sample_rate + bandwidth_step_max_f - bandwidth_step_max_f*self.ear_zero_offset

    def _numOfChannels(self):
        min_f = self.ear_break_f / sqrt(4.0*self.ear_q*self.ear_q - 1.0)
        channels = log(self.max_f_calc) - log(min_f + sqrt(min_f*min_f + self.ear_break_squared))
        
        return int(floor(self.ear_q*channels/self.ear_step_factor))

    def _calcCentreFrequenciesTill(self, channel_index):
        if (self.centre_frequencies[channel_index] > 0):
            return self.centre_frequencies[channel_index]
        else:
            step = self._calcCentreFrequenciesTill(channel_index-1)
            channel_cf = step - self.ear_step_factor*self._earBandwidth(step)
            self.centre_frequencies[channel_index] = channel_cf
            
            return channel_cf

    def _evaluateFiltersForFrequencies(self, filters, frequencies):
        Zs = exp(2j*pi*frequencies/self.sample_rate)
        Z_squareds = Zs * Zs
        
        zeros = ones((shape(frequencies)[0], shape(filters[0])[0], 3), dtype=complex256)
        zeros[:,:,2] = filters[0][:,2] * Z_squareds
        zeros[:,:,1] = filters[0][:,1] * Zs
        zeros[:,:,0] = filters[0][:,0]
        zeros = sum(zeros, axis=2)

        poles = ones((shape(frequencies)[0], shape(filters[1])[0], 3), dtype=complex256)
        poles[:,:,2] = filters[1][:,2] * Z_squareds
        poles[:,:,1] = filters[1][:,1] * Zs
        poles[:,:,0] = filters[1][:,0]
        poles = sum(poles, axis=2)
        
        return zeros / poles

    def _evaluateFiltersOverTime(self, filters, samples):
        Zs = exp(2j*pi*frequencies/self.sample_rate)
        Z_squareds = Zs * Zs
        
        zeros = ones((shape(frequencies)[0], shape(filters[0])[0], 3), dtype=complex256)
        zeros[:,:,2] = filters[0][:,2] * Z_squareds
        zeros[:,:,1] = filters[0][:,1] * Zs
        zeros[:,:,0] = filters[0][:,0]
        zeros = sum(zeros, axis=2)

        poles = ones((shape(frequencies)[0], shape(filters[1])[0], 3), dtype=complex256)
        poles[:,:,2] = filters[1][:,2] * Z_squareds
        poles[:,:,1] = filters[1][:,1] * Zs
        poles[:,:,0] = filters[1][:,0]
        poles = sum(poles, axis=2)
        
        return zeros / poles
        
    # a frequency and gain are specified so that the resulting filter can 
    # be normalized to have any desired gain at a specified frequency.
    def _makeFilters(self, zeros, poles, f, desired_gains):  
        desired_gains = reshape(desired_gains,[size(desired_gains),1])
        
        unit_gains = self._evaluateFiltersForFrequencies([zeros,poles], f)
        unit_gains = reshape(unit_gains,[size(unit_gains),1])
        
        return [zeros*desired_gains, poles*unit_gains]
        
    def _frequencyResponses(self, evaluated_filters):
        evaluated_filters[evaluated_filters==0] = 1.0
        return 20.0 * log10(abs(evaluated_filters))

    def _specificFilter(self, x2_coefficient, x_coefficient, constant):  
        return array([[x2_coefficient,x_coefficient,constant], ], dtype=float128)
            
    def _firstOrderFilterFromCorner(self, corner_f):
        polynomial = zeros((1,3), dtype=float128)
        polynomial[:,0] = -exp(-2.0*pi*corner_f/self.sample_rate)
        polynomial[:,1] = 1.0

        return polynomial

    def _secondOrderFilterFromCenterQ(self, cf, quality):
        cf_as_ratio = cf/self.sample_rate
        
        rho = exp(-pi*cf_as_ratio/quality)
        rho_squared = rho*rho
        
        theta = 2.0*pi*cf_as_ratio * sqrt(1.0-1.0/(4.0*quality*quality))
        theta_calc = -2.0*rho*cos(theta)
        
        polynomial = ones((size(cf),3), dtype=float128)
        polynomial[:,1] = theta_calc
        polynomial[:,2] = rho_squared
        
        return polynomial
     
    def _earFilterGains(self):
        return self.centre_frequencies[:-1] / self.centre_frequencies[1:]

    def _earFirstStage(self):    
        outer_middle_ear_filter = self._makeFilters(self._firstOrderFilterFromCorner(self.ear_preemph_corner_f), 
            self._specificFilter(1.0,0.0,0.0), array([0.0]), 1.0)

        high_freq_compensator = self._makeFilters(self._specificFilter(1.0,0.0,-1.0), self._specificFilter(0.0,0.0,1.0), 
            array([self.quart_sample_rate]), 1.0)
        
        pole_pair = self._makeFilters(self._specificFilter(0.0,0.0,1.0), 
            self._secondOrderFilterFromCenterQ(self.cascade_pole_cfs[0],self.cascade_pole_qs[0]), 
            array([self.quart_sample_rate]), 1.0)
        
        top = poly1d(fliplr(high_freq_compensator[0])[0]) * poly1d(fliplr(pole_pair[0])[0]) \
            * poly1d(fliplr(outer_middle_ear_filter[0])[0])
        
        bottom = poly1d(fliplr(high_freq_compensator[1])[0]) * poly1d(fliplr(pole_pair[1])[0]) \
            * poly1d(fliplr(outer_middle_ear_filter[1])[0])
        
        print outer_middle_ear_filter
        print [top, bottom]
        
        outer_middle_ear_evaluations = self._evaluateFiltersForFrequencies(outer_middle_ear_filter, self.frequencies)
        high_freq_compensator_evaluations = self._evaluateFiltersForFrequencies(high_freq_compensator, self.frequencies)
        pole_pair_evaluations = self._evaluateFiltersForFrequencies(pole_pair, self.frequencies)
        
        return outer_middle_ear_evaluations * high_freq_compensator_evaluations * pole_pair_evaluations

    def _earAllOtherStages(self):
        zeros = self._secondOrderFilterFromCenterQ(self.cascade_zero_cfs[1:], self.cascade_zero_qs[1:])
        poles = self._secondOrderFilterFromCenterQ(self.cascade_pole_cfs[1:], self.cascade_pole_qs[1:])
        
        stage_filters = self._makeFilters(zeros, poles, array([0.0]), self.ear_filter_gains)
        return self._evaluateFiltersForFrequencies(stage_filters, self.frequencies)

    def _generateCascadeFilters(self):
        
        cascade_filters = self.ear_stages
        
        for channel in range(1,self.num_of_channels):
            cascade_filters[channel,:] = cascade_filters[channel,:] * cascade_filters[channel-1,:]
        
        return self._frequencyResponses(cascade_filters)
        
    def _generateCochlearFilters(self):
        max_f = self._maxFrequency()
        self.max_f_calc = max_f + sqrt(max_f*max_f + self.ear_break_squared)

        self.num_of_channels = self._numOfChannels()

        self.centre_frequencies = zeros(self.num_of_channels, dtype=float128)
        self.centre_frequencies[0] = max_f
        self._calcCentreFrequenciesTill(self.num_of_channels-1)

        bandwidths = self._earBandwidth(self.centre_frequencies)
        
        self.cascade_zero_cfs = self.centre_frequencies + bandwidths*self.ear_step_factor*self.ear_zero_offset
        self.cascade_zero_qs = self.ear_sharpness * self.cascade_zero_cfs / bandwidths
        self.cascade_pole_cfs = self.centre_frequencies
        self.cascade_pole_qs = self.centre_frequencies / bandwidths
        
        self.ear_filter_gains = self._earFilterGains()
        
        self.frequencies = arange(self.half_sample_rate).reshape(self.half_sample_rate, 1)
        
        self.ear_stages = hstack((self._earFirstStage(), self._earAllOtherStages())).transpose() 
        
        self.cochlear_channels = self._generateCascadeFilters()
        
    def _onFirstRun(self, overrides):
        self._first_run = False    

        self._sheet_dimensions = SheetCoordinateSystem(overrides.bounds,\
            overrides.xdensity,overrides.ydensity).shape
    
        if self._sheet_dimensions[0] != self.num_of_channels:
            raise ValueError("The number of Sheet Rows must correspond to the number of Lyons Filters. " +\
            "Adjust the number sheet rows from [%s] to [%s]."%(self._sheet_dimensions[0], self.num_of_channels))
        
        self.previous_interval_samples = self.signal.extractSpecificInterval(0, 3)
        self._next_start = 3
        
        self._all_filtered_samples = zeros([self.num_of_channels,3], dtype=float128)
        
        #for channel in range(0,self.num_of_channels):
        channel = 0
        filter = self.cochlear_channels[channel]
        
        print filter
        
        a0 = filter[0][0]; a1 = filter[0][1]; a2 = filter[0][2]
        b1 = filter[1][1]; b2 = filter[1][2]
    
        self._all_filtered_samples[channel][0] = a0*interval_samples[0]
        
        self._all_filtered_samples[channel][1] = a0*interval_samples[1] +\
            a1*interval_samples[0] - b1*self._all_filtered_samples[channel][0]
            
        self._all_filtered_samples[channel][2] = a0*interval_samples[2] +\
            a1*interval_samples[1] - b1*self._all_filtered_samples[channel][1] +\
            a2*interval_samples[0] - b2*self._all_filtered_samples[channel][0]
                                
    def __call__(self, **params_to_override):
        if self._first_run:
            self._onFirstRun(ParamOverrides(self, params_to_override))
        
        else:
            current_interval_samples = self.signal.extractSpecificInterval(self._next_start, self._next_start+3)
            self._next_start = self._next_start + 3
            
            filtered_samples = zeros([self.num_of_channels,3], dtype=float128)            
            
            #for channel in range(0,self.num_of_channels):
            channel = 0

            filter = self.cochlear_channels[channel][0]
            
            a0 = filter[0][0]; a1 = filter[0][1]; a2 = filter[0][2]
            b1 = filter[1][1]; b2 = filter[1][2]
            
            filtered_samples[channel][0] = a0*current_interval_samples[0] +\
                a1*self.previous_interval_samples[-1] - b1*self._all_filtered_samples[channel][-1] +\
                a2*self.previous_interval_samples[-2] - b2*self._all_filtered_samples[channel][-2]            
            
            filtered_samples[channel][1] = a0*current_interval_samples[1] +\
                a1*current_interval_samples[0] - b1*filtered_samples[channel][0] +\
                a2*self.previous_interval_samples[-1] - b2*self._all_filtered_samples[channel][-1]     
                
            filtered_samples[channel][2] = a0*current_interval_samples[2] +\
                a1*current_interval_samples[1] - b1*filtered_samples[channel][1] +\
                a2*current_interval_samples[0] - b2*filtered_samples[channel][0]     
                                
            self._all_filtered_samples = hstack((fliplr(filtered_samples), fliplr(self._all_filtered_samples)))

        empty_columns = self.sheet_dimensions[1] - shape(self._all_filtered_samples)[1]
        if empty_columns > 0:
            self._all_filtered_samples = hstack((self._all_filtered_samples, zeros([self.num_of_channels,empty_columns])))
        else:
            self._all_filtered_samples = self._all_filtered_samples[0:, 0:self._all_filtered_samples.shape[1]-3]        
        
        return self._all_filtered_samples
        
        
class Cochleogram(LyonsCochlearModel):
    """
    Employs Lyons Cochlear Model to return a Cochleoogram, 
    i.e. the response over time along the cochlea.
    """
            
    def __init__(self, **params):
        super(Cochleogram, self).__init__(**params)

    def _onFirstRun(self, **overrides):
        super(Cochleogram, self)._onFirstRun(**overrides)

        self.cochleogram = zeros(self.sheet_dimensions)

    def __call__(self, **params_to_override):
        overrides = ParamOverrides(self, params_to_override)
         
        if self._first_run:
            self._onFirstRun(overrides)
            
        amplitudes = self._getAmplitudes()
        
        assert shape(amplitudes)[0] == shape(self.cochleogram)[0]
        self.cochleogram = hstack((amplitudes, self.cochleogram))
        
        # knock off eldest information, i.e. right-most column.
        self.cochleogram = self.cochleogram[0:, 0:self.cochleogram.shape[1]-1]        
        return self.cochleogram
        
        
if __name__=='__main__' or __name__=='__mynamespace__':

    from topo import sheet
    import topo

    topo.sim['C']=sheet.GeneratorSheet(
        input_generator=AudioFile(filename='sounds/complex/daisy.wav',sample_window=0.3,
            seconds_per_timestep=0.3,min_frequency=20,max_frequency=20000),
            nominal_bounds=sheet.BoundingBox(points=((-0.1,-0.5),(0.0,0.5))),
            nominal_density=10,period=1.0,phase=0.05)
