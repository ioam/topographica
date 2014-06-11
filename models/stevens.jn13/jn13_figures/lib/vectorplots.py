"""
Vectorplots

Utilities for generating vector images with matplotlib and numpy. Used
to generate overlays showing pinwheel locations, scale bars,
histograms, "stream plots" and other vector assets.
"""

import math, json
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from analysis import KaschubeFit

#==============================================#
# Overlays for OR maps and FFTs (subplots D-F) #
#==============================================#

def pinwheel_overlay(pinwheels, contours=None, style='wo',linewidth=1):
   """
   Plots the pinwheel locations and optionally the real and imaginary
   pinwheel contours. Designed to be overlayed over an OR map.
   """
   fig = plt.figure(frameon=False)
   fig.patch.set_alpha(0.0)
   ax = plt.subplot(111, aspect='equal', frameon=True)
   ax.patch.set_alpha(0.0)
   plt.hold(True)

   (recontours, imcontours) = contours if contours else ([],[])
   for recontour in recontours:
      plt.plot(recontour[:,0], recontour[:,1],'k',linewidth=linewidth)
   for imcontour in imcontours:
      plt.plot(imcontour[:,0], imcontour[:,1],'w', linewidth=linewidth)

   Xs, Ys = zip(*pinwheels)
   plt.plot(np.array(Xs), np.array(Ys), style)

   plt.xlim((0.0,1.0));         plt.ylim((0.0,1.0))
   ax.xaxis.set_ticks([]);      ax.yaxis.set_ticks([])
   ax.xaxis.set_ticklabels([]); ax.yaxis.set_ticklabels([])
   return fig


def scale_bar_overlay(normalized_width, aspect=0.05, color='w'):
   """
   Overlay that generates a scalebar with the given normalized width.
   """
   fig = plt.figure()
   ax = fig.add_subplot(111, aspect=aspect)
   ax.patch.set_alpha(0.0)
   ax.get_xaxis().set_visible(False)
   ax.get_yaxis().set_visible(False)
   [spine.set_visible(False) for spine in ax.spines.values()]
   if (0.5>normalized_width>0):
       ax.add_patch(plt.Rectangle((0,0), width=normalized_width,
                                  height=1.0, facecolor=color))
   return fig

def scale_box_overlay(normalized_width, offset = (0.1,0.195), color='w'):

    """
    Overlay that generates a scalebox with the given normalized width.
    """
    fig = plt.figure(frameon=False)
    ax = fig.add_subplot(111)
    ax.set_aspect('equal')
    ax.add_patch(plt.Rectangle(offset,normalized_width, normalized_width,
                               facecolor=(0,0,0,0), edgecolor=color, lw=5))

    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    [spine.set_visible(False) for spine in ax.spines.values()]
    plt.ylim((0,1)); plt.xlim((0,1))
    return fig


def FFT_histogram_overlay(amplitudes, fit, fit_function = KaschubeFit,
                          ylimit = 0.8, bar_color = (0.0, 0.35,0.0),
                          arrow_color = (0.0,0.0,0.5)):
   """
   Intended for generating FFT histograms.
   """
   fig = plt.figure(frameon=False)
   fig.patch.set_alpha(0.0)
   ax = fig.add_subplot(111)
   ax.patch.set_alpha(0.0)
   # Hide the plot spines
   [spine.set_visible(False) for spine in ax.spines.values()]
   ax.get_xaxis().set_visible(False)
   ax.get_yaxis().set_visible(False)
   try:
      bins = range(len(amplitudes))
   except:
      print "Invalid list of amplitudes"
      return fig

   light_blue =(0.75, 0.75, 1.0)
   bars = plt.bar(bins, amplitudes, facecolor='w',
                  edgecolor=bar_color,  width=1.0, lw=2)

   kmax = None
   if fit is not None:
      xs = np.linspace(1, len(amplitudes), 100) # From 0 for DC
      fit_curve = list(fit_function(x, **fit) for x in xs)
      plt.plot(xs, fit_curve, color='r', lw=8, alpha=0.7)
      kmax = fit['a1']

   if (kmax is not None) and (kmax >=1.5):
       plt.arrow(kmax, max(fit_curve)+ 0.38, 0.0, -0.3,
                 fc=arrow_color, ec=arrow_color,lw=6,
                 length_includes_head=True,
                 head_width=4.0, head_length=0.1)

   plt.xlim((0.0,len(amplitudes)))
   plt.ylim((0.0, ylimit))
   return fig

#=============================================#
# 'Stream' plots for contrast and development #
#=============================================#

