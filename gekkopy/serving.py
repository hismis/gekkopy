from abc import abstractmethod
from typing import Dict, Any, Optional

import numpy as np
from flask import Flask, request, abort

app = Flask("strat_server")


def _try_get_strat(name):
    try:
        return StratServer.get(name)
    except KeyError:
        abort(404)


@app.route("/strats/<strat_name>/window_size")
def window_size(strat_name):
    strat = _try_get_strat(strat_name)
    return {"window_size": strat.window_size()}


@app.route("/strats/<strat_name>/protocol_version")
def protocol_version(strat_name):
    strat = _try_get_strat(strat_name)
    return {"protocol_version": strat.protocol_version()}


@app.route("/strats/<strat_name>/advice", methods=["POST"])
def advice(strat_name):
    """ Creates a recommendations for the data in the request body.

    Expects request data of mimetype application/json. Data must be a dictionary
    with the following keys:

    * ``data``: list of lists, where each row contains the 6 values for
      [open, high, low, close, volume, avg_weighted_price].

    Returns:
    ========
    advice
        Dictionary with mandatory keys:

        * ``advice``: one of "long", "short" or "hold"

    The strategy may add additional keys.
     """
    strat = _try_get_strat(strat_name)
    raw_data = request.get_json()
    data = np.array(raw_data)
    return {"advice": strat.advice(data)}


class Strategy:
    """ Abstract class template for serving strategies. """

    LONG = "long"
    SHORT = "short"
    HOLD = "hold"

    COLUMNS = ["open", "high", "low", "close", "volume", "trades"]

    @abstractmethod
    def window_size(self):
        """ Return the window size of the strategy, i.e., how many candles the
         strategy needs to make a prediction. """
        raise NotImplementedError

    @abstractmethod
    def advice(self, data):
        """ Create a recommended action for the given data.

        Must create a single prediction for the *last* candle in the input.


        Parameters
        ----------
        data: np.array
            Candle data with columns
            [open, high, low, close, volume, avg_weighted_price].
            Shape: [>=window_size, 6]

        Returns
        -------
        recommendation: Dict[str, Any]
            recommendation. Must-have keys:

            * 'action': one of 'buy', 'sell', 'hold'

            Additional keys can be added, but don't have a special function.
        """
        raise NotImplementedError

    @abstractmethod
    def protocol_version(self):
        """ Protocol version. Should be 1 at the moment. Might be increased in later
        version of the framework to indicate API changes. """
        return 1


class StratServer:
    """ Class that manages strategies and starts the webserver."""

    strats = {}

    @classmethod
    def register(cls, name: str, strat: Strategy):
        """ Registers a strategy. """
        cls.strats[name] = strat

    @classmethod
    def get(cls, name: str) -> Optional[Strategy]:
        """ Retrieves a strategy """
        if name in cls.strats:
            return cls.strats[name]
        raise KeyError(f"No strategy with name {name} is registered")

    @classmethod
    def start(cls, debug=False, host="localhost", port=2626):
        """ Starts the flask server. Default port is 2626 on localhost. """
        app.run(debug=debug, host=host, port=port)