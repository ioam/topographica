import math, os, shutil, uuid
import lancet
import imagen
import numpy as np
from lib import rasterplots, compose, vectorplots, analysis

class Display(object):

    def __init__(self, data=None, template_dir=None, snapshot=None):
        self.data = data
        self.png_path = None
        if None not in (snapshot, template_dir):
            self.png_path = os.path.join(template_dir, 'snapshots',
                                         '%s.png' % snapshot)

        if (self.png_path is None) and (self.data is None):
            raise Exception("Insufficient information for display")

    def _repr_svg_(self):
        if self.data:
            return self.data
        elif self.svg_path:
            return open(self.svg_path, 'r').read()

    def _repr_png_(self):
        if self.data is None and self.png_path:
            return open(self.png_path, 'r').read()


def get_pref(row, roi=True, normalize=True):
    sheetview = row['OrientationPreference']
    if roi is True:     roi = row['roi']
    elif roi is False:  roi = slice(None,None)
    data = sheetview.data[roi, roi]
    return data / sheetview.cyclic_range if normalize else data

def get_sel(row, roi=True):
    sheetview = row['OrientationSelectivity']
    if roi is True:     roi = row['roi']
    elif roi is False:  roi = slice(None,None)
    return sheetview.data[roi, roi]


def setup(name, template_dir, build_dir, subdir=None):
    """
    Searches for the appropriate template in template_dir and creates
    a new subdirectory in build_dir for building the figure. Returns
    the full template path and the output_path. If subdir is none, the
    name of the subdirectory is the same as the name of the template.
    """
    subdir = subdir if subdir else name
    output_dir = os.path.join(build_dir, subdir)
    if not os.path.isdir(output_dir): os.makedirs(output_dir)
    if name+'.svg' not in os.listdir(template_dir):
        info =(name+'.svg', template_dir)
        raise Exception("Template %r not found in %r" % info)
    else:
        path = os.path.join(template_dir, name+'.svg')
        return os.path.abspath(path), output_dir


def OR_analysis(row, template_dir, build_dir, name='OR_analysis',
                selectivity=False, contours=False,
                cfs=True, scalebox = False, size_factor=1.0,):
    """
    Builds a pinwheel analysis of a single orientation map from a
    template. Used in Figures 3 and 6-9.  Displays an annotated map
    with pinwheels next to the FFT spectrum and corresponding fit.
    The selectivity channel of the map can be enabled as can pinwheel
    contours and a column of central connection fields. The map can
    have either a normal scalebar or a box showing the hypercolumn
    area.
    """
    template_path, output_dir = setup('OR_analysis', template_dir, build_dir, subdir=name)
    savefig_opts = dict(transparent=True, format='svg', bbox_inches='tight', pad_inches=0)
    pref = get_pref(row)
    sel = get_sel(row) if selectivity else None
    fname = os.path.join(output_dir, '%%s_%s.%%s' % name)
    # Save the OR preference and selectivity raster
    or_map = rasterplots.OR_map(pref, sel)
    rasterplots.black_selectivity(or_map).save(fname % ('OR','png'))
    # Save the FFT raster
    rasterplots.greyscale(analysis.power_spectrum(pref)).save(fname % ('FFT','png'))

    # Save the histogram SVG overlay
    hist = vectorplots.FFT_histogram_overlay(row['amplitudes'], row['fit'])
    hist.savefig(fname % ('HIST', 'svg'), **savefig_opts)
    # Save the pinwheel contour SVG overlay
    contours = (row['re_contours'], row['im_contours']) if contours else None
    contour_fig = vectorplots.pinwheel_overlay(row['pinwheels'], contours=contours)
    contour_fig.savefig(fname % ('OVERLAY','svg'), **savefig_opts)

    # Save the CFs (if enabled)
    if cfs and row['afferent_CFs'] is np.nan:
        print "No afferent connection fields found in the given row"
    elif cfs:
        cf_block = rasterplots.cf_image(*row['afferent_CFs'],
                                         border=5, width=1, height=8, pos=(4,1))
        cf_block.save(fname % ('CFs', 'png'))

    # Save the scale bar or scale box SVG overlay
    scale_overlay = (vectorplots.scale_box_overlay if scalebox
                     else vectorplots.scale_bar_overlay)
    scale = scale_overlay(row['units_per_hypercolumn']/float(pref.shape[0]))
    scale.savefig(fname % ('SBOX' if scalebox else 'SBAR', 'svg'), **savefig_opts)
    vectorplots.close([hist, contour_fig, scale])

    layers = {'-scalebox':(not scalebox), '+scalebox':scalebox,
              '-CFs':(not cfs), '+CFs':cfs}

    svg_path = os.path.join(output_dir, '%s.svg' % name)
    return compose.apply_template(template_path, svg_path,
                                  mapping={'[LABEL]':name},
                                  layers=layers,
                                  size_factor=size_factor)


