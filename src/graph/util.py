import json
from pathlib import Path

from src.graph.state import AgentState


def get_next_run_id(agent_state:AgentState):
    data_dir = get_data_dir()
    folder_names = [dir_name for dir_name in data_dir.iterdir() if agent_state['mode'] in str(dir_name)]
    if len(folder_names)==0:
        return agent_state['mode']+f"_{1:04d}"
    else:
        max_num = max([int(str(folder_name).split('_')[-1]) for folder_name in folder_names])
        return agent_state['mode'] + f'_{max_num+1:04d}'


def save_state(agent_state:AgentState):
    state_path = get_state_path(agent_state['run_id'])
    with open(state_path,'w') as f:
        f.write(json.dumps(agent_state,indent=2, default=str))


def load_state(run_id:str):
    state_path = get_state_path(run_id)
    with open(state_path,'r',encoding='utf-8') as f:
        agent_state = json.loads(f.read())
    return agent_state


def get_price_data_path(ticker, run_id):
    fname = f"{ticker}.parquet"
    path = Path.cwd().parent.parent / 'data' / run_id
    path.mkdir(parents=True, exist_ok=True)
    fpath = path / fname
    return fpath


def get_chart_path(ticker, run_id):
    fname = f"{ticker}.png"
    path = Path.cwd().parent.parent / 'data' / run_id
    path.mkdir(parents=True, exist_ok=True)
    fpath = path / fname
    return fpath


def get_state_path(run_id):
    path = Path.cwd().parent.parent / 'data' / run_id
    path.mkdir(parents=True, exist_ok=True)
    fpath = path / 'state.json'
    return fpath


def get_data_dir():
    path = Path.cwd().parent.parent / 'data'
    return path


def gemini_json(response:str):
    return json.loads(response.replace('```json','').replace('```','').strip())
