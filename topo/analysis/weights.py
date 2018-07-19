import numpy as np

import param
from holoviews import Store, Options, Layout, HoloMap, Histogram, Dimension

try:     # HoloViews <1.8
    from holoviews.operation import TreeOperation
except:  # HoloViws >=1.8
    from featuremapper.analysis import TreeOperation

class WeightIsotropy(TreeOperation):
    """
    Computes a histogram of azimuths between the positional
    preferences of pre- and post-synaptic neurons weighted
    by the connection strength and normalized relative to
    the orientation preference.

    Useful for determining whether lateral connection are
    anisotropic along the axis of preferred orientation.
    """

    num_bins = param.Integer(default=20, doc="""
        Number of bins in the histogram.""")

    roi = param.NumericTuple(default=(-0.5, -0.5, 0.5, 0.5), doc="""
        Region of interest supplied as a four-tuple of the
        form (left, bottom, right, top)""")

    projections = param.List(default=[], doc="""
       List of tuples of the form (sheet, projection).""")

    threshold = param.Integer(default=70, doc="""
       Threshold as a percentile of the weight field.""")

    min_dist = param.Number(default=0.1, doc="""
       Minimum distance in sheet coordinates""")

    symmetric = param.Boolean(default=True, doc="""
       Whether to make isotropy symmetric.""")

    @classmethod
    def _last(cls, obj):
        return obj.last if isinstance(obj, HoloMap) else obj

    def _process(self, tree, key=None):
        layout = Layout()
        for s, p in self.p.projections:
            # Get last element
            orelmnt = self._last(tree.OrientationPreference[s])
            selelmnt = self._last(tree.OrientationSelectivity[s])
            xelmnt  = self._last(tree.XPreference[s])
            yelmnt  = self._last(tree.YPreference[s])

            # If any preference has not been supplied skip analysis
            if any(not o for o in [orelmnt, xelmnt, yelmnt]):
                return Layout()

            # Flatten preferences
            xpref_arr = xelmnt.dimension_values(2)
            ypref_arr = yelmnt.dimension_values(2)
            sel_arr = selelmnt.dimension_values(2)

            # Iterate over CFs in ROI
            l, b, r, t = self.p.roi
            lat_weights = tree.CFs[p]
            azimuths, weights = [], []
            for key, cf in lat_weights[l:r, b:t].items():
                # Get preferences for a particular unit
                unit_angle, unit_x, unit_y = orelmnt[key], xelmnt[key], yelmnt[key]
                unit_sel = selelmnt[key]
                weight_arr = cf.situated.dimension_values(2)
                mask = weight_arr>np.percentile(weight_arr, self.p.threshold)
                sel = sel_arr[mask]
                weight = weight_arr[mask] * unit_sel * sel
                xpref = xpref_arr[mask]
                ypref = ypref_arr[mask]

                # Compute x/y-preference differences between
                # pre- and post-synaptic neurons
                dx = xpref - unit_x
                dy = ypref - unit_y
                d = np.sqrt(dx**2 + dy**2)

                # Compute angle between position preferences
                # of the pre- and post-synaptic neurons
                # Correcting for preferred orientation
                conn_angle = np.arctan2(dy, dx)
                delta = conn_angle - unit_angle
                delta[delta<0] += np.pi*2
                delta2 = delta + np.pi
                delta2 %= np.pi*2

                azimuths.append(delta[d>self.p.min_dist])
                weights.append(weight[d>self.p.min_dist])
                if self.p.symmetric:
                    azimuths.append(delta2[d>self.p.min_dist])
                    weights.append(weight[d>self.p.min_dist])

            # Combine azimuths and weights for all CFs
            azimuths = np.concatenate(azimuths)
            weights = np.concatenate(weights)
            # Compute histogram
            bins, edges = np.histogram(azimuths, range=(0, 2*np.pi),
                                       bins=self.p.num_bins, weights=weights, normed=True)

            # Construct Elements
            label =' '.join([s, p])
            histogram = Histogram((edges, bins), group="Weight Isotropy",
                                  kdims=[Dimension('Azimuth')], label=label)
            layout.WeightIsotropy['_'.join([s, p])] = histogram
        return layout


def circular_dist(a, b, period):
    """
    Returns the distance between a and b (scalars) in a domain with `period` period.
    """
    return np.minimum(np.abs(a - b), period - np.abs(a - b))


class WeightDistribution(TreeOperation):
    """
    Computes histogram of the difference in feature
    preference between pre- and post-synaptic neurons
    weighted by the connection strength between them.
    """

    feature = param.String(default='Orientation', doc="""
       Feature to compute the distribution over""")

    num_bins = param.Integer(default=10, doc="""
       Number of histogram bins.""")

    normalized = param.Boolean(default=False, doc="""
       Whether to normalize the histogram""")

    projections = param.List(default=[], doc="""
       List of tuples of the form (sheet, projection).""")

    weighted = param.Boolean(default=True)

    def _process(self, tree, key=None):
        preferences = tree[self.p.feature+'Preference']
        layout = Layout()
        for s, p in self.p.projections:
            if s not in preferences:
                continue
            featurepref = preferences[s]
            if isinstance(featurepref, HoloMap):
                featurepref = featurepref.last
            feature = featurepref.vdims[0]
            feature_arr = featurepref.data.flat
            cfs = tree.CFs[p]
            deltas, weights = [], []
            for k, cf in cfs.items():
                preferred = featurepref[k]
                weight_arr = cf.situated.data.flat
                feature_slice = feature_arr[weight_arr>0]
                weight_slice = weight_arr[weight_arr>0]
                if feature.cyclic:
                    feature_delta = circular_dist(preferred, feature_slice, feature.range[1])
                else:
                    feature_delta = np.abs(feature_slice-preferred)
                deltas.append(feature_delta)
                weights.append(weight_slice)
            deltas = np.concatenate(deltas)
            weights = np.concatenate(weights)
            bin_range = (0, feature.range[1]/2.) if feature.cyclic else None
            bins, edges = np.histogram(deltas, range=bin_range, bins=self.p.num_bins,
                                       weights=weights, normed=self.p.normalized)
            # Construct Elements
            label = ' '.join([s,p])
            group = '%s Weight Distribution' % self.p.feature
            histogram = Histogram((edges, bins), group=group, label=label,
                                  kdims=[' '.join([self.p.feature, 'Difference'])],
                                  vdims=['Weight'])

            layout.WeightDistribution['_'.join([s,p])] = histogram

        return layout

options = Store.options(backend='matplotlib')
options.Histogram.Weight_Isotropy = Options('plot', projection='polar', show_grid=True)
