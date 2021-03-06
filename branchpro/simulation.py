#
# SimulationController Class
#
# This file is part of BRANCHPRO
# (https://github.com/SABS-R3-Epidemiology/branchpro.git) which is released
# under the BSD 3-clause license. See accompanying LICENSE.md for copyright
# notice and full license details.
#

import numpy as np

from branchpro import ForwardModel


class SimulationController:
    """SimulationController Class:
    Class for the simulation of models in any of the subclasses in the
    ``ForwardModel``.

    Parameters
    ----------
    model
        (ForwardModel) Instance of the :class:`ForwardModel` class used for
        the simulation.
    start_sim_time
        (integer) Time from which we start running the SimulationController.
    end_sim_time
        (integer) Time at which we stop running the SimulationController.

    Notes
    -----
    Always apply method switch_resolution before calling
    :meth:`SimulationController.run` for a change of resolution!

    """

    def __init__(self, model, start_sim_time, end_sim_time):
        if not isinstance(model, ForwardModel):
            raise TypeError(
                'Model needs to be a subclass of the branchpro.ForwardModel')

        self.model = model
        start_sim_time = int(start_sim_time)
        end_sim_time = int(end_sim_time)
        self._sim_end_points = (start_sim_time, end_sim_time)

        # Set default regime 'simulate in full'
        self._regime = np.arange(
            start=start_sim_time, stop=end_sim_time+1).astype(int)

    def switch_resolution(self, num_points):
        """
        Change the number of points we wish to keep from our simulated sample
        of incidences.

        Parameters
        ----------
        num_points
            (integer) number of points we wish to keep from our simulated
            sample of incidences.

        """
        start_sim_time, end_sim_time = self._sim_end_points
        self._regime = np.rint(np.linspace(
            start_sim_time, end_sim_time, num=num_points)).astype(int)

    def get_regime(self):
        """
        Gets all time point the simulation uses.
        """
        return self._regime

    def get_time_bounds(self):
        """
        Gets time bounds of the simulation as a tuple with start and end time
        of the simulation.
        """
        return self._sim_end_points

    def run(self, parameters):
        """
        Operates the ``simulate`` method present in any subclass of the
        ``ForwardModel``.

        Parameters
        ----------
        parameters
            An ordered sequence of parameter values.

        """
        return self.model.simulate(parameters, self._regime)
