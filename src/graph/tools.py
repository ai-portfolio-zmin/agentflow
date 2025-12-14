from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
from src.graph.state import AgentState
import yfinance as yf
from src.graph.plan_tools import *

from src.graph.util import get_price_data_path, get_chart_path


def calculate_return_runtime(ticker: str,
                             period: str,
                             agent_state: AgentState) -> dict:
    price_data_path = get_price_data_path(ticker, agent_state['run_id'])
    daily_price = pd.read_parquet(price_data_path).squeeze()
    current_date = daily_price.index[-1]
    if period[-1] == 'y':
        time_delta = relativedelta(years=int(period[:-1]))
    elif period[-1] == 'm':
        time_delta = relativedelta(months=int(period[:-1]))
    elif period[-1] == 'd':
        time_delta = relativedelta(days=int(period[:-1]))
    start_date = current_date - time_delta
    price = daily_price.loc[start_date:]
    return {'execution_result':
                {ticker:
                     {f'return_{period}': float(price.iloc[-1] / price.iloc[0] - 1)}
                 },
            'execution_status': [f'{period} return calculation of {ticker} status: success']
            }


def calculate_vol_runtime(ticker: str,
                          period: str,
                          agent_state: AgentState) -> dict:
    price_data_path = get_price_data_path(ticker, agent_state['run_id'])
    daily_price = pd.read_parquet(price_data_path).squeeze()
    if daily_price is None:
        raise ValueError(f'the daily price for {ticker} is missing')
    current_date = daily_price.index[-1]
    if period[-1] == 'y':
        time_delta = relativedelta(years=int(period[:-1]))
    elif period[-1] == 'm':
        time_delta = relativedelta(months=int(period[:-1]))
    elif period[-1] == 'd':
        time_delta = relativedelta(days=int(period[:-1]))
    else:
        raise ValueError(f'unsupported period: {period}')
    start_date = current_date - time_delta
    price = daily_price.loc[start_date:]
    return {'execution_result':
                {ticker: {f'vol_{period}': float(price.pct_change().std() * 252 ** 0.5)}
                 },
            'execution_status': [f'status for {period} volatility calculate of {ticker}: success']
            }


def get_stock_price_runtime(ticker: str,
                            period: str,
                            agent_state: AgentState) -> dict:
    if period[-1] == 'm':
        period = period + 'o'
    df = yf.download(ticker, period=period)
    df.columns = df.columns.droplevel(1)

    fpath = get_price_data_path(ticker, agent_state['run_id'])
    df[['Close']].to_parquet(fpath)

    return {'data': {ticker: str(fpath)},
            'execution_status': [f'load {period} price data for {ticker} status: success']
            }


def plot_runtime(ticker: str,
                 agent_state: AgentState) -> dict:
    price_data_path = get_price_data_path(ticker, agent_state['run_id'])
    time_series = pd.read_parquet(price_data_path).squeeze()
    if len(time_series) == 0:
        raise ValueError(f'the price data for {ticker} is missing')
    fig, ax = plt.subplots()
    time_series.plot(ax=ax)

    fpath = get_chart_path(ticker, agent_state['run_id'])

    plt.savefig(fpath)
    plt.close(fig)

    return {'execution_result':
                {ticker: {'chart': {'status': 'ok',
                                    'path': str(fpath)
                                    }
                          }
                 },
            'execution_status': [f'chat plot for {ticker} status: success']
            }


tools = [calculate_return_runtime,
         calculate_vol_runtime,
         get_stock_price_runtime,
         plot_runtime]
tool_names = [t.__name__ for t in tools]
plan_tools = [plan_calculate_return,
              plan_calculate_vol,
              plan_get_stock_price,
              plan_plot]
plan_tool_names = [t.__name__ for t in plan_tools]

TOOLS_REGISTRY = {}
PLAN_TOOL_NAME_MAP = {}
PLAN_TOOL_TOOL_MAP = {}
PLAN_TOOL_MAP = {}
for tool, plan_tool in zip(tools, plan_tools):
    assert '_'.join(tool.__name__.split('_')[:-1]) == '_'.join(
        plan_tool.__name__.split('_')[1:]), 'tool and plan too mismatch'
    PLAN_TOOL_NAME_MAP[plan_tool.__name__] = tool.__name__
    PLAN_TOOL_TOOL_MAP[plan_tool.__name__] = plan_tool
    PLAN_TOOL_MAP[plan_tool.__name__] = tool
    TOOLS_REGISTRY[tool.__name__] = tool