def fig03(template_dir, build_dir, L_seed=20, L_contrast=15,
          mean_mm2_ferret=0.75, size_factor=1.0, show_raster=False):
    """
    Automatically selects the best examplar of a high metric map from
    the GCAL dataset and displays it along with the chosen examplar of
    a non-optimal map from the L model.
    """
    name = 'fig03'
    if show_raster: return Display(snapshot=name, template_dir=template_dir)
    template_path, output_dir = setup(name, template_dir, build_dir)

    # Get the files relating to L and GCAL
    L_pattern = 'jn13_figures/output/Fig05_06/*/*/*.npz'
    L_files = lancet.FilePattern('npz_file', L_pattern)
    L_info = lancet.FileInfo(L_files, 'npz_file', lancet.NumpyFile())
    L_frame = L_info.dframe

    GCAL_pattern = 'jn13_figures/output/Fig09/*Fig09_*/*/*.npz'
    GCAL_files = lancet.FilePattern('npz_file', GCAL_pattern)
    GCAL_info = lancet.FileInfo(GCAL_files, 'npz_file', lancet.NumpyFile())
    GCAL_frame =GCAL_info.dframe

    assert max(L_frame['time']) == max(GCAL_frame['time'])
    max_time = max(GCAL_frame['time'])

    pi_index = (GCAL_frame['rho'] - math.pi).abs().argmin()
    GCAL_row = GCAL_info.load(GCAL_frame.ix[pi_index:pi_index]).iloc[0]

    GCAL_kmax = GCAL_row['kmax']; GCAL_pwcount = GCAL_row['pinwheels'].shape[0]
    GCAL_labels = [GCAL_kmax, GCAL_kmax**2, GCAL_pwcount / (GCAL_kmax**2), GCAL_pwcount]

    # Select the chosen L map from the dataframe
    Lmap_condition = ( (L_frame['contrast']== L_contrast)
                      & (L_frame['input_seed']==L_seed)
                      & (L_frame['time'] == max_time))

    L_row = L_info.load(L_frame[Lmap_condition]).iloc[0]
    L_kmax = L_row['kmax']; L_pwcount = L_row['pinwheels'].shape[0]
    L_labels = [L_kmax, L_kmax**2, L_pwcount / (L_kmax**2), L_pwcount]

    # Saving the preference only maps (subplot C)
    analysis_kws = dict(scalebox=True, selectivity=True, contours=True, cfs=False)
    OR_analysis(GCAL_row, template_dir, output_dir, name='GCAL', **analysis_kws)
    OR_analysis(L_row, template_dir, output_dir, name='L',**analysis_kws)

    fname = os.path.join(output_dir, '%s')
    # Note: Not using ROI in these two example images.
    GCAL_pref = rasterplots.OR_map(get_pref(GCAL_row))
    L_pref = rasterplots.OR_map(get_pref(L_row))
    GCAL_pref.save(fname % 'GCAL_pref.png')
    L_pref.save(fname % 'L_pref.png')

    # Saving the scatterplot
    GCAL_maps = GCAL_info.load(GCAL_frame[(GCAL_frame['time']==20000)
                                        & (GCAL_frame['contrast']==100)])
    GCAL_pwds = GCAL_maps['rho']
    L_maps = L_info.load(L_frame[(L_frame['time']==20000)
                               & (L_frame['contrast']==L_contrast)])
    L_pwds = L_maps['rho']

    iterables = [zip(GCAL_maps['units_per_hypercolumn'], GCAL_pwds),
                 zip(L_maps['units_per_hypercolumn'], L_pwds)]

    scatter = vectorplots.model_scatterplot(iterables, ['r','b'])
    savefig_opts = dict(transparent=True, format='svg', bbox_inches='tight', pad_inches=0)
    scatter.savefig(fname % 'model_scatter.svg', **savefig_opts)
    vectorplots.close([scatter])

    GCAL_fmts = [('[pk1]','%.2f'),('[ar1]','%.2f'), ('[pd1]','%.3f'),('[pw1]','%d')]
    L_fmts=  [('[pk2]','%.2f'),('[ar2]','%.2f'), ('[pd2]','%.3f'),('[pw2]','%d')]
    labels = zip(GCAL_labels + L_labels, GCAL_fmts + L_fmts)
    mapping=dict((label, fmt%v) for (v,(label,fmt)) in labels)
    svg_path = os.path.join(output_dir, '%s.svg' % name)
    return Display(compose.apply_template(template_path, svg_path,
                                             mapping=mapping,
                                             size_factor=size_factor))


