"""
Pattern generators for audio signals.

$Id$
"""
__version__='$Revision$'


import param
import os

from topo.pattern.basic import TimeSeries, Spectrogram, PowerSpectrum
from topo import transferfn

from numpy import arange, array, ceil, complex64, concatenate, cos, exp, fft, flipud, float64, floor, hanning, hstack, log, log2, log10, \
    logspace, multiply, nonzero, ones, pi, repeat, reshape, shape, size, sqrt, sum, tile, where, zeros
    
try:
    import scikits.audiolab as audiolab

except ImportError:
    param.Parameterized().warning("audio.py classes will not be usable because scikits.audiolab is not available.")
     

        
class AudioFile(TimeSeries):
    """
    Requires an audio file in any format accepted by audiolab (wav, aiff, flac).
    """
        
    time_series = param.Array(precedence=(-1))
    sample_rate = param.Number(precedence=(-1))
    
    filename = param.Filename(default='sounds/complex/daisy.wav', doc="""
        File path (can be relative to Topographica's base path) to an audio file. 
        The audio can be in any format accepted by audiolab, e.g. WAV, AIFF, or FLAC.""")
    
    precision = param.Parameter(default=float64, doc="""
        The float precision to use for loaded audio files.""")
         
               
    def __init__(self, **params):
        super(AudioFile, self).__init__(**params)
        self._load_audio_file()


    def _load_audio_file(self):
        source = audiolab.Sndfile(self.filename, 'r')
        
        # audiolab scales the range by the bit depth automatically so the dynamic range is now [-1.0, 1.0]
        # we rescale it to the range [0.0, 1.0]
        self.time_series = (source.read_frames(source.nframes, dtype=self.precision) + 1) / 2
        self.sample_rate = source.samplerate



class AudioFolder(AudioFile):
    """
    Returns a rolling spectrogram, i.e. the spectral density over time 
    of a rolling window of the input audio signal, for all files in the 
    specified folder.
    """
    
    filename = param.Filename(precedence=(-1))

    folderpath = param.Foldername(default='sounds/sine_waves/normalized', 
        doc="""Folder path (can be relative to Topographica's base path) to a
        folder containing audio files. The audio can be in any format accepted 
        by audiolab, i.e. WAV, AIFF, or FLAC.""")
         
    gap_between_sounds = param.Number(default=0.0, bounds=(0.0,None),
        doc="""The gap in seconds to insert between consecutive soundfiles.""")
      
                            
    def __init__(self, **params):
        super(AudioFolder, self).__init__(**params)
        self._load_audio_folder()
                
                
    def _load_audio_folder(self):
        folder_contents = os.listdir(self.folderpath)
        self.sound_files = []
        
        for file in folder_contents:
            if file[-4:]==".wav" or file[-3:]==".wv" or file[-5:]==".aiff" or file[-4:]==".aif" or file[-5:]==".flac":
                self.sound_files.append(self.folderpath + "/" + file) 

        self.filename=self.sound_files[0]
        self._load_audio_file()
        self.next_file = 1


    def extract_specific_interval(self, interval_start, interval_end):
        """
        Overload if special behaviour is required when a series ends.
        """
        
        interval_start = int(interval_start)
        interval_end = int(interval_end)
        
        if interval_start >= interval_end:
            raise ValueError("Requested interval's start point is past the requested end point.")
        
        elif interval_start > self.time_series.size:
            if self.repeat:
                interval_end = interval_end - interval_start
                interval_start = 0                
            else:
                raise ValueError("Requested interval's start point is past the end of the time series.")
            
        if interval_end < self.time_series.size:
            interval = self.time_series[interval_start:interval_end]
            
        else:
            requested_interval_size = interval_end - interval_start
            remaining_signal = self.time_series[interval_start:self.time_series.size]

            if self.next_file == len(self.sound_files) and self.repeat:
                self.next_file = 0
            
            if self.next_file < len(self.sound_files):
                next_source = audiolab.Sndfile(self.sound_files[self.next_file], 'r')
                self.next_file += 1
                   
                if next_source.samplerate != self.sample_rate:
                    raise ValueError("All sound files must be of the same sample rate")        
                
                if self.gap_between_sounds > 0:
                    remaining_signal = hstack((remaining_signal, zeros(int(self.gap_between_sounds*self.sample_rate), dtype=self.precision)))
                
                self.time_series = hstack((remaining_signal, next_source.read_frames(next_source.nframes, dtype=self.precision)))
                                
                interval = self.time_series[0:requested_interval_size]
                self._next_interval_start = requested_interval_size

            else:
                self.warning("Returning last interval of the time series.")
                self._next_interval_start = self.time_series.size + 1

                samples_per_interval = self.interval_length*self.sample_rate
                interval = hstack((remaining_signal, zeros(samples_per_interval-remaining_signal.size)))
                    
        return interval



