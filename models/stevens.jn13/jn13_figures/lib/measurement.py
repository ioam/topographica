"""
Measurement

Analysis functions that measure orientation maps and analyse them
within each running Topographica simulation. These functions return
dictionaries which allow the data to be collated by RunBatchCommand in
the Topographica Lancet extension (topo/misc/lancext.py).
"""

from topo.analysis.featureresponses import MeasureResponseCommand

import numpy as np
import math

import topo
from topo.transferfn.misc import PatternCombine
import analysis

# Set up appropriate defaults for analysis
import topo.analysis.featureresponses

# Figures 5-9, afferent response only

def OR_measurement(selectivity_multiplier, settings={}):
    """ Default scale is 0.3, not 1.0 (100% contrast)"""
    topo.analysis.featureresponses.FeatureMaps.selectivity_multiplier = selectivity_multiplier
    measurement = topo.command.analysis.measure_sine_pref(scale=1.0, **settings)
    sel = topo.sim.V1.views.maps.OrientationSelectivity.last
    pref = topo.sim.V1.views.maps.OrientationPreference.last
    return {'OrientationSelectivity':sel, 'OrientationPreference': pref,
            'metadata':{'mean_selectivity':sel.data.mean()}}

def ROI(disable=False):
    """
    In the paper, the cortical density is 98 with area 1.5, resulting
    in a 147x147 matrix. A central area cannot have exactly 1.0x1.0
    sheet coordinates - the roi slice returned is slightly larger.
    """
    if disable: return slice(None,None)
    # sheet2matrixidx returns off-center slice with even dimensions.
    (start_idx, stop_idx) = topo.sim.V1.sheet2matrixidx(0.5,0.5)
    return slice(start_idx, stop_idx+1) # Centered with odd dimensions.

def stability_analysis(figure, times):
    """
    Accumulates the preference maps over the course of the
    simulation. On the last iteration, computes the stabilities for
    all the accumulated maps and returns the stability values as
    metadata.
    """
    roi = ROI(disable=(True if figure=='Fig10_12' else False))
    simulation_time = topo.sim.time()
    preference = topo.sim.V1.views.maps.OrientationPreference.last.data
    preference = preference / topo.sim.V1.views.maps.OrientationPreference.last.cyclic_range
    if simulation_time == times[0]:
        topo.stability_maps = [preference[roi,roi]]
    if simulation_time == times[-1]:
        topo.stability_maps.append(preference[roi,roi])
        stabilities = analysis.stability_index(topo.stability_maps)
        return {'metadata':{'stabilities':stabilities}}
    else:
        topo.stability_maps.append(preference[roi,roi])

def pinwheel_analysis():
    """
    Computes the pinwheels analysis. Fits the hypercolumn distance to
    get the estimated value of kmax to compute the pinwheel density.
    """
    roi = ROI() # Central ROI (1.0 x 1.0 in sheet coordinates)
    preference = topo.sim.V1.views.maps.OrientationPreference.last.data
    preference = preference / topo.sim.V1.views.maps.OrientationPreference.last.cyclic_range
    polar_map = analysis.polar_preference(preference[roi,roi])
    contour_info = analysis.polarmap_contours(polar_map)
    (re_contours, im_contours, _ ) = contour_info
    pinwheels= analysis.identify_pinwheels(*contour_info)
    metadata = analysis.hypercolumn_distance(preference[roi,roi])
    metadata.update(rho = (len(pinwheels) / metadata['kmax']**2))
    return {'pinwheels':pinwheels,
            're_contours':re_contours,
            'im_contours':im_contours,
            'metadata': metadata}

def measure_FF():
    """
    Disables the lateral connectivity by measuring before settling and
    disable homeostatic adaptation (i.e. output functions).
    """
    ff_map_multiplier = 2.0
    measurement = OR_measurement(selectivity_multiplier=ff_map_multiplier,
                                 settings = dict(durations=[0.225],
                                                 apply_output_fns=False))
    measurement['metadata'].update(roi=ROI())
    return measurement

def measure_GR():
    full_map_multiplier = 0.2
    measurement = OR_measurement(selectivity_multiplier=full_map_multiplier)
    measurement['metadata'].update(roi=ROI())
    return measurement

def measure_shouval(times, num_orientation, num_phase):
    """
    Measures the map with settling and all output functions
    applied. This complete measurement protocol is only used with
    GCAL.

    The output function is needed to set the random state to reproduce
    the same noise.
    """
    full_map_multiplier = 0.2
    contrasts =  [{'contrast':c} for c in [1, 5, 10, 20, 40,60, 80, 100]]
    additive_noise = PatternCombine(generator=topo.pattern.random.UniformRandom(scale=0.0), operator=np.add)
    topo.sim.V1.output_fns.append(additive_noise)
    measurement = OR_measurement(selectivity_multiplier=full_map_multiplier)
    measurement['metadata'].update(roi=ROI(disable=True))
    topo.sim.V1.output_fns.pop()
    if topo.sim.time() == times[-1]:
        topo.command.analysis.measure_or_tuning_fullfield(num_orientation=num_orientation,
                                                          num_phase=num_phase,
                                                          curve_parameters=contrasts)
        measurement.update({'tuning_curves':topo.sim.V1.views.curves.Orientation.last})
    return measurement


def afferent_CFs(times):
    """
    Supplies the connection fields and their coordinates as numpy
    arrays in the format suitable for display with image.cf_image.

    Access cf idx using cfs[...,idx] and its [x,y] coordinates using
    coords[idx]. For a map from coordinates to CFs:

    tuple_coords = (tuple(c) for c in coords)
    cfgen = (cfs[:,:,i] for i in range(len(coords)))
    cf_map = dict(zip(tuple_coords,cfgen))
    """
    projection = topo.sim.V1.LGNOnAfferent
    sheet = projection.dest
    density=10; area=1.0

    density, area = float(density), float(area)
    spacing = np.linspace(-area/2.0, area/2.0, density+2)[1:-1]
    X, Y = np.meshgrid(spacing, spacing)
    sheet_coords = zip(X.flatten(),Y.flatten())
    coords = [sheet.sheet2matrixidx(x,y) for (x,y) in sheet_coords]
    cfs = np.dstack([projection.cfs[x][y].weights for (x,y) in coords])
    coords =  np.vstack([np.array(coord) for coord in coords])
    return {'afferent_CFs':(cfs, coords)}