def fig05(template_dir, build_dir, contrast=25, seed=102,
          times=[4000*i for i in range(6)],
          size_factor=1.0, show_raster=False):
    """
    Builds figure 5 showing the development of L model from an SVG
    template.
    """
    name = 'fig05'
    if show_raster: return Display(snapshot=name, template_dir=template_dir)
    template_path, output_dir = setup(name, template_dir, build_dir)
    L_pattern = 'jn13_figures/output/Fig05_06/*/*/*.npz'
    L_files = lancet.FilePattern('npz_file', L_pattern)
    L_info = lancet.FileInfo(L_files, 'npz_file', lancet.NumpyFile())

    filter_times = L_info.dframe['time'].map(lambda x: x in times)
    selection = L_info.dframe[filter_times
                              & (L_info.dframe['contrast']==contrast)
                              & (L_info.dframe['input_seed']==seed)]
    selected_rows = L_info.load(selection)

    for (index, row) in selected_rows.iterrows():
        fname = os.path.join(output_dir, '%%s_%.1f.png' % int(row['time']))
        roi=row['roi']
        (cfs, coords) = row['afferent_CFs']
        # Create the combined preference/selectivity map
        or_map = rasterplots.OR_map(get_pref(row), get_sel(row))
        or_black = rasterplots.black_selectivity(or_map)
        # Save the orientation map
        or_black.save(fname % 'OR')
        # Save the row of CF images
        cf_block  = rasterplots.cf_image(cfs, coords, border=5, width=8, height=1, pos=(1,4))
        cf_block.save(fname % 'CF')

    svg_path = os.path.join(output_dir, '%s.svg' % name)
    (basepath,_) = os.path.split(svg_path)
    svg = compose.SVGUtils.load(os.path.abspath(template_path))
    svg = compose.SVGUtils.embed_rasters(svg, basepath)
    svg = compose.SVGUtils.resize(svg, size_factor)
    compose.SVGUtils.save(svg, svg_path)
    return Display(compose.SVGUtils.string(svg))


