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
        self.figsize_params = None
        self.panel_label_params = None
        self.constrained_layout_pads = None
        self.panel_labels = {}

        if name is None:
            self.name = 'default'
            self._validate_panel_labels(
                {}
            )
            return

        if name.endswith('.yml'):
            fname = name
            name = name.split(os.sep)[-1][:-4]
        else:
            if name not in FigureLayout.available:
                errstr = f'"{name}" is not a valid Figure Layout name. See "FigureLayout.available"'
                errstr += ' or specify a valid yml file.'
                raise ValueError(errstr)
            fname = os.path.join(FigureLayout._data_dir, f'{name}.yml')

        self.name = None
        with open(fname) as f:
            params = yaml.load(f, Loader=yaml.SafeLoader)
            if not isinstance(params, dict):
                raise ValueError(f'"{fname}" does not parse into a valid dict data structure.')
            self._validate_parameters(params)
            self.name = name
                
    def _validate_figsize(self, params):
        if 'figsize' in params:
            figsize_keys = ['column_width', 'gutter_width', 'max_width', 'max_height', 'units']
            unrecognized = list(set(params['figsize']).difference(set(figsize_keys)))
            if len(unrecognized) > 0:
                warnings.warn(f'Found "{unrecognized}" in figsize and only "{figsize_keys}" are recognized.')
            incomplete = list(set(figsize_keys).difference(set(params['figsize'])))
            if len(incomplete) > 0:
                warnstr = 'These keys are missing from "figsize". Adding them will help ensure performance.\n'
                warnstr += f'{incomplete}'
                warnings.warn(warnstr)
            if params['figsize']['units'] == 'mm':
                max_height_inches = params['figsize']['max_height'] / 25.4
            if params['figsize']['units'] == 'cm':
                max_height_inches = params['figsize']['max_height'] / 2.54
            self.figsize_params = params['figsize']
            self.figsize_params['max_height_inches'] = max_height_inches
        else:
            warnings.warn('"figsize" is not in FigureLayout. get_figsize() will return Matplotlib defaults.')
            self.figsize_params = None

    def _validate_panel_labels(self, params):
        if 'panel_labels' in params:
            panel_label_keys = ['case', 'prefix', 'suffix']
            unrecognized = list(set(params['panel_labels']).difference(set(panel_label_keys)))
            unrecognized = [x for x in unrecognized if not x.startswith('font')]
            if len(unrecognized) > 0:
                warnings.warn(f'Found "{unrecognized}" in panel_labels and only "{panel_label_keys}" are recognized.')
            incomplete = list(set(panel_label_keys).difference(set(params['panel_labels'])))
            if len(incomplete) > 0:
                warnstr = 'These keys are missing from "panel_labels". Adding them will help ensure performance.\n'
                warnstr += f'{incomplete}'
                warnings.warn(warnstr)
            self.panel_label_params = params['panel_labels']
        else:
            warnings.warn('"panel_labels" is not in FigureLayout, so draw_panel_labels() will render raw.')
            self.panel_label_params = None

    def _validate_constrained_layout_pads(self, params):
        if 'constrained_layout_pads' in params:
            self.constrained_layout_pads = params['constrained_layout_pads']
        else:
            self.constrained_layout_pads = None

    def _validate_parameters(self, params):
        if params is None:
            warnings.warn('FigureLayout could not be instantiated. Using defaults.')
            return
        self._validate_figsize(params)
        self._validate_panel_labels(params)
        self._validate_constrained_layout_pads(params)

    def get_figsize(self, n_columns: int=None, width_proportion: float=None, height=None, 
                    wh_ratio: float=(1 + sqrt(5))/2, dpi: int=None) -> tuple:
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
            dpi (int): dpi to be used in the subsequent figure. Matplotlib requires appropriate rounding per this value.
                If None, it will use rcParams['figure.dpi']. Regardless, this should be the same dpi used when rendering
                or saving the figure. Default is None.

        Example:

            With a yaml file with the following values for figsize (as found in [Nature]
            (https://www.nature.com/documents/nature-final-artwork.pdf)):

                figsize:
                    column_width: 89
                    gutter_width: 5
                    max_width: 183
                    max_height: 247
                    units: 'mm'
                    dpi: 600

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
        if self.name == 'default':
            figsize = rcParams['figure.figsize']
            if height is None:
                return figsize  # Just return defaults.
            else:
                return [figsize[0], height]
        
        if n_columns is None and width_proportion is None:
            raise ValueError('n_columns and width_proportion cannot both be NULL.')
            
        if n_columns is not None:
            width_inches = self.figsize_params['column_width'] * n_columns
            width_inches += self.figsize_params['gutter_width'] * floor(n_columns - 1)
            
        if n_columns is None and (width_proportion > 1 or width_proportion < 0):
            raise ValueError('width_proportion must between 0 and 1.')
            
        elif width_proportion is not None and (0 <= width_proportion <= 1.):
            width_inches = self.figsize_params['max_width'] * width_proportion
        if width_inches > self.figsize_params['max_width']:
            width_inches = self.figsize_params['max_width']

        if self.figsize_params['units'] == 'mm':
            width_inches /= 25.4
        if self.figsize_params['units'] == 'cm':
            width_inches /= 2.54
        if height is None:
            height = width_inches / wh_ratio
        if 0 < height <= 1:
            height = self.figsize_params['max_height_inches'] * height
        if height > self.figsize_params['max_height_inches']:
            height = self.figsize_params['max_height_inches']
        
        # We need to round according to the dpi, otherwise the scaling may become off.
        if dpi is None:
            dpi = rcParams['figure.dpi']
        width_inches = int(width_inches * dpi) / dpi
        height = int(height * dpi) / dpi
        return width_inches, height
    
    def draw_panel_labels(self, fig):
        """Draw panel labels into the figure using our selected style.

        To use, one has to set an axes object to be labeled with a "panel_label" attribute, as in:

            ax.panel_label = 'A'

        This is an external, unrecognized attribute to matplotlib so calling `ax.set({'panel_label': 'A'})` will
        result in an error and one has to follow the approach above.

        Additionally, when creating and saving figures, a 
        [constrained_layout](https://matplotlib.org/stable/tutorials/intermediate/constrainedlayout_guide.html)
        should be used over 
        [tight_layout](https://matplotlib.org/stable/tutorials/intermediate/tight_layout_guide.html). This helps
        ensure that the figure size as defined in our parameters file is more accurately adopted.

        If for some reason we may want to perform further editing of the label handles, they are available in the
        `fig.texts` list.
        As well, the rendered labels is available as `fig_layout.labels`.

        Args:
            fig (Matplotlib Figure): A Matplotlib Figure with some number of axes.

        Example:

            From https://matplotlib.org/stable/tutorials/intermediate/gridspec.html:

                fig_layout = FigureLayout('nature')
                fig = plt.figure(figsize=fig_layout.get_figsize(n_columns=2, height=1.), constrained_layout=True)
                gs = fig.add_gridspec(3, 3)
                ax1 = fig.add_subplot(gs[0, :])
                ax1.set_title('gs[0, :]')
                ax2 = fig.add_subplot(gs[1, :-1])
                ax2.set_title('gs[1, :-1]')
                ax3 = fig.add_subplot(gs[1:, -1])
                ax3.set_title('gs[1:, -1]')
                ax4 = fig.add_subplot(gs[-1, 0])
                ax4.set_title('gs[-1, 0]')
                ax5 = fig.add_subplot(gs[-1, -2])
                ax5.set_title('gs[-1, -2]')

                # Add the panel_label attributes
                ax1.panel_label = 'A'
                ax2.panel_label = 'B'
                ax3.panel_label = 'E'
                ax4.panel_label = 'C'
                ax5.panel_label = 'D'

                # Draw the panel labels
                fig_layout.draw_panel_labels(fig)

                # Print a caption in Markdown.
                from IPython.display import Markdown as md
                panel_labels = fig_layout.get_formatted_panel_labels(fig, frmt='markdown')
                print(f'Figure 1. {panel_labels["A"]}, description of panel A...')
        """
        formatted_labels = self.get_formatted_panel_labels(fig)
        if len(formatted_labels) == 0:
            return
        if self.constrained_layout_pads is not None:
            fig.set_constrained_layout_pads(**self.constrained_layout_pads)
        fig.align_labels()
        fig.canvas.draw()  # We need to update all layouts otherwise, we may not capture where the axes really are.
        size_in_points = fig.get_size_inches()*fig.dpi
        constrained_layout = fig.get_constrained_layout()
        fig.set_constrained_layout(False)
        if self.panel_label_params:
            fontkwargs = {k: v for (k,v) in self.panel_label_params.items() if k.startswith('font')}
        else:
            fontkwargs = {}

        for ax in fig.get_axes():
            if hasattr(ax, 'panel_label'):
                formatted_label = formatted_labels[ax.panel_label]
                bbox_in_points = ax.get_tightbbox(fig.canvas.get_renderer(), for_layout_only=False)
                bbox = ax.get_position()
                # x = bbox.x0 - ax._xmargin
                y = bbox.y1

                # We write the label via `fig.text()`. However, if we have called fig.text() with labels before, 
                # we will run into problems trying to reuse the artist. Therefore, if it exists, we update it.
                updating = False  
                x = (bbox_in_points.x0)/size_in_points[0]
                # y = (bbox_in_points.y1)/size_in_points[1]
                for o in fig.findobj(text.Text):
                    if o.get_text() == formatted_label:
                        updating = True
                        o._x = x
                        o._y = y
                        o.set(va='baseline', ha='left', **fontkwargs)

                if updating is False:
                    fig.text(x, y, formatted_label, figure=fig, va='baseline', ha='left', **fontkwargs)
        fig.set_constrained_layout(constrained_layout)

    def get_formatted_panel_labels(self, fig, frmt='figure') -> dict:
        """For the figure axes that have a `panel_label` attribute, retrieve the string with its
        formatting characteristics. For example, "A" in bold lowercase for `frmt='html'` will
        give "<b>a</b>".

        Args:
            fig ([type]): Matplotlib figure where axes that have a `panel_label`, 
                we will get the text format of the label.
            format (str, optional): One of ['figure', 'tex', 'raw', 'html', 'markdown']. Defaults to 'figure'.
        
        Example:

            # Print a caption in Markdown.
            from IPython.display import Markdown as md
            panel_labels = fig_layout.get_formatted_panel_labels(fig, frmt='markdown')
            print(f'Figure 1. {panel_labels["A"]}, description of panel A...')

        Returns:
            dict: Keys are the `panel_label` attributes ascribed to various axes and the value is the
                formatted string. 
        """
        params = self.panel_label_params  # Just using a smaller variable name.
        if params is None:
            params = {}
        usetex = rcParams['text.usetex']
        prefix = ''
        suffix = ''
        ret = {}
        if frmt == 'raw':
            pass
        elif frmt == 'markdown':
            if 'fontweight' in params:
                if params['fontweight'] == 'bold':
                    prefix += '**'
                    suffix += '**'
            if 'fontstyle' in params:
                if params['fontstyle'] in ['italic', 'oblique']:
                    prefix += '*'
                    suffix += '*'
        elif frmt == 'html':
            if 'fontweight' in params:
                if params['fontweight'] == 'bold':
                    prefix += '<b>'
                    suffix += '</b>'
            if 'fontstyle' in params:
                if params['fontstyle'] in ['italic', 'oblique']:
                    prefix += '<i>'
                    suffix += '</i>'
        elif usetex or frmt == 'tex':
            prefix = ''
            suffix = ''
            if 'fontweight' in params:
                if params['fontweight'] == 'bold':
                    prefix += r'\textbf{'
                    suffix += r'}'
            if 'fontstyle' in params:
                if params['fontstyle'] in ['italic', 'oblique']:
                    prefix += r'\textit{'
                    suffix += r'}'

        for ax in fig.get_axes():
            if hasattr(ax, 'panel_label'):
                label = ax.panel_label
                orig_label = label
                if 'case' in params:
                    if params['case'] == 'lower':
                        label = label.lower()
                    if params['case'] == 'upper':
                        label = label.upper()
                if 'prefix' in params:
                    label = f'{params["prefix"]}{label}'
                if 'suffix' in params:
                    label = f'{label}{params["suffix"]}'
                label = prefix + label + suffix
                ret[orig_label] = label

        return ret