def convert_to_decibels(amplitudes):
    amplitudes[amplitudes==0] = 1.0
    return 20.0 * log10(abs(amplitudes))


        
class DecibelSpectrogram(Spectrogram):
    """
    Extends Spectrogram to provide a response in decibels over a base 10 logarithmic scale.
    """
        
    def _set_frequency_spacing(self, min_freq, max_freq):
        self.frequency_spacing = logspace(log10(min_freq+1), log10(max_freq), num=self._sheet_dimensions[0]+1, endpoint=True, base=10)
        

    def _shape_response(self, new_column):
        new_column_in_db = convert_to_decibels(new_column)
        return super(DecibelSpectrogram, self)._shape_response(new_column_in_db)



class CochlearSpectrogram(Spectrogram):
    """
    Extends Spectrogram to provide a response over an octave scale.
    """

    def _get_row_amplitudes(self):
        signal_interval = self.signal()
        sample_rate = self.signal.sample_rate        

        # A signal window *must* span one sample rate
        signal_window = tile(signal_interval, ceil(1.0/self.signal.interval_length))

        if self.windowing_function:
            smoothed_window = signal_window[0:sample_rate] * self.windowing_function(sample_rate)  
        else:
            smoothed_window = signal_window[0:sample_rate]
        
        amplitudes = (abs(fft.rfft(smoothed_window))[0:sample_rate/2] + self.offset) * self.scale
        
        for index in range(0, self._sheet_dimensions[0]-2):
            start_frequency = self.frequency_spacing[index]
            end_frequency = self.frequency_spacing[index+1]
             
            normalisation_factor = nonzero(amplitudes[start_frequency:end_frequency])[0].size            
            if normalisation_factor == 0:
                amplitudes[index] = 0
            else:
                amplitudes[index] = sum(amplitudes[start_frequency:end_frequency]) / normalisation_factor
        
        return flipud(amplitudes[0:self._sheet_dimensions[0]].reshape(-1,1))
        
    
    def _set_frequency_spacing(self, min_freq, max_freq):
        self.frequency_spacing = logspace(log2(min_freq+1), log2(max_freq), num=self._sheet_dimensions[0]+1, endpoint=True, base=2)



class CochlearSpectrogramWithAmplification(CochlearSpectrogram):
    """
    Extends OctaveSpectrogram with a simple model of outer ear amplification. 
    One can set both the range to amplify and the amount.
    """
        
    amplify_from_frequency=param.Number(default=1000.0, bounds=(0.0,None),
        doc="""The lower bound of the frequency range to be amplified.""")

    amplify_till_frequency=param.Number(default=7000.0, bounds=(0.0,None),
        doc="""The upper bound of the frequency range to be amplified.""")
    
    amplify_by_percentage=param.Number(default=15.0, bounds=(0.0,None),
        doc="""The percentage by which to amplify the signal between the 
        specified frequency range.""")
        
        
    def __init__(self, **params):
        super(CochlearSpectrogramWithAmplification, self).__init__(**params)
            
        if self.amplify_from_frequency > self.amplify_till_frequency:
            raise ValueError("Amplify from frequency must be less than its amplify till frequency.")
        

    def set_matrix_dimensions(self, bounds, xdensity, ydensity):
        super(CochlearSpectrogramWithAmplification, self).set_matrix_dimensions(bounds, xdensity, ydensity)

        self._amplify_start_index = nonzero(self.frequency_spacing >= self.amplify_from_frequency)[0][0]
        self._amplify_end_index = nonzero(self.frequency_spacing >= self.amplify_till_frequency)[0][0]
        
        self._amplifications = (hanning(self._amplify_end_index-self._amplify_start_index) * (self.amplify_by_percentage/100.0)) + 1.0
        self._amplifications = reshape(self._amplifications, [-1,1])


    def _shape_response(self, new_column):
        if self.amplify_by_percentage > 0:
            if (self.amplify_from_frequency < self.min_frequency) or (self.amplify_from_frequency > self.max_frequency):
                raise ValueError("Lower bound of frequency to amplify is outside the global frequency range.")
 
            elif (self.amplify_till_frequency < self.min_frequency) or (self.amplify_till_frequency > self.max_frequency):
                raise ValueError("Upper bound of frequency to amplify is outside the global frequency range.")
            
            else:
                new_column[self._amplify_start_index:self._amplify_end_index] *= self._amplifications

        return super(CochlearSpectrogramWithAmplification, self)._shape_response(new_column)
        


