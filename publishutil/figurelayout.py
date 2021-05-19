"""Object for calculating figure sizes and laying out panel labels.

For a list of available styles, one can access:

    FigureLayout.available

"""
import warnings
import os
import pkg_resources
from math import sqrt, floor

import yaml
from matplotlib import rcParams
import matplotlib.text as text

class FigureLayout(object):
    _data_dir = pkg_resources.resource_filename(__name__, 'figure_layouts/')
    available = [name[:-4] for name in os.listdir(_data_dir) if name.endswith('.yml')]
    
    def __init__(self, name: str=None):
        """
        Args:
            name (str): Name of the layout set to use if built in, or a path to a valid yaml file.

        Raises:
            ValueError: If the name is invalid or if the specified file cannot be found or is problematic. 
        """
        if name is None:
            errstr = f'"name" parameter is unspecified. See "FigureLayout.available" or specify a valid yml file.'
            raise ValueError(errstr)
        
        if name.endswith('.yml'):
            fname = name
            name = name.split(os.sep)[-1][:-4]
        else:
            if name not in FigureLayout.available:
                errstr = f'"{name}" is not a valid Figure Layout name. See "FigureLayout.available"'
                errstr += ' or specify a valid yml file.'
                raise ValueError(errstr)
            fname = os.path.join(FigureLayout._data_dir, f'{name}.yml')

        self.params = None
        self.name = None
        with open(fname) as f:
            self.params = yaml.load(f, Loader=yaml.SafeLoader)
            if not isinstance(self.params, dict):
                raise ValueError(f'"{fname}" does not parse into a valid dict data structure.')
            self._validate_parameters()
            self.name = name
            if 'figsize' in self.params:
                if self.params['figsize']['units'] == 'mm':
                    self.max_height_inches = self.params['figsize']['max_height'] / 25.4
                if self.params['figsize']['units'] == 'cm':
                    self.max_height_inches = self.params['figsize']['max_height'] / 2.54
        if name is None:
            errstr = f'"{name}" is not a valid figure layout.'
            errstr += 'Use "FigureLayout.available" to see available values or specify a valid path.'
            raise ValueError(errstr)
                
    def _validate_parameters(self):
        figsize_keys = ['column_width', 'gutter_width', 'max_width', 'max_height', 'units']
        panel_label_keys = ['case', 'prefix', 'suffix']
        if self.params is None:
            warnings.warn('FigureLayout could not be instantiated. Using defaults.')
        if 'figsize' not in self.params:
            warnings.warn('"figsize" is not in FigureLayout. get_figsize() will return Matplotlib defaults.')
        if 'panel_labels' not in self.params:
            warnings.warn('"panel_labels" is not in FigureLayout, so draw_panel_labels() is unavailable.')
        if 'figsize' in self.params:
            unrecognized = list(set(self.params['figsize']).difference(set(figsize_keys)))
            if len(unrecognized) > 0:
                warnings.warn(f'Found "{unrecognized}" in figsize and only "{figsize_keys}" are recognized.')
            incomplete = list(set(figsize_keys).difference(set(self.params['figsize'])))
            if len(incomplete) > 0:
                warnstr = 'These keys are missing from "figsize". Adding them will help ensure performance.\n'
                warnstr += f'{incomplete}'
                warnings.warn(warnstr)
        if 'panel_labels' in self.params:
            unrecognized = list(set(self.params['panel_labels']).difference(set(panel_label_keys)))
            unrecognized = [x for x in unrecognized if not x.startswith('font')]
            if len(unrecognized) > 0:
                warnings.warn(f'Found "{unrecognized}" in panel_labels and only "{panel_label_keys}" are recognized.')
            incomplete = list(set(panel_label_keys).difference(set(self.params['panel_labels'])))
            if len(incomplete) > 0:
                warnstr = 'These keys are missing from "panel_labels". Adding them will help ensure performance.\n'
                warnstr += f'{incomplete}'
                warnings.warn(warnstr)

    def get_figsize(self, n_columns: int=None, width_proportion: float=None, height=None, 
                    wh_ratio: float=(1 + sqrt(5))/2) -> tuple:
        """Get the figure width and height in inches given our style layout parameters.

        Args:
            n_columns (int, optional): If specified, this should most likely be an integer, but does not have to be. 
                When 1, then for multicolumn publications, this will be the same width of 1 column of text. 
                If 2 or more (or anything over 1), then this will incorporate the gutter spacing between columns.
                Either this argument or `width_proportion` should be specified=, but not both.
            width_proportion (float, optional): A value between 0-1 for the fraction of the maximum page width to 
                allow. Defaults to None. Either this argument or `n_columns` should be specified, but not both.
            height (int or float, optional): If this is a float between 0-1, then this represents the fraction of the
                maximal page height. For values greater than 1, this represents the height *in inches*, regardless of
                the native publication parameters. If None, then `wh_ratio` is used to calculate the height. 
                Defaults to None.
            wh_ratio (float, optional): When `height` is not specified, calculate the height of the figure as
                a ratio to the width. Defaults to the Golden Ration: (1 + sqrt(5))/2 = 1.61, so the height is 0.61
                of the width.

        Example:

            With a yaml file with the following values for figsize (as found in [Nature]
            (https://www.nature.com/documents/nature-final-artwork.pdf)):

                figsize:
                    column_width: 89
                    gutter_width: 5
                    max_width: 183
                    max_height: 247
                    units: 'mm'

            Here are a few scenarios for `get_figsize()`:

                fig_layout = FigureLayout('nature')
                print(f'Full page: {fig_layout.get_figsize(width_proportion=1., height=1.)}')
                print(f'Alternative Full page: {fig_layout.get_figsize(n_columns=2, height=1.)}')
                print(f'Half page: {fig_layout.get_figsize(width_proportion=1., height=.5)}')
                print(f'One column: Golden Ratio Height: {fig_layout.get_figsize(n_columns=1)}')
                print(f'One column: 16:9 aspect: {fig_layout.get_figsize(n_columns=1, wh_ratio=16/9)}')

            Which provides the following output:

                Full page: (7.204724409448819, 9.724409448818898)
                Alternative Full page: (7.204724409448819, 9.724409448818898)
                Half page: (7.204724409448819, 4.862204724409449)
                One column: Golden Ratio Height: (3.5039370078740157, 2.16555216530475)
                One column: 16:9 aspect: (3.5039370078740157, 1.970964566929134)

        Raises:
            ValueError: If both n_columns and width_proportion are not specified.

        Returns:
            tuple: (width, height) in inches.
        """
        if self.name is None:
            figsize = rcParams['figure.figsize']
            if height is None:
                return figsize  # Just return defaults.
            else:
                return [figsize[0], height]
        
        if n_columns is None and width_proportion is None:
            raise ValueError('n_columns and width_proportion cannot both be NULL.')
            
        if n_columns is not None:
            width_inches = self.params['figsize']['column_width'] * n_columns
            width_inches += self.params['figsize']['gutter_width'] * floor(n_columns - 1)
            
        if n_columns is None and (width_proportion > 1 or width_proportion < 0):
            raise ValueError('width_proportion must between 0 and 1.')
            
        elif width_proportion is not None and (0 <= width_proportion <= 1.):
            width_inches = self.params['figsize']['max_width'] * width_proportion
        if width_inches > self.params['figsize']['max_width']:
            width_inches = self.params['figsize']['max_width']

        if self.params['figsize']['units'] == 'mm':
            width_inches /= 25.4
        if self.params['figsize']['units'] == 'cm':
            width_inches /= 2.54
        if height is None:
            height = width_inches / wh_ratio
        if 0 < height <= 1:
            height = self.max_height_inches * height
        if height > self.max_height_inches:
            height = self.max_height_inches
        
        return width_inches, height
    
    def draw_panel_labels(self, fig, shift=(0, 0)):
        """Draw panel labels into the figure using our selected style.

        To use, one has to set an axes object to be labeled with a "panel_label" attribute, as in:

            ax.panel_label = 'A'

        This is an external, unrecognized attribute to matplotlib so calling `ax.set({'panel_label': 'A'})` will
        result in an error and one has to follow the approach above.

        If for some reason we may want to perform further editing of the labels, they are available in the
        `fig.texts` list.

        Args:
            fig (Matplotlib Figure): A Matplotlib Figure with some number of axes.
            shift (tuple): Shift, in pixels of the label from the upper left of the axes' 
                [tightbox](https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.get_tightbbox.html).
                A negative X value shifts to the left and a positive Y value moves up.

        Example:

            From https://matplotlib.org/stable/tutorials/intermediate/gridspec.html:

                fig_layout = FigureLayout('nature')
                fig3 = plt.figure(figsize=fig_layout.get_figsize(n_columns=2, height=1.), constrained_layout=True)
                gs = fig3.add_gridspec(3, 3)
                f3_ax1 = fig3.add_subplot(gs[0, :])
                f3_ax1.set_title('gs[0, :]')
                f3_ax2 = fig3.add_subplot(gs[1, :-1])
                f3_ax2.set_title('gs[1, :-1]')
                f3_ax3 = fig3.add_subplot(gs[1:, -1])
                f3_ax3.set_title('gs[1:, -1]')
                f3_ax4 = fig3.add_subplot(gs[-1, 0])
                f3_ax4.set_title('gs[-1, 0]')
                f3_ax5 = fig3.add_subplot(gs[-1, -2])
                f3_ax5.set_title('gs[-1, -2]')

                # Add the panel_label attributes
                f3_ax1.panel_label = 'A'
                f3_ax2.panel_label = 'B'
                f3_ax3.panel_label = 'E'
                f3_ax4.panel_label = 'C'
                f3_ax5.panel_label = 'D'

                # Draw the panel labels
                fig_layout.draw_panel_labels(fig3)
        """
        if self.params is None:
            return
        if 'panel_labels' not in self.params:
            return
        fig.canvas.draw()  # We need to update all layouts otherwise, we may not capture where the axes really are.
        size_in_points = fig.get_size_inches()*fig.dpi
        usetex = rcParams['text.usetex']
        params = self.params['panel_labels']
        if usetex:
            texprefix = ''
            texsuffix = ''
            if 'fontweight' in params:
                if params['fontweight'] == 'bold':
                    texprefix += r'\textbf{'
                    texsuffix += r'}'
            if 'fontstyle' in params:
                if params['fontstyle'] in ['italic', 'oblique']:
                    texprefix += r'\textit{'
                    texsuffix += r'}'

        for ax in fig.get_axes():
            if hasattr(ax, 'panel_label'):
                label = ax.panel_label
                fontkwargs = {k: v for (k,v) in params.items() if k.startswith('font')}
                if 'case' in params:
                    if params['case'] == 'lower':
                        label = label.lower()
                    if params['case'] == 'upper':
                        label = label.upper()
                if 'prefix' in params:
                    label = f'{params["prefix"]}{label}'
                if 'suffix' in params:
                    label = f'{label}{params["suffix"]}'
                if usetex:
                    label = texprefix + label + texsuffix

                bbox_in_points = ax.get_tightbbox(fig.canvas.get_renderer(), for_layout_only=False)

                # We write the label via `fig.text()`. However, if we have called fig.text() with labels before, 
                # we will run into problems trying to reuse the artist. Therefore, if it exists, we update it.
                updating = False  
                x = (bbox_in_points.x0+shift[0])/size_in_points[0]
                y = (bbox_in_points.y1+shift[1])/size_in_points[1]
                for o in fig.findobj(text.Text):
                    if o.get_text() == label:
                        updating = True
                        o._x = x
                        o._y = y
                        o.set(va='top', ha='left', **fontkwargs)

                if updating is False:
                    fig.text(x, y, label, figure=fig, va='top', ha='left', **fontkwargs)