def fig06_09(template_dir, build_dir, fig, contrasts=(10,25,100),
             selectivity_norm = 1.0, input_seed=102, size_factor=1.0,
             kernel=analysis.gamma_metric, show_raster=False):

    name = 'fig0%d' % fig
    if show_raster: return Display(snapshot=name, template_dir=template_dir)
    template_path, output_dir = setup('fig06_09', template_dir,
                                      build_dir, subdir=name)
    # Get the files containing the relevant data
    output_name = ('Fig0%d' % fig) if fig != 6 else 'Fig05_06'
    pattern = 'jn13_figures/output/%s/*%s_*/*/*.npz' % (output_name, output_name)
    files = lancet.FilePattern('npz_file', pattern)
    info = lancet.FileInfo(files, 'npz_file', lancet.NumpyFile())
    dframe = info.dframe
    # Some basic constants
    max_time = max(dframe['time']); input_seeds = set(dframe['input_seed'])
    all_contrasts = set(dframe['contrast']); all_times = set(dframe['time'])

    savefig_opts = dict(transparent=True, format='svg', bbox_inches='tight', pad_inches=0)
    # Saving all the png/svg components for the three chosen contrasts (subplot D-F)
    boolarr = np.array(dframe['time'] == max_time) & np.array(dframe['input_seed'] == input_seed)
    for contrast in contrasts:
        fname = os.path.join(output_dir, '%%s_%d_%d.%%s' % (contrast, max_time))
        contrast_slice = np.array(dframe['contrast']==contrast)
        row = info.load(dframe[boolarr & contrast_slice]).iloc[0]

        OR_analysis(row, template_dir, output_dir,
                    name='OR_c%s' % contrast, selectivity=True)

        # Collecting preferences/selectivities across time/seeds for map_development plots
        selectivities, stabilities = [],[]
        for seed in input_seeds:
            seed_slice = np.array(dframe['input_seed'] == seed)
            df = info.load(dframe[contrast_slice & seed_slice])
            # Ensuring the data is sorted by simulation time
            sorted_rows = [df[df['time'] == time].iloc[0] for time in sorted(df['time'])]
            prefs = [get_pref(row) for row in sorted_rows]
            # Each selectivity is a whole map, these selectivities are averages across the map
            mean_sels = [get_sel(row).mean() for row in sorted_rows]
            selectivities.append(mean_sels)
            stabilities.append(analysis.stability_index(prefs))

        # Save the stability/selectivity plots
        map_dev = vectorplots.map_development_streams(np.array(stabilities),
                                                      np.array(selectivities),
                                                      selectivity_norm = selectivity_norm)
        fname = os.path.join(output_dir, 'SI_%s.svg' % contrast)
        map_dev.savefig(fname,**savefig_opts)
        vectorplots.close([map_dev])

    # Collect the selectivity, stability and map metric across contrasts and seeds
    selectivities, stabilities, metrics = [],[],[]
    time_slice = np.array(dframe['time'] == max_time)
    for seed in input_seeds:
        seed_slice = np.array(dframe['input_seed'] == seed)
        df = info.load(dframe[time_slice & seed_slice])
        # Ensuring contrasts are sorted
        sorted_rows = [df[df['contrast'] == contrast].iloc[0] for contrast in sorted(df['contrast'])]

        missing_contrasts = set(df['contrast']) ^set(all_contrasts)
        if missing_contrasts != set():
            missing = ', '.join(str(el) for el in missing_contrasts)
            print "Warning: Contrast values %s are missing for seed %d" % (missing, seed)
        # Each selectivity is a whole map, these selectivities are averages across the map
        mean_sels = [get_sel(row).mean() for row in sorted_rows]
        # Computing map quality based on the pinwheel density
        pinwheel_counts = [row['pinwheels'].shape[0] for row in sorted_rows]
        # Pinwheel density is pinwheel count / (kmax**2)
        pinwheel_densities = [(pwcount/row['kmax']**2) for (pwcount,row)
                                      in zip(pinwheel_counts, sorted_rows)]
        metrics.append([kernel(pwd) for pwd in pinwheel_densities])
        selectivities.append(mean_sels)
        # Obtaining the mean stability per contrast, sorted by contrast then by time
        df = info.load(dframe[seed_slice])
        contrast_stabilities = []
        for contrast in sorted(all_contrasts):
            rows = [df[(df['time']==time) & (df['contrast']==contrast)].iloc[0] for time in sorted(all_times)]
            prefs = [get_pref(row) for row in rows]
            mean_stability = np.mean(analysis.stability_index(prefs))
            contrast_stabilities.append(mean_stability)
        stabilities.append(contrast_stabilities)

    # Save the contrast plot
    fname = os.path.join(output_dir, 'contrast.svg')
    args = (sorted(all_contrasts), np.array(selectivities), np.array(stabilities), np.array(metrics))
    contrast_plot = vectorplots.contrast_streams(*args, vlines=contrasts)
    contrast_plot.savefig(fname, **savefig_opts)
    vectorplots.close([contrast_plot])
    # Composing the whole figure together
    svg_path = os.path.join(output_dir, '%s.svg' % name)
    model_list = ['L','AL','GCL','GCAL']
    current_model = model_list[[6,7,8,9].index(fig)]
    mapping = dict([('[CONTRAST%d]' % i,c) for (i,c) in enumerate(contrasts)]
                   + [('[TIME]', int(max_time)),
                      ('[Model-Name]', current_model + " Model")])

    layers = dict((name,name==current_model) for name in model_list)
    return Display(compose.apply_template(template_path, svg_path,
                                             mapping=mapping,
                                             layers=layers,
                                             size_factor=size_factor))


