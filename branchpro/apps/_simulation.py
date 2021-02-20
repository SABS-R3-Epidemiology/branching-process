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

import numpy as np
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
        super().__init__()
        self.session_data = {'data_storage': None, 'sim_storage': None}

        self.app = dash.Dash(__name__, external_stylesheets=self.css)
        self.app.title = 'BranchproSim'

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
                            dcc.Graph(
                                figure=bp.IncidenceNumberPlot().figure,
                                id='myfig')
                        ]),
                        dbc.Col(
                            self.update_sliders(), id='all-sliders')
                    ], align='center'),
                    html.H4([
                        'You can upload your own incidence data here. It will'
                        'appear as bars, while the simulation will be a line.'
                    ]),
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div([
                            'Drag and Drop or ',
                            html.A('Select Files',
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
                        multiple=True  # Allow multiple files to be uploaded
                    ),
                    html.Div(id='incidence-data-upload'),
                    html.Div([]),  # Empty div for bottom text
                    html.Div(id='data_storage', style={'display': 'none'}),
                    html.Div(id='sim_storage', style={'display': 'none'})
                    ], fluid=True),
                mathjax_script
                ])

        # Set the app index string for mathjax
        self.app.index_string = 'fix this'

    def update_sliders(self,
                       init_cond=10.0,
                       r0=2.0,
                       r1=0.5,
                       magnitude_init_cond=None):
        """Generate sliders for the app.

        This method tunes the bounds of the sliders to the time period and
        magnitude of the data.

        Parameters
        ----------
        init_cond : int
            start position on the slider for the number of initial cases for
            the Branch Pro model in the simulator.
        r0 : float
            start position on the slider for the initial reproduction number
            for the Branch Pro model in the simulator.
        r1 : float
            start position on the slider for the second reproduction number for
            the Branch Pro model in the simulator.
        magnitude_init_cond : int
            maximal start position on the slider for the number of initial
            cases for the Branch Pro model in the simulator. By default, it
            will be set to the maximum value observed in the data.

        Returns
        -------
        html.Div
            A dash html component containing the sliders
        """
        data = self.session_data['data_storage']

        # Calculate slider values that depend on the data
        if data is not None:
            if magnitude_init_cond is None:
                magnitude_init_cond = max(data['Incidence Number'])
            bounds = (1, max(data['Time']))

        else:
            # choose values to use if there is no data
            if magnitude_init_cond is None:
                magnitude_init_cond = 10
            bounds = (1, 30)

        mid_point = round(sum(bounds) / 2)

        # Make new sliders
        sliders = bp._SliderComponent()
        sliders.add_slider(
            'Initial Cases', 'init_cond', init_cond, 0.0, magnitude_init_cond,
            1, as_integer=True)
        sliders.add_slider('Initial R', 'r0', r0, 0.1, 10.0, 0.01)
        sliders.add_slider('Second R', 'r1', r1, 0.1, 10.0, 0.01)
        sliders.add_slider(
            'Time of change', 't1', mid_point, bounds[0], bounds[1], 1,
            as_integer=True)

        return sliders.get_sliders_div()

    def update_figure(self):
        """Generate a plotly figure of incidence numbers and simulated cases.

        Returns
        -------
        plotly.Figure
            Figure with updated data and simulations
        """
        data = self.session_data['data_storage']
        simulations = self.session_data['sim_storage']
        num_simulations = len(simulations.columns) - 1

        plot = bp.IncidenceNumberPlot()
        plot.add_data(data)

        # Keeps traces visibility states fixed when changing sliders
        plot.figure['layout']['legend']['uirevision'] = True

        for sim in range(num_simulations):
            plot.add_simulation(simulations[['Time', 'sim{}'.format(sim + 1)]])

            # Unless it is the most recent simulation, decrease the opacity to
            # 25% and remove it from the legend
            if sim < num_simulations - 1:
                plot.figure['data'][-1]['line'].color = 'rgba(255,0,0,0.25)'
                plot.figure['data'][-1]['showlegend'] = False

        return plot.figure

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
        Clears all simulations currently plotted in the figure and adds
        one fitted for the current parameters of the sliders.
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
        """Run a simulation of the branchpro model at the given slider values.

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

        Returns
        -------
        str
            Simulations storage dataframe in JSON format
        """
        data = self.session_data['data_storage']
        simulations = self.session_data['sim_storage']
        times = data['Time']

        # Add the correct R profile to the branchpro model
        br_pro_model = bp.BranchProModel(new_r0, np.array([1, 2, 3, 2, 1]))
        br_pro_model.set_r_profile([new_r0, new_r1], [0, new_t1])

        # Generate one simulation trajectory from this model
        simulation_controller = bp.SimulationController(
            br_pro_model, 1, len(times))
        data = simulation_controller.run(new_init_cond)

        # Add data to simulations storage
        num_sims = len(simulations.columns)
        simulations['sim{}'.format(num_sims)] = data

        return simulations.to_json()