def stream(xvals, samples, normalization=1.0, show_std=False,
           fillcolor=(1,0,0), linecolor=(1,0,0)):
   """
   Given a list of samples (also lists) which may be empty, computes
   the mean and 95% confidence interval (and optionally standard
   deviation) of each group of values and plots a 'stream'. This is a
   line representing the mean value flanked by a shaded area that
   represents the 95% confidence interval. If show_std is True, also
   shows the normal standard deviation as a dashed line.

   Note that the 0.96*standard error (95% confidence) lines are
   plotted according to the standard error which make use of the
   sample counts. Retuns (xinds, mean, conf95, std)
   """
   # Cannot take mean or std of empty lists - filter first
   xs,filtered =  zip(*[(x,grp) for (x,grp)
                        in zip(xvals,samples) if (grp != [])])
   # Normalize to given normalization constant
   normed = [[el/normalization for el in grp] for grp in filtered]
   # Means of the normalized sample groups
   mean = np.array([np.mean(grp) for grp in normed])
   # Standard deviation of the normalized sample groups
   std = [np.std(grp) for grp in normed]
   # Standard error is std / (num samples)**0.5
   std_error = [(np.std(grp)/ len(grp)**0.5) for grp in normed]
   # 95% confidence interval is std_error multiplied by 1.95996
   conf95 = [1.95996 * std_err for std_err in std_error]

   # Plot the mean line
   plt.plot(xs,mean,color=linecolor)
   # Plot the fill area (95% confidence area)
   plt.fill_between(xs,
                    mean+np.array(conf95),
                    mean-np.array(conf95),
                    interpolate=True, color=fillcolor)
   # If show_std, plot the standard deviation as a dashed line.
   if show_std:
      plt.plot(xs, mean-np.array(std), color=(r,g,b), linestyle='--')
      plt.plot(xs, mean+np.array(std), color=(r,g,b), linestyle='--')

   return xs, mean, np.array(std), np.array(conf95)


def map_development_plot(stabilities, selectivities, selectivity_norm,
                         figsize=(5.40212, 2), frame=False, spines=True):
   fig = plt.figure(frameon=frame, figsize=figsize)
   fig.patch.set_alpha(0.0)
   ax = fig.add_subplot(111)
   ax.patch.set_alpha(0.0)
   if not frame:
      ax.get_xaxis().set_visible(False)
      ax.get_yaxis().set_visible(False)

   if not spines: [spine.set_visible(False) for spine in ax.spines.values()]

   xs = range(len(stabilities))
   selectivity_norms = [sel/selectivity_norm for sel in selectivities]
   plt.plot(xs, stabilities, '-bo', lw=2,  markersize=8)
   plt.plot(xs, selectivity_norms, '-rs', lw=2,  markersize=8)
   plt.ylim((0.0,1.0))
   plt.xlim((0.0, max(xs)))
   return fig

def map_development_streams(stabilities, selectivities, selectivity_norm,
                            figsize=(5.40212, 2), frame=False, spines=True,
                            day_count=None):
   """
   Plots selectivity and stability over simulated or real animal
   development. The input stability and selectivity values may be
   supplied as a numpy array of shape (trials x time samples) when the
   trial number is constant. Alternatively, a list of lists may be
   supplied where the list elements hold the samples at a given time
   point (regularly sampled) with empty lists marking missing data.
   """

   if isinstance(stabilities, np.ndarray):
      stabilities = stabilities.transpose().tolist()

   if isinstance(selectivities, np.ndarray):
      selectivities = selectivities.transpose().tolist()

   assert len(selectivities) == len(stabilities)
   xvals = range(len(stabilities))

   fig = plt.figure(frameon=frame, figsize=figsize)
   fig.patch.set_alpha(0.0)
   ax = fig.add_subplot(111)
   ax.patch.set_alpha(0.0)
   if not frame:
      ax.get_xaxis().set_visible(False)
      ax.get_yaxis().set_visible(False)
   if not spines: [spine.set_visible(False) for spine in ax.spines.values()]
   # Plotting the 'streams'
   stab_xs,_,_,_ = stream(xvals, stabilities,
                          fillcolor='#ccccff',linecolor=(0,0,1))
   sel_xs,_,_,_ = stream(xvals, selectivities,
                         normalization=selectivity_norm,
                         fillcolor='#ffcfcf',linecolor=(1,0,0))
   # Setting the plot limits and returning the figure
   plt.ylim((0.0,1.0))
   if day_count: plt.xlim((0.0, day_count-1))
   else:         plt.xlim((0.0, max(sel_xs+stab_xs)))
   return fig