class LyonsCochlearModel(PowerSpectrum):
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
    
    signal = param.Parameter(default=None, doc="""
        A TimeSeries object to be fed to the model.
        
        This can be any kind of signal, be it from audio files or live
        from a mic, as long as the values conform to a TimeSeries.
        """)
    
    quality_factor = param.Number(default=8.0, doc="""
        Quality factor controls the bandwidth of each cochlear filter.
        
        The bandwidth of each cochlear filter is a function of its 
        center frequency. At high frequencies the bandwidth is 
        approximately equal to the center frequency divided by a 
        quality constant (quality_factor). At lower frequncies the 
        bandwidth approaches a constant given by: 1000/quality_factor.
        """)
    
    stage_overlap_factor = param.Number(default=4.0, doc="""
        The degree of overlap between filters.
    
        Successive filter stages are overlapped by a fraction of their 
        bandwidth. The number is arbitrary but smaller numbers lead to 
        more computations. We currently overlap 4 stages within the 
        bandpass region of any one filter.
        """)
                
    precision = param.Parameter(default=float64, doc="""
        The float precision to use when calculating ear stage filters.""")
    
    
    def __init__(self, **params):
        super(LyonsCochlearModel, self).__init__(**params)

        # Hardwired Parameters specific to model, which is to say changing
        # them without knowledge of the mathematics of the model is a bad idea.
        self.sample_rate = self.signal.sample_rate
        self.half_sample_rate = float(self.sample_rate/2.0)
        self.quart_sample_rate = float(self.half_sample_rate/2.0)
 
        self.ear_q = float(self.quality_factor)
        self.ear_step_factor = float(1.0/self.stage_overlap_factor)

        self.ear_break_f = float(1000.0)
        self.ear_break_squared = self.ear_break_f*self.ear_break_f

        self.ear_preemph_corner_f = float(300.0)
        self.ear_zero_offset = float(1.5)
        self.ear_sharpness = float(5.0)
        
        self._num_of_channels = self._num_of_channels()
        self._generateCochlearFilters()
    
    
    def _ear_bandwidth(self, cf):
        return sqrt(cf*cf + self.ear_break_squared) / self.ear_q
        
        
    def _max_frequency(self):
        bandwidth_step_max_f = self._ear_bandwidth(self.half_sample_rate) * self.ear_step_factor    
        return self.half_sample_rate + bandwidth_step_max_f - bandwidth_step_max_f*self.ear_zero_offset


    def _num_of_channels(self):
        min_f = self.ear_break_f / sqrt(4.0*self.ear_q*self.ear_q - 1.0)
        channels = log(self.max_f_calc) - log(min_f + sqrt(min_f*min_f + self.ear_break_squared))
        
        return int(floor(self.ear_q*channels/self.ear_step_factor))


    def _calc_centre_frequencies_till(self, channel_index):
        if (self.centre_frequencies[channel_index] > 0):
            return self.centre_frequencies[channel_index]
        else:
            step = self._calc_centre_frequencies_till(channel_index-1)
            channel_cf = step - self.ear_step_factor*self._ear_bandwidth(step)
            self.centre_frequencies[channel_index] = channel_cf
            
            return channel_cf


    def _evaluate_filters_for_frequencies(self, filters, frequencies):
        Zs = exp(2j*pi*frequencies/self.sample_rate)
        Z_squareds = Zs * Zs
        
        zeros = ones((shape(frequencies)[0], shape(filters[0])[0], 3), dtype=complex64)
        zeros[:,:,2] = filters[0][:,2] * Z_squareds
        zeros[:,:,1] = filters[0][:,1] * Zs
        zeros[:,:,0] = filters[0][:,0]
        zeros = sum(zeros, axis=2)

        poles = ones((shape(frequencies)[0], shape(filters[1])[0], 3), dtype=complex64)
        poles[:,:,2] = filters[1][:,2] * Z_squareds
        poles[:,:,1] = filters[1][:,1] * Zs
        poles[:,:,0] = filters[1][:,0]
        poles = sum(poles, axis=2)
        
        return zeros / poles
        
        
    # a frequency and gain are specified so that the resulting filter can 
    # be normalized to have any desired gain at a specified frequency.
    def _make_filters(self, zeros, poles, f, desired_gains):  
        desired_gains = reshape(desired_gains,[size(desired_gains),1])
        
        unit_gains = self._evaluate_filters_for_frequencies([zeros,poles], f)
        unit_gains = reshape(unit_gains,[size(unit_gains),1])
        
        return [zeros*desired_gains, poles*unit_gains]
        
        
    def _frequency_responses(self, evaluated_filters):
        evaluated_filters[evaluated_filters==0] = 1.0
        return 20.0 * log10(abs(evaluated_filters))


    def _specific_filter(self, x2_coefficient, x_coefficient, constant):  
        return array([[x2_coefficient,x_coefficient,constant], ], dtype=self.precision)
            
            
    def _first_order_filter_from_corner(self, corner_f):
        polynomial = zeros((1,3), dtype=self.precision)
        polynomial[:,0] = -exp(-2.0*pi*corner_f/self.sample_rate)
        polynomial[:,1] = 1.0

        return polynomial


    def _second_order_filter_from_center_q(self, cf, quality):
        cf_as_ratio = cf/self.sample_rate
        
        rho = exp(-pi*cf_as_ratio/quality)
        rho_squared = rho*rho
        
        theta = 2.0*pi*cf_as_ratio * sqrt(1.0-1.0/(4.0*quality*quality))
        theta_calc = -2.0*rho*cos(theta)
        
        polynomial = ones((size(cf),3), dtype=self.precision)
        polynomial[:,1] = theta_calc
        polynomial[:,2] = rho_squared
        
        return polynomial
     
     
    def _ear_filter_gains(self):
        return self.centre_frequencies[:-1] / self.centre_frequencies[1:]


    def _ear_first_stage(self):    
        outer_middle_ear_filter = self._make_filters(self._first_order_filter_from_corner(self.ear_preemph_corner_f), 
            self._specific_filter(1.0,0.0,0.0), array([0.0]), 1.0)

        high_freq_compensator = self._make_filters(self._specific_filter(1.0,0.0,-1.0), self._specific_filter(0.0,0.0,1.0), 
            array([self.quart_sample_rate]), 1.0)
        
        pole_pair = self._make_filters(self._specific_filter(0.0,0.0,1.0), 
            self._second_order_filter_from_center_q(self.cascade_pole_cfs[0],self.cascade_pole_qs[0]), 
            array([self.quart_sample_rate]), 1.0)
        
        outer_middle_ear_evaluations = self._evaluate_filters_for_frequencies(outer_middle_ear_filter, self.frequencies)
        high_freq_compensator_evaluations = self._evaluate_filters_for_frequencies(high_freq_compensator, self.frequencies)
        pole_pair_evaluations = self._evaluate_filters_for_frequencies(pole_pair, self.frequencies)
        
        return outer_middle_ear_evaluations * high_freq_compensator_evaluations * pole_pair_evaluations


    def _ear_all_other_stages(self):
        zeros = self._second_order_filter_from_center_q(self.cascade_zero_cfs[1:], self.cascade_zero_qs[1:])
        poles = self._second_order_filter_from_center_q(self.cascade_pole_cfs[1:], self.cascade_pole_qs[1:])
        
        stage_filters = self._make_filters(zeros, poles, array([0.0]), self.ear_filter_gains)
        return self._evaluate_filters_for_frequencies(stage_filters, self.frequencies)


    def _generate_cascade_filters(self):
        cascade_filters = self.ear_stages
        
        for channel in range(1,self._num_of_channels):
            cascade_filters[channel,:] = cascade_filters[channel,:] * cascade_filters[channel-1,:]
        
        return self._frequency_responses(cascade_filters)
        
        
    def _generateCochlearFilters(self):
        max_f = self._max_frequency()
        self.max_f_calc = max_f + sqrt(max_f*max_f + self.ear_break_squared)

        self.centre_frequencies = zeros(self._num_of_channels, dtype=self.precision)
        self.centre_frequencies[0] = max_f
        self._calc_centre_frequencies_till(self._num_of_channels-1)

        bandwidths = self._ear_bandwidth(self.centre_frequencies)
        
        self.cascade_zero_cfs = self.centre_frequencies + bandwidths*self.ear_step_factor*self.ear_zero_offset
        self.cascade_zero_qs = self.ear_sharpness * self.cascade_zero_cfs / bandwidths
        self.cascade_pole_cfs = self.centre_frequencies
        self.cascade_pole_qs = self.centre_frequencies / bandwidths
        
        self.ear_filter_gains = self._ear_filter_gains()
        
        self.frequencies = arange(self.half_sample_rate).reshape(self.half_sample_rate, 1)
        
        self.ear_stages = hstack((self._ear_first_stage(), self._ear_all_other_stages())).transpose() 
        
        self.cochlear_channels = self._generate_cascade_filters()
        
        
    def _get_row_amplitudes(self):
        """
        Perform a real Discrete Fourier Transform (DFT; implemented
        using a Fast Fourier Transform algorithm, FFT) of the current
        sample from the signal multiplied by the smoothing window.

        See numpy.rfft for information about the Fourier transform.
        """
        
        sample_rate = self.signal.sample_rate        
        
        # A signal window *must* span one sample rate, irrespective of interval length.
        signal_window = tile(self.signal(), ceil(1.0/self.signal.interval_length))
        
        if self.windowing_function == None:
            smoothed_window = signal_window[0:sample_rate]
        else:
            smoothed_window = signal_window[0:sample_rate] * self.windowing_function(sample_rate)  
        
        row_amplitudes = abs(fft.rfft(smoothed_window))[0:sample_rate/2]
        row_amplitudes = row_amplitudes.reshape(1,sample_rate/2.0)
        
        filter_responses = multiply(self.cochlear_channels, row_amplitudes)
        sheet_responses = zeros(self._num_of_channels)
        
        for channel in range(0,self._num_of_channels):
            time_responses = abs(fft.ifft(filter_responses[channel]))
            sheet_responses[channel] = sum(time_responses) / (sample_rate/2.0)
        
        return sheet_responses.reshape(self._num_of_channels, 1)
          
              
    def set_matrix_dimensions(self, bounds, xdensity, ydensity):
        super(LyonsCochlearModel, self).set_matrix_dimensions(bounds, xdensity, ydensity)
        
        self._num_of_channels = self._num_of_channels()
        if self._sheet_dimensions[0] == self._num_of_channels:
            self._generateCochlearFilters()
        else:
            raise ValueError("The number of Sheet Rows must correspond to the number of Lyons Filters. Adjust the number sheet rows from [%s] to [%s]." %(self._sheet_dimensions[0], self._num_of_channels))
            
        
        
        
