import inspect
import re

from src.graph.tools import plan_tool_names, PLAN_TOOL_TOOL_MAP


def check_parameters(func:callable, params:dict):
    msg = []
    signiture = inspect.signature(func)
    function_params = {}
    for name, t in signiture.parameters.items():
        function_params[name] = t.annotation
        # check the required parameters in the input
        if t.default is inspect._empty:
            if not name in params:
                msg.append(f'{func.__name__}: parameter {name} required but not seen')

    #check the input parameter is function input and type matches
    for name in params.keys():
        if not name in function_params:
            msg.append(
                f'{func.__name__}: {name} not a function input')
            continue
        else:
            if not isinstance(params[name], function_params[name]):
                msg.append(
                    f'{func.__name__}: input type for {name} doesnt match function signiture, expect {function_params[name]}, get {type(params[name])}')
    return msg


def check_data_availability(plans):
    msg = []
    data_seen = set()
    for plan in plans:

        ticker = plan['params']['ticker']
        if plan['action'] == 'plan_get_stock_price':
            data_seen.add(ticker)
        elif plan['action'] in ['plan_calculate_vol', 'plan_calculate_return', 'plan_plot']:
            if not ticker in data_seen:
                msg.append(
                    f'data for {ticker} not seen, use plan_get_stock_price to get the data, period needs to be equal to or longer than the period required for metrics calculations')
    msg = list(set(msg))
    return msg


def check_plans(plans: list):
    msg = []
    invalid_functions = []
    ## check the actions are valid
    for plan in plans:
        func = plan['action']
        if not func in plan_tool_names:
            invalid_functions.append(func)
            msg.append(f'tool "{func}"  suggested by planner not available in the tools list')

    ## check function signiture
    for plan in plans:
        func = plan['action']
        if not func in invalid_functions:
            msg = msg + check_parameters(PLAN_TOOL_TOOL_MAP[func], plan['params'])


    ## check data availability
    msg = msg + check_data_availability(plans)

    ## check period
    for plan in plans:
        period = plan['params'].get('period')
        if period:
            pattern = '^\d{1,2}(d|m|y)$'
            if not bool(re.match(pattern, period)):
                func = plan['action']
                ticker = plan['params'].get('ticker')
                msg.append(
                    f'period for func {func} and ticker {ticker} must follow 1d, 2m, or 1y')

    return msg
