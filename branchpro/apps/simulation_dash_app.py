#
# Dash app
#
# This file is part of BRANCHPRO
# (https://github.com/SABS-R3-Epidemiology/branchpro.git) which is released
# under the BSD 3-clause license. See accompanying LICENSE.md for copyright
# notice and full license details.
#
"""This is an app which shows forward simulation of the branching process model
with fixed example data. To run the app, use ``python dash_app.py``.
"""

import os

import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

import branchpro as bp
from branchpro.apps import IncidenceNumberSimulationApp


app = IncidenceNumberSimulationApp()
full_ffd = bp.DatasetLibrary().french_flu()
small_ffd = full_ffd.query('year == 2020')
french_flu_data = pd.DataFrame({
            'Weeks': small_ffd['week'],
            'Incidence Number': small_ffd['inc']
        })

sliders = ['init_cond', 'r0', 'r1', 't1']

# Add the explanation texts
fname = os.path.join(os.path.dirname(__file__), 'data', 'dash_app_text.md')
with open(fname) as f:
    app.add_text(dcc.Markdown(f.read(), dangerously_allow_html=True))

fname = os.path.join(os.path.dirname(__file__),
                     'data',
                     'dash_app_collapsible_text.md')
with open(fname) as f:
    app.add_collapsed_text(dcc.Markdown(f.read(), dangerously_allow_html=True))

# Get server of the app; necessary for correct deployment of the app.
server = app.app.server


@app.app.callback(
    Output('incidence-data-upload', 'children'),
    Output('data_storage', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
)
def load_data(*args):
    """Load data from a file and save it in storage.
    """
    list_contents, list_names = args

    with app.lock:
        if list_contents is not None:
            # Run content parser for each file and get message
            # Only use latest file
            message, data = app.parse_contents(list_contents[-1], list_names[-1])

            if data is None:
                # The file could not be loaded, so keep the current data and
                # try to prevent updates to any other part of the app
                return message, dash.no_update

            data = data.to_json()

        else:
            message = html.Div(['No data file selected.'])
            data = french_flu_data.to_json()

        return message, data


@app.app.callback(
    Output('all-sliders', 'children'),
    Input('data_storage', 'children'),
)
def update_slider_ranges(*args):
    """Update sliders when a data file is uploaded.
    """
    data = french_flu_data if args[0] is None else args[0]
    with app.lock:
        app.refresh_user_data_json(data_storage=data)
        return app.update_sliders()

@app.app.callback(
    Output('myfig', 'figure'),
    Input('data_storage', 'children'),
    Input('sim_storage', 'children'),
    State('myfig', 'figure'),
)
def update_figure(*args):
    """Handles all updates to the incidence number figure.
    """
    ctx = dash.callback_context
    source = ctx.triggered[0]['prop_id'].split('.')[0]
    current_figure = args[2]

    with app.lock:
        app.refresh_user_data_json(data_storage=args[0], sim_storage=args[1])

        new_figure_needed = False
        if source == 'data_storage' or \
                (len(current_figure['data']) > 2 and \
                 len(app.session_data['sim_storage'].columns) == 2):
            return app.update_figure()

        elif len(current_figure['data']) == 2 and len(app.session_data['sim_storage'].columns) == 2:
            return app.update_figure_change_values(current_figure)

        else:
            return app.update_figure_add_simulation(current_figure)


@app.app.callback(
    Output('sim_storage', 'children'),
    Input('sim-button', 'n_clicks'),
    Input('data_storage', 'children'),
    [Input(s, 'value') for s in sliders],
    State('sim_storage', 'children'),
)
def run_simulation(*args):
    """Run simulation based on slider values, simulation button, or new data.
    """
    n_clicks, data_json, init_cond, r0, r1, t1, sim_json = args

    with app.lock:
        app.refresh_user_data_json(
            data_storage=data_json, sim_storage=sim_json)

        # In all cases except a click of the add new simulation buttom, we
        # want to remove all previous simulation traces from the figure
        ctx = dash.callback_context
        source = ctx.triggered[0]['prop_id'].split('.')[0]
        if source != 'sim-button':
            app.clear_simulations()

        return app.update_simulation(init_cond, r0, r1, t1).to_json()


@app.app.callback(
    Output('collapsedtext', 'is_open'),
    [Input('showhidebutton', 'n_clicks')],
    [State('collapsedtext', 'is_open')],
)
def toggle_hidden_text(num_clicks, is_it_open):
    """
    Switches the visibility of the hidden text.
    """
    if num_clicks:
        return not is_it_open
    return is_it_open


if __name__ == "__main__":
    app.app.run_server(debug=True)