class LyonsCochleogram(LyonsCochlearModel):
    """
    Employs Lyons Cochlear Model to return a Cochleoogram, 
    i.e. the response over time along the cochlea.
    """
        
    def _update_cochleogram(self, new_column):
        self._cochleogram = hstack((new_column, self._cochleogram))
        self._cochleogram = self._cochleogram[0:, 0:self._sheet_dimensions[1]]
            
                    
    def set_matrix_dimensions(self, bounds, xdensity, ydensity):
        super(Cochleogram, self).set_matrix_dimensions(bounds, xdensity, ydensity)
        self._cochleogram = zeros(self._sheet_dimensions)


    def __call__(self, **params_to_override):
        self._update_cochleogram(self._get_row_amplitudes())
        return self._cochleogram           


        
        
if __name__=='__main__' or __name__=='__mynamespace__':

    from topo import sheet
    import topo

    topo.sim['C']=sheet.GeneratorSheet(
        input_generator=AudioFile(filename='sounds/complex/daisy.wav',sample_window=0.3,
            seconds_per_timestep=0.3,min_frequency=20,max_frequency=20000),
            nominal_bounds=sheet.BoundingBox(points=((-0.1,-0.5),(0.0,0.5))),
            nominal_density=10,period=1.0,phase=0.05)
