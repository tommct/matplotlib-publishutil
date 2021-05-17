# matplotlib-publishutil

[![PyPI version](https://badge.fury.io/py/publishutil.svg)]
(https://badge.fury.io/py/matplotlib-publishutil)

*Utilities to help configure matplotlib figures for publication.*

This repo contains utility functions to help (re)configure [Matplotlib]
(https://matplotlib.org/) figures within the formatting constraints of a given 
publication. Example uses include:

  * Toggling figures between slide presentation and print publication formats. 
  * Dynamically rescale figure dimensions to abide by a publication's column 
    or page dimensions while maintaining font sizes and styles.
  * Labeling panels per the publication's standards.

## Installation

The easiest way to install matplotlib-publishutil is by using `pip`:

```bash
# to install the lastest release (from PyPI)
pip install matplotlib-publishutil

# to install the latest commit (from GitHub)
pip install git+https://github.com/tommct/matplotlib-publishutil.git
```

## Tutorial and Examples

### Figure size by columns

The following shows how we might scale an image for publication in [Nature]
(https://www.nature.com/documents/nature-final-artwork.pdf), passing in 
different parameters to `FigureLayout.get_figsize()`.

The configuration file for *Nature* contains the following values for figsize:

    figsize:
        column_width: 89
        gutter_width: 5
        max_width: 183
        max_height: 247
        units: 'mm'

Here are a few scenarios for `FigureLayout.get_figsize()`:

```python
import matplotlib.pyplot as plt
from publishutil.figurelayout import FigureLayout

fig_layout = FigureLayout('nature')
print(f'Full page: {fig_layout.get_figsize(width_proportion=1., height=1.)}')
print(f'Alternative Full page: {fig_layout.get_figsize(n_columns=2, height=1.)}')
print(f'Half page: {fig_layout.get_figsize(width_proportion=1., height=.5)}')
print(f'One column: Golden Ratio Height: {fig_layout.get_figsize(n_columns=1)}')
print(f'One column: 16:9 aspect: {fig_layout.get_figsize(n_columns=1, wh_ratio=16/9)}')
```

Which provides the following output:

```
Full page: (7.204724409448819, 9.724409448818898)
Alternative Full page: (7.204724409448819, 9.724409448818898)
Half page: (7.204724409448819, 4.862204724409449)
One column: Golden Ratio Height: (3.5039370078740157, 2.16555216530475)
One column: 16:9 aspect: (3.5039370078740157, 1.970964566929134)
```

Any of these approaches can be passed as the `figsize` arguments when creating
a Matplotlib figure. E.g. 
`fig, ax = plt.subplots(figsize=fig_layout.get_figsize(n_columns=1))`.

### Panel Labels

To provide panel labels into the figure using our selected style, one has to 
set an axes object to be labeled with a "panel_label" attribute, as in:

```python
ax.panel_label = 'A'
```

This is an external, unrecognized attribute to matplotlib so calling 
`ax.set({'panel_label': 'A'})` will result in an error and one has to follow 
the approach above. Also note that it is not necessary to label every axes. 
If you do not give an axes object a `panel_label` attribute, it will not get 
drawn.

The following example comes from [this matplotlib demo]
(https://matplotlib.org/stable/tutorials/intermediate/gridspec.html):

```python
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
```

After exexuting the code above, if for some reason we may want to perform 
further editing of the labels, they are available in the `fig.texts` list.

This particular example is useful as it shows that even though we supplied
simply uppercase letters, the *Nature* style makes them 8-point, sans-serif,
lowercased, bold.

The placement of each panel label is in the upper left of each axes [tightbox]
(https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.get_tightbbox.html).
Adjustments, in points, can be performed by modifying the `shift` argument.
For example, to shift each label 10 pixels to the left and 2 pixels up:

```python
fig_layout.draw_panel_labels(fig, shift=(-10,2))
```

### List of available layout styles

To determine the list of named styles, simply call `FigureLayout.available`.

### Customizing your own layout style

To add your own style, simply make a YAML file in a format similar to those
in the *figure_layouts* folder. Supply the full or relative path to this
file as the `name` parameter when creating a `FigureLayout` object and you
should be good to go.

### Adding your own layout style to the repo

This tool is generally easy to use, especially if on can simply give a name
to a layout style file. If you have created a style file (or enhanced an
existing one), please add it to the repo! The easiest way is to 
[create an issue](https://github.com/tommct/matplotlib-publishutil/issues) and
paste in your template file. Alternatively, if you have code changes, feel free
to fork a branch and create a pull request to merge your changes.

### Using with Matplotlib styles

This package is independent of other [Matplotlib Styles]
(https://matplotlib.org/stable/gallery/style_sheets/style_sheets_reference.html).
However, one may find styles such as those in [SciencePlots]
(https://github.com/garrettj403/SciencePlots) to be complementary to the
layout styles here. For example, one could use the `nature` layout here
while using the `nature` Matplotlib style for a consistent look.