def fig10(template_dir, build_dir, bound_radius=0.6,  selectivity_norm=0.07138,
          size_factor=1.0, show_raster=False):
    name = 'fig10'
    if show_raster: return Display(snapshot=name, template_dir=template_dir)
    times=[2000*i for i in range(6)]
    template_path, output_dir = setup(name, template_dir, build_dir)
    pattern = 'jn13_figures/output/Fig10_12/*/*/*.npz'
    files = lancet.FilePattern('npz_file', pattern)
    file_info = lancet.FileInfo(files, 'npz_file', lancet.NumpyFile())

    filter_times = file_info.dframe['time'].map(lambda x: x in times)
    selection = file_info.load(file_info.dframe[filter_times])

    savefig_opts = dict(transparent=True, format='svg', bbox_inches='tight', pad_inches=0)
    development_info = []
    for (index, row) in selection.iterrows():
        time =row['time']
        fname = os.path.join(output_dir, '%%s_%.1f.png' % int(time))
        bounds = imagen.boundingregion.BoundingBox(radius=0.75)
        sheetcoords = imagen.SheetCoordinateSystem(bounds, xdensity=98)
        roi = slice(*sheetcoords.sheet2matrixidx(bound_radius, bound_radius))
        # Not applying ROI as new bounds will be used
        pref = get_pref(row, roi=roi)
        sel = get_sel(row, roi=roi)
        (cfs, coords) = row['afferent_CFs']

        roi = slice(*sheetcoords.sheet2matrixidx(bound_radius, bound_radius))
        # Create the combined preference/selectivity map
        or_map = rasterplots.OR_map(pref,sel)
        or_black = rasterplots.black_selectivity(or_map)
        (dim1,dim2) = pref.shape
        or_black_resized = rasterplots.resize(or_black, (dim1*4,dim2*4))
        # Save the orientation map
        or_black_resized.save(fname % 'OR')
        # Save the row of CF images
        cf_block  = rasterplots.cf_image(cfs, coords, border=5, width=8, height=1,
                                         pos=(1,4),  bg=(255,255,255))
        cf_block.save(fname % 'CF')
        # Save the FFT of the last map
        if time == times[-1]:
            normalized_spectrum = analysis.power_spectrum(pref[roi,roi])
            fft_im = rasterplots.greyscale(normalized_spectrum)
            fft_im.save(fname % 'FFT')

        # Note: ROI not applied and the values of 3 are due to historical reasons
        development_info.append((time,pref[3:-3, 3:-3], np.mean(sel[3:-3,3:-3])))

    ts, prefs, mean_sels = zip(*sorted(development_info))
    # We only need the stabilities up till 10000
    fname = os.path.join(output_dir, 'model_development.svg')
    development_fig = vectorplots.map_development_plot(analysis.stability_index(prefs),
                                                          mean_sels, selectivity_norm)
    development_fig.savefig(fname, **savefig_opts)
    vectorplots.close([development_fig])
    svg_path = os.path.join(output_dir, '%s.svg' % name)
    return Display(compose.apply_template(template_path, svg_path,
                                             size_factor=size_factor))


