#
# ReproductionNumberPlot Class
#
# This file is part of BRANCHPRO
# (https://github.com/SABS-R3-Epidemiology/branchpro.git) which is released
# under the BSD 3-clause license. See accompanying LICENSE.md for copyright
# notice and full license details.
#

import warnings
import pandas as pd
import plotly.graph_objs as go


class ReproductionNumberPlot():
    """ReproductionNumberPlot Class
    Stores the main figure for the Dash app.
    """
    def __init__(self):
        self.figure = go.Figure()

    def _label_warning(self, time_key, r_key):
        x_label = self.figure['layout']['xaxis']['title']['text']
        y_label = self.figure['layout']['yaxis']['title']['text']
        if (x_label is not None) and (y_label is not None):
            if (x_label != time_key) or (y_label != r_key):
                warnings.warn('Labels do not match. They will be updated.')

    def add_ground_truth_rt(self, df, time_key='Time Points', r_key='R_t'):
        """
        Plots the true values of R_t as a line on the figure.

        Parameters
        ----------
        df
            (pandas DataFrame) contains the true values of the reproduction
            number by days. Data stored in columns 'Time Points' and 'R_t',
            respectively.
        time_key
            x-axis label for the line plot.
        r_key
            y-axis label for the line plot.
        """
        if not issubclass(type(df), pd.DataFrame):
            raise TypeError('df needs to be a dataframe')
        self._label_warning(time_key, r_key)

        trace = go.Scatter(
            y=df[r_key],
            x=df[time_key],
            mode='lines',
            name='True R',
            line_color='green'
        )

        self.figure.add_trace(trace)
        self.figure.update_layout(
            xaxis_title=time_key,
            yaxis_title=r_key)

    def add_interval_rt(
            self, df, time_key='Time Points', r_key='Mean',
            lr_key='Lower bound CI', ur_key='Upper bound CI',
            cp_key='Central Probability'):
        """
        Plots the estimated values of R_t as a line on the figure, as well
        as an area of confidence for the location of the true value.

        Parameters
        ----------
        df
            (pandas DataFrame) contains the posterior mean with percentiles
            over time. Data stored in columns 'Time Points', 'Mean',
            'Lower bound CI', 'Upper bound CI', respectively.
        time_key
            x-axis label for the line plot.
        r_key
            y-axis label for the line plot.
        lr_key
            dataframe label for the lower bound of the credible interval of
            r.
        ur_key
            dataframe label for the upper bound of he credible interval of
            r.
        cp_key
            dataframe label for the central probability of the credible
            interval of r.
        """
        if not issubclass(type(df), pd.DataFrame):
            raise TypeError('df needs to be a dataframe')
        self._label_warning(time_key, r_key)

        trace1 = go.Scatter(
            y=df[r_key],
            x=df[time_key],
            mode='lines',
            name='Estimated R',
            line_color='indigo'
        )

        trace2 = go.Scatter(
            x=list(df[time_key]) + list(df[time_key])[::-1],
            y=list(df[ur_key]) + list(df[lr_key])[::-1],
            fill='toself',
            fillcolor='indigo',
            line_color='indigo',
            opacity=0.5,
            name='Credible interval ' + str(df[cp_key][0]),
        )

        self.figure.add_trace(trace1)
        self.figure.add_trace(trace2)

        self.figure.update_layout(
            xaxis_title=time_key,
            yaxis_title='R',
            hovermode='x unified')

    def update_labels(self, time_label=None, r_label=None):
        """
        Updates the figure labels with user inputed values.

        Parameters
        ----------
        time_label
            x-axis label for the line plot.
        r_label
            y-axis label for the line plot.
        """
        if time_label is not None:
            self.figure.update_layout(xaxis_title=time_label)

        if r_label is not None:
            self.figure.update_layout(yaxis_title=r_label)

    def show_figure(self):
        """
        Shows current figure.
        """
        self.figure.show()