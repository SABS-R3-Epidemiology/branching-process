#
# SimulationApp
#
# This file is part of BRANCHPRO
# (https://github.com/SABS-R3-Epidemiology/branchpro.git) which is released
# under the BSD 3-clause license. See accompanying LICENSE.md for copyright
# notice and full license details.
#

import base64
import io
import os

import pandas as pd
import dash_defer_js_import as dji  # For mathjax
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

import branchpro as bp


# Import the mathjax
mathjax_script = dji.Import(
    src='https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/latest.js'
        '?config=TeX-AMS-MML_SVG')

# Write the mathjax index html
# https://chrisvoncsefalvay.com/2020/07/25/dash-latex/
index_str_math = """<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            <script type="text/x-mathjax-config">
            MathJax.Hub.Config({
                tex2jax: {
                inlineMath: [ ['$','$'],],
                processEscapes: true
                }
            });
            </script>
            {%renderer%}
        </footer>
    </body>
</html>
"""


class IncidenceNumberSimulationApp:
    """IncidenceNumberSimulationApp Class:
    Class for the simulation dash app with figure and sliders for the
    BranchPro models.
    """
    def __init__(self):
        self.app = dash.Dash(
            __name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.app.title = 'BranchproSim'
        self.plot = bp.IncidenceNumberPlot()

        # Keeps traces visibility states fixed when changing sliders
        self.plot.figure['layout']['legend']['uirevision'] = True
        self.sliders = bp._SliderComponent()

        self.app.layout = \
            html.Div([
                dbc.Container([
                    html.H1('Branching Processes'),
                    html.Div([]),  # Empty div for top explanation texts
                    dbc.Row([
                        dbc.Col([
                            html.Button(
                                'Add new simulation',
                                id='sim-button',
                                n_clicks=0),
                            dcc.Graph(figure=self.plot.figure, id='myfig')]
                            ),
                        dbc.Col(
                            self.sliders.get_sliders_div(), id='all-sliders')
                            ],
                            align='center'
                            ),
                    html.H4(['You can upload your own incidence data here. It \
                        will appear as bars, while the simulation will be a \
                        line.']),
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            'Drag and Drop or ',
                            html.A(
                                'Select Files',
                                style={'text-decoration': 'underline'}),
                            ' to upload your Incidence Number data.'
                        ]),
                        style={
                            'width': '100%',
                            'height': '60px',
                            'lineHeight': '60px',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            'textAlign': 'center',
                            'margin': '10px'
                        },
                        # Allow multiple files to be uploaded
                        multiple=True
                    ),
                    html.Div(id='incidence-data-upload'),
                    html.Div([])], fluid=True),  # Empty div for bottom text
                mathjax_script])

        # Set the app index string for mathjax
        self.app.index_string = index_str_math

        self.current_df = None

    def add_text(self, text):
        """Add a block of text at the top of the app.

        This can be used to add introductory text that everyone looking at the
        app will see right away.

        Parameters
        ----------
        text
            The text to add to the html div
        """
        self.app.layout.children[0].children[1].children.append(text)

    def add_collapsed_text(self, text, title='More details...'):
        """Add a block of collapsible text at the bottom of the app.

        By default, this text will be hidden. The user can click on a button
        with the specified title in order to view the text.

        Parameters
        ----------
        text
            The text to add to the html div
        title
            str which will be displayed on the show/hide button
        """
        collapse = html.Div([
                dbc.Button(
                    title,
                    id='showhidebutton',
                    color='primary',
                ),
                dbc.Collapse(
                    dbc.Card(dbc.CardBody(text)),
                    id='collapsedtext',
                ),
            ])
        self.app.layout.children[0].children[-1].children.append(collapse)

    def parse_contents(self, contents, filename):
        """
        Opens user-uploaded file and passes its content to a pandas
        Dataframe format, returning to the user the name of the file that
        has been used.
        """
        self.current_df = None

        content_type, content_string = contents.split(',')
        _, extension = os.path.splitext(filename)

        decoded = base64.b64decode(content_string)
        try:
            if extension in ['.csv', '.txt']:
                # Assume that the user uploaded a CSV or TXT file
                df = pd.read_csv(
                    io.StringIO(decoded.decode('utf-8')))
            else:
                return html.Div(['File type must be CSV or TXT.'])
        except Exception as e:
            print(e)
            return html.Div([
                'There was an error processing this file.'
            ])

        if ('Time' not in df.columns) or (
                'Incidence Number' not in df.columns):
            return html.Div(['Incorrect format; file must contain a `Time` \
                and `Incidence Number` column.'])
        else:
            self.current_df = df

            return html.Div(['Loaded data from: {}'.format(filename)])

    def add_data(
            self, df=None, time_label='Time', inc_label='Incidence Number'):
        """
        Adds incidence data to the plot in the dash app.

        Parameters
        ----------
        df
            (pandas DataFrame) contains numbers of new cases by time unit.
            Data stored in columns of time and incidence number, respectively.
        time_label
            label key given to the temporal data in the dataframe.
        inc_label
            label key given to the incidental data in the dataframe.
        """
        if df is not None:
            self.current_df = df

        self.plot.add_data(
            self.current_df, time_key=time_label, inc_key=inc_label)

        # Save the labels incidence figure for later update
        self._time_label = time_label
        self._inc_label = inc_label

    def add_simulator(self,
                      simulator,
                      init_cond=10.0,
                      r0=2.0,
                      r1=0.5,
                      magnitude_init_cond=100.0):
        """
        Simulates an instance of a model, adds it as a line to the plot and
        adds sliders to the app.

        Parameters
        ----------
        simulator
            (SimulatorController) a BranchPro model and the time bounds
            between which you run the simulator.
        init_cond
            (int) start position on the slider for the number of initial
            cases for the Branch Pro model in the simulator.
        r0
            (float) start position on the slider for the initial reproduction
            number for the Branch Pro model in the simulator.
        r1
            (float) start position on the slider for the second reproduction
            number for the Branch Pro model in the simulator.
        magnitude_init_cond
            (int) maximal start position on the slider for the number of
            initial cases for the Branch Pro model in the simulator.
        """
        if not issubclass(type(simulator), bp.SimulationController):
            raise TypeError('Simulatior needs to be a SimulationController')

        model = simulator.model

        if not issubclass(type(model), bp.BranchProModel):
            raise TypeError('Models needs to be a BranchPro')

        bounds = simulator.get_time_bounds()
        mid_point = round(sum(bounds)/2)

        self.sliders.add_slider(
            'Initial Cases', 'init_cond', init_cond, 0.0, magnitude_init_cond,
            1, as_integer=True)
        self.sliders.add_slider('Initial R', 'r0', r0, 0.1, 10.0, 0.01)
        self.sliders.add_slider('Second R', 'r1', r1, 0.1, 10.0, 0.01)
        self.sliders.add_slider(
            'Time of change', 't1', mid_point, bounds[0], bounds[1], 1,
            as_integer=True)

        new_rs = [r0, r1]
        start_times = [0, mid_point]
        simulator.model.set_r_profile(new_rs, start_times)

        self._init_cond = init_cond

        data = simulator.run(self._init_cond)
        df = pd.DataFrame({
            'Time': simulator.get_regime(),
            'Incidence Number': data})

        self.plot.add_simulation(df)

        self.simulator = simulator

        # Save the simulated figure for later update
        self._graph = self.plot.figure['data'][-1]

    def get_sliders_ids(self):
        """
        Returns the IDs of all sliders accompaning the figure in the
        app.
        """
        return self.sliders.slider_ids()

    def add_simulation(self):
        """
        Adds new simulated graph in the figure for the current slider values.
        """
        data = self.simulator.run(self._init_cond)
        df = pd.DataFrame({
            'Time': self.simulator.get_regime(),
            'Incidence Number': data})

        self.plot.add_simulation(df)

        return self.plot.figure

    def clear_simulations(self):
        """
        Clears all simulations currently plotted in the figure.
        """
        self.plot = bp.IncidenceNumberPlot()
        # Keeps traces visibility states fixed when changing sliders
        self.plot.figure['layout']['legend']['uirevision'] = True

        self.add_data(
            df=self.current_df,
            time_label=self._time_label,
            inc_label=self._inc_label)

        self.plot.figure = self.add_simulation()

        return self.plot.figure

    def update_simulation(self, new_init_cond, new_r0, new_r1, new_t1):
        """
        Updates the model parameters in the simulator and the
        simulated graph in the figure.

        Parameters
        ----------
        new_init_cond
            (int) updated position on the slider for the number of initial
            cases for the Branch Pro model in the simulator.
        new_r0
            (float) updated position on the slider for the initial reproduction
            number for the Branch Pro model in the simulator.
        new_r1
            (float) updated position on the slider for the second reproduction
            number for the Branch Pro model in the simulator.
        new_t1
            (float) updated position on the slider for the time change in
            reproduction numbers for the Branch Pro model in the simulator.
        """
        new_rs = [new_r0, new_r1]
        start_times = [0, new_t1]

        model = self.simulator.model
        model.set_r_profile(new_rs, start_times)

        self._init_cond = new_init_cond

        data = self.simulator.run(self._init_cond)
        self._graph['y'] = data

        return self.plot.figure