def fig11(template_dir, build_dir, input_seed=102, size_factor=1.0, show_raster=False):
    """
    Automatically generates Figure 11 showing the result of simulated
    goggle rearing and comparing to the experimental data (Tanaka
    2009).
    """
    name = 'fig11'
    if show_raster: return Display(snapshot=name, template_dir=template_dir)
    resize_factor = 4
    times = [ 6000,  9000, 12000, 20000]

    template_path, output_dir = setup(name, template_dir, build_dir)
    pattern = 'jn13_figures/output/Fig11/*seed102/*/*.npz'
    files = lancet.FilePattern('npz_file', pattern)
    file_info = lancet.FileInfo(files, 'npz_file', lancet.NumpyFile())

    filter_times = file_info.dframe['time'].map(lambda x: x in times)
    selection = file_info.load(file_info.dframe[filter_times])

    roi = selection[selection['time']==times[-1]]['roi'].iloc[0]
    savefig_opts = dict(transparent=True, format='svg', bbox_inches='tight', pad_inches=0)

    for (index,row) in selection.iterrows():
        fname = os.path.join(output_dir, 'OR_%d.png' % int(row['time']))
        pref = get_pref(row)
        sel = get_sel(row)

        # Rotate the colour key to match the convention in Tanaka et el.
        tanaka_pref = pref + (2.0 / 3.0) % 1
        # Create the combined preference/selectivity map
        or_map = rasterplots.OR_map(tanaka_pref,sel)
        or_black = rasterplots.black_selectivity(or_map)
        # Resize by factor
        (dim1,dim2) = pref.shape
        or_black_resized = rasterplots.resize(or_black, (dim1*resize_factor,
                                                         dim2*resize_factor))
        # Save the orientation maps
        or_black_resized.save(fname)

        # Unbiased experimental histogram
        unbiased_hist = vectorplots.tanaka_histogram('unbiased')
        unbiased_hist.savefig(os.path.join(output_dir, 'unbiased_tanaka.svg'), **savefig_opts)

        # Vertically biased experimental histogram
        biased_hist = vectorplots.tanaka_histogram('biased')
        biased_hist.savefig(os.path.join(output_dir, 'biased_tanaka.svg'), **savefig_opts)

        # Approximation to vertical goggle rearing
        fname = os.path.join(output_dir, 'VGR_%d.svg' % int(row['time']))
        gcal_hist = vectorplots.tanaka_histogram(pref)
        gcal_hist.savefig(fname, **savefig_opts)
        vectorplots.close([biased_hist, gcal_hist])
    svg_path = os.path.join(output_dir, '%s.svg' % name)
    return Display(compose.apply_template(template_path, svg_path,
                                             size_factor=size_factor))


def fig12(template_dir, build_dir, input_seed=102, time=20000, legend=False,
          size_factor=1.0, show_raster=False,
          coords=[(0.1494891818682797, 0.19955835216333589),  # FIXME: need less decimal places than this!
                  (0.096254715375009847, 0.34303406831506555),
                  (0.35008453579353438, 0.33729457381835848)]):
    """
    Plots orientation tuning across contrast for simulation
    trained using the 'Nature' condition.
    """
    name = 'fig12'
    if show_raster: return Display(snapshot=name, template_dir=template_dir)
    template_path, output_dir = setup(name, template_dir, build_dir)


    pattern = 'jn13_figures/output/Fig10_12/*/*/*.npz'
    files = lancet.FilePattern('npz_file', pattern)
    file_info = lancet.FileInfo(files, 'npz_file', lancet.NumpyFile())
    selection = file_info.load(file_info.dframe[file_info.dframe['time']==time])
    tuning_curves = selection.iloc[0]['tuning_curves']

    savefig_opts = dict(transparent=True, format='svg', bbox_inches='tight', pad_inches=0)

    for i,coord, norm in [(i,c,norm) for (i,c) in enumerate(coords) for norm in [True, False]]:
        fname = 'ORtuning_%d%s_%d.svg' % (i+1, '_norm' if norm else '', time)

        tcfig = vectorplots.tuning_curve_plot(tuning_curves, coord,
                                              legend=legend, normalize=norm)
        tcfig.savefig(os.path.join(output_dir, fname), **savefig_opts)

    svg_path = os.path.join(output_dir, '%s.svg' % name)
    return Display(compose.apply_template(template_path, svg_path,
                                             size_factor=size_factor))
