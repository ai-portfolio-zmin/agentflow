from typing import Union, Dict
import pandas as pd


def plan_calculate_return(ticker: str,
                          period: str) -> dict:
    """
    function used for llm planning, this function calculates stock
    returns based on ticker(name) and time period, using this function when asked about:
    - return
    - performance
    - etc
    :param ticker: stock ticker, e.g. MSFT, APPLE
    :param period: time period, for example 1y, 3m ,5d
    :return:
    """


def plan_calculate_vol(ticker: str,
                       period: str) -> dict:
    """
    function used for llm planning, this function calculates stock
    volatilities based on ticker(name) and time period, use this when asked about:
    - risk
    - vol/volatility
    :param ticker: stock ticker, e.g. MSFT, APPLE
    :param period: time period, for example 1y, 3m ,5d
    :return:
    """


def plan_get_stock_price(ticker: str,
                         period: str,
                         ) -> Dict[str, Union[pd.DataFrame, None]]:
    """
    function used for llm planning, this function gets stock price
    given ticker and time period
    :Parameters:
        tickers : str, e.g. AAPL, MSFT
        period : str
            Valid periods: 1d,5d,1m,3m,6m,1y,2y,5y,10y
    :return:
    """


def plan_plot(ticker: str) -> dict:
    """
    function used for llm planning, this function plots the stock price for a ticker
    :param ticker: : str, e.g. AAPL, MSFT
    :return:
    """