def contrast_streams(contrasts, selectivities, stabilities, metrics, vlines=[]):
   """
   The plots showing selectivity and stability against scale
   (contrast).  The inputs are numpy arrays of shape (seeds x
   contrasts).
   """
   # List of list formats for use with stream plots.
   stabilities = stabilities.transpose().tolist()
   selectivities = selectivities.transpose().tolist()
   metrics = metrics.transpose().tolist()

   fig = plt.figure(frameon=False)
   ax = fig.add_subplot(111, frameon=False)
   stream(contrasts, selectivities, fillcolor='#ffcfcf', linecolor=(1,0,0))
   stream(contrasts, stabilities,   fillcolor='#ccccff', linecolor=(0,0,1))
   stream(contrasts, metrics,       fillcolor='#ccffcc', linecolor=(0,1,0))
   [spine.set_visible(False) for spine in ax.spines.values()]
   ax.get_xaxis().set_visible(False)
   ax.get_yaxis().set_visible(False)
   plt.xlim((0.0,max(contrasts)))
   plt.ylim((-0.1,1.1))
   for vl in vlines:
      plt.axvline(x=vl, linewidth=1, color='r', linestyle='--')
   return fig


#===================#
# Figure 3 (Metric) #
#===================#

def animal_scatterplot(json_filename, lw=3, s=60, hline_width=0.16):
   """
   Reproduces the animal data from Kaschube et al. 2010 as a scatter
   plot in a similar style. One key difference is that the area of the
   markers no longer signifies anything.
   """
   fig = plt.figure(figsize=(8,6))
   ax = plt.subplot(111)
   plt.axhline(y=math.pi, linestyle='dotted')
   d = json.load(open(json_filename,'r'))['Kaschube 2010']

   animals = ('Ferret','Tree shrew','Galago')
   colors = ('#27833a','#7fcbf1', '#f9ab27')
   for (animal, color) in zip(animals,colors):
      point_kws = dict(edgecolor=color, marker='D', facecolor=(0,0,0,0))
      plt.scatter(d[animal]['x'], d[animal]['y'], s=s, lw=lw, **point_kws)
      medx = np.median(d[animal]['x'])
      medy = np.median(d[animal]['y'])
      hline_kws = dict(colors=color, linestyles='solid', lw=lw)
      plt.hlines(medy, medx-hline_width, medx+hline_width, **hline_kws)

   ax.get_xaxis().set_visible(False)
   ax.get_yaxis().set_visible(False)
   [spine.set_visible(False) for spine in ax.spines.values()]
   plt.ylim((0, 12)); plt.xlim((0, 1.1))
   return fig


def model_scatterplot(iterables, colors=['r','b'],
                      mean_mm2_ferret=0.75,
                      lw=3, s=60, hline_width=0.16):
   """
   Scatterplot of simulation data for the GCAL and L models to overlay
   over the animal data. The two iterables are to contain zipped kmax
   and pinwheel densities.

   mean_mm2_ferret - mean hypercolumn size in millimeters squared
                     Sets a value for the models (uncalibrated).
   """
   fig = plt.figure(figsize=(8,6))
   ax = plt.subplot(111)
   plt.axhline(y=math.pi, linestyle='dotted')

   for iterable, color in zip(iterables, colors):
      units_per_hc, pw_densities = zip(*iterable)
      units_per_hc2 = np.array(units_per_hc)**2

      # Center both clusters on the given mean hypercolumn size for ferret.
      HCmm2 = units_per_hc2 * (mean_mm2_ferret / units_per_hc2.mean())
      point_kws = dict(edgecolor=color, marker='o', facecolor=(0,0,0,0))
      plt.scatter(HCmm2, pw_densities, s=s,lw=lw, **point_kws)

      medx = np.median(pw_densities); medy = np.median(HCmm2)
      hline_kws = dict(colors=color, linestyles='solid', lw=lw)
      plt.hlines(medy, medx-hline_width, medx+hline_width, **hline_kws)

   ax.get_xaxis().set_visible(False)
   ax.get_yaxis().set_visible(False)
   [spine.set_visible(False) for spine in ax.spines.values()]
   plt.ylim((0, 12)); plt.xlim((0, 1.1))
   return fig


#
# Tanaka histograms
#

def tanaka_histogram(data, bins=7, aspect=0.78):
    """
    Generates an orientation histogram in the style of Tanaka 2009.

    If data is the string 'biased' or 'unbiased', replicates the
    corresponding data shown in Tanaka et al 2009. The unbiased data
    replots their figure 1e while the unbiased data replots their
    figure 2a. Otherwise, data should be an orientation preference
    map.
    """
    # Relative height of histogram bars (figures 1e and 2a)
    replot_data = {'biased':[3, 5.5, 11, 57,  14, 6, 3.5],
                   'unbiased':[12, 15.5, 19, 17, 13, 11.5, 12]}
    replot = isinstance(data, str)

    if replot:
       counts = replot_data[data]
       data = np.linspace(0.0,1.0,100)
    else:
       # Use numpy.histogram to compute bar heights for the array
       interval_30deg = 1.0 / 6.0
       lower_bound = (interval_30deg / 2.0)
       upper_bound = 1.0 - (interval_30deg / 2.0)
       data_counts, _ = np.histogram(data, bins=5,
                                     range=(lower_bound, upper_bound),
                                     density=False)
       # The style of histogram in tanaka et al includes a repeated bar
       repeated_bar = sum((data.flatten() < lower_bound) ^ (data.flatten() > upper_bound))
       assert (data_counts.sum() + repeated_bar) == data.shape[0]*data.shape[1]
       data_counts = [repeated_bar] + data_counts.tolist() + [repeated_bar]
       sum_counts = sum(data_counts[:-1])

    # Use numpy.histogram again to find the bin edges
    _ , bin_edges = np.histogram(data, bins=bins, range=(0.0,1.0))

    # Using matplotlib's bar plot to build the histogram.
    fig = plt.figure()
    ax = plt.subplot(111, frameon=True)
    bars = plt.bar(bin_edges[:-1], counts if replot else data_counts,
                   width=0.8/bins, color='k')

    # Show the hline for equi-orientation distribution
    if replot: plt.axhline(100 / 7.0, lw=2)
    else:      plt.axhline(sum_counts/6.0, lw=2)

    # Set the xlim and ylim (ylim=100 if replotting data)
    plt.xlim((-0.05,1.05))
    x_range = 1.05 + 0.05
    ylim = 100 if replot else sum_counts
    plt.ylim((0.0,ylim))

    for axis in [ax.xaxis, ax.yaxis]:
       axis.set_ticks([])
       axis.set_ticklabels([])

    ax.set_aspect((x_range / 100.0 if replot
                   else float(x_range) / sum_counts) * aspect)
    return fig



class TuningCurvePlot(object):
    """
    Custom plot type to supply to pylabplot.cyclic_unit_tuning_curve.
    Plots orientation tuning curves in either in the usual fashion or
    in a normalized style (all vertically scaled to the same height)
    """

    def __init__(self, normalize, axes=False, count=8,
                 colors=['b', '#ff9500', 'ff9500', 'c', 'm', 'y', 'g', 'r']):
        matplotlib.rcParams['axes.color_cycle'] = colors
        self.normalize = normalize
        self.axes = axes
        self.count = count
        self.accumulator = []

    def __call__(self, x_values, y_values, label, lw):
        if len(self.accumulator) != self.count:
            self.accumulator.append((label, x_values, y_values))
        if len(self.accumulator)== self.count:
            plt.title('')
            ax = plt.gca()
            plt.gcf().set_size_inches(8,6 )

            for label, x_vals, y_vals in self.accumulator[::-1]:
                if self.normalize:  self.plot_normalized(x_vals, y_vals, label, lw)
                else:               self.plot_unnormalized(x_vals, y_vals, label, lw)

            if not self.axes:
                ax.get_xaxis().set_visible(False)
                ax.get_yaxis().set_visible(False)
                plt.xlabel('');  plt.ylabel('')

            plt.ylim((0.0,1.0)) if self.normalize else plt.ylim((0.0,0.8))
            plt.draw()

    def plot_normalized(self,x_values, y_values, label, lw):
        if max(y_values) == 0: return
        normalized = [yval / max(y_values) for yval in y_values]
        plt.plot(x_values, normalized, label=label,lw=lw, color='k')

    def plot_unnormalized(self,x_values, y_values, label, lw):
        plt.plot(x_values, y_values, label=label, lw=lw)


def tuning_curve_plot(tuning_curves, coord, legend=False, normalize=False):
    """
    To reproduce the tuning curve figure exactly, please checkout the following:

    Topographica: 37a7113   measure_or_tuning can no longer be imported from
                            command.pylabplot

    Imagen:       fec785e   Updated ProjectionGrid methods

    In later versions of Topographica, tuning curves may still be plotted using
    the FeatureMapper and DataView packages, or using the backward compatibility
    method command.pylabplot.tuning_curve.
    """
    from topo.command.pylabplot import cyclic_unit_tuning_curve
    return cyclic_unit_tuning_curve(tuning_curves, coord=coord,
                                    legend=legend, center=False,
                                    plot_type=TuningCurvePlot(normalize=normalize))


def close(figs):
   """
   Closes a list of figure handles.
   """
   for f in figs: plt.close(f)
