from src.graph.tools import PLAN_TOOL_NAME_MAP, TOOLS_REGISTRY, tool_names, plan_tools
from src.graph.state import AgentState
from src.graph.util import get_next_run_id, save_state, gemini_json
from src.graph.logger import get_logger
from src.graph.gemini_response import response
from src.graph.validation import check_plans
from dotenv import load_dotenv
from google.genai import types
from google import genai
import os

load_dotenv()

logger = get_logger('nodes')

api_key = os.getenv('GEMINI_API_KEY')
client = genai.Client(api_key=api_key)
config = types.GenerateContentConfig(tools=plan_tools, automatic_function_calling={"disable": True})

MAX_STEPS = 20


def status_update(node_func):
    def wrapper(agent_state: AgentState):
        result = node_func(agent_state)
        nsteps = agent_state.get('nsteps', 0)
        nsteps += 1
        call_stack = [node_func.__name__]
        return {**result,
                'nsteps': nsteps,
                'call_stack': call_stack}

    return wrapper


@status_update
def planner(agent_state: AgentState) -> dict:
    query = agent_state.get('query', '')
    plan_check_msg='NA'
    previous_plan ='NA'
    plan_checked = False
    if len(query) == 0:
        raise ValueError('Please input query')
    logger.info(f'query: {query}')
    max_trials = 3
    n_trials = 0
    while not plan_checked:
        prompt = f"""
                    You are an AI assistant who makes plans.
                    You make new plan if there's no previous plan.
                    You correct the previous plan if it exists, with the feedback from the validation failure

                    Rules:
                    1. you do NOT to answer the query directly.
                    2. you will create a structured plan, referencing ONLY the available tools in ordered sequence which can executed step by step
                    3. The output MUST be a JSON list of steps.
                    6. Each step must be an object with:
                       - "action": <tool name>
                       - "params": an object of arguments.

                    The available tools are:
                    {[t.__name__ for t in plan_tools]}

                    Query:
                    "{query}"

                    Previous plan:
                    {previous_plan}

                    validation failure on previous plan:
                    {plan_check_msg}

                    Return ONLY JSON, no text or explanation.
    """

        if agent_state['mode'] =='test':
            gemini_response = response['planner']
        else:
            plan_response = client.models.generate_content(model='gemini-2.5-flash',
                                                           contents=[prompt],
                                                           config=config)
            gemini_response = plan_response.text
        plans = gemini_json(gemini_response)
        plan_check_msg = check_plans(plans)
        if len(plan_check_msg)==0:
            plan_checked=True
            break
        n_trials +=1
        if n_trials>max_trials:
            break
    if not plan_checked: raise RuntimeError(f'plan {plans} failed validation due to {plan_check_msg}')
    logger.info(f'plans:\n{plans}')
    return {'plans': plans,
            'next_plan_index': 0}


def router(agent_state: AgentState) -> dict:
    """
    direct the current plan to the executor node or some other node
    :param agent_state:
    :return:
    """
    
    if not agent_state.get('mode'):
        agent_state['mode']='test'

    run_id = agent_state.get('run_id')
    if not run_id:
        run_id = get_next_run_id(agent_state)
        agent_state['run_id']= run_id
    
    #depends on run_id and mode
    save_state(agent_state)

    if agent_state.get('nsteps', 0) > MAX_STEPS:
        return {'next_node': 'END'}

    critic_status = agent_state.get('critic_result', {}).get('status')
    if critic_status == 'ok':
        return {'next_node': 'END'}
    elif critic_status == 'retry':
        return {'next_node': 'answer'}
    plans = agent_state.get('plans')
    if plans:
        next_plan_index = agent_state['next_plan_index']
        plan_not_finished = next_plan_index < len(plans)
        if plan_not_finished:
            next_step = plans[next_plan_index]
            action = next_step['action']
            tool_name = PLAN_TOOL_NAME_MAP.get(action)
            if tool_name in tool_names:
                return {'next_node': 'executor'}
            else:
                raise NotImplementedError(f'unknow tool name {tool_name}')
        else:  # when the plan from the planner is executed, we move to answer
            return {'next_node': 'answer'}
    else:
        return {'next_node': 'planner',
                'run_id':run_id}


@status_update
def executor(agent_state: AgentState) -> dict:
    """
    executor the current plan
    :param agent_state:
    :return:
    """
    next_plan_index = agent_state['next_plan_index']
    plans = agent_state.get('plans')

    next_step = plans[next_plan_index]
    action = next_step['action']
    tool_name = PLAN_TOOL_NAME_MAP.get(action)
    tool_func = TOOLS_REGISTRY[tool_name]
    kwargs = next_step['params'].copy()
    kwargs['agent_state'] = agent_state
    logger.info(f'executing plan: {next_step}')
    result = tool_func(**kwargs)
    next_plan_index = next_plan_index + 1
    return {**result,
            'next_plan_index': next_plan_index,
            }


@status_update
def answer(agent_state: AgentState) -> dict:
    query = agent_state.get('query')
    execution_result = agent_state.get('execution_result',{})

    retry = agent_state.get('critic_result',{}).get('status') =='retry'
    if retry:
        reason = agent_state.get('critic_result',{}).get('reason')
        prompt = f"""
                    You are a financial analyst.
                    You will answer the same question again based on the feedback from the critic


                    Rules:
                    1. you MUST only answer/reason/explain based on the context
                    2. dont make things up or hallucinate
                    3. answer in plain, human language
                    4. output a short and structured explanation

                    Query:
                    "{query}"

                    Context:
                    {execution_result}

                    Reason for retry:
                    {reason}

        """
    else:
        prompt = f"""
                    You are a financial analyst.
                    You answer questions based on the structured context


                    Rules:
                    1. you MUST only answer/reason/explaing based on the context
                    2. dont make things up or hallucinate
                    3. answer in plain, human language
                    4. output a short and structured explanation

                    Query:
                    "{query}"

                    Context:
                    {execution_result}

        """
    if agent_state['mode'] == 'test':
        draft_answer = response['answer']
    else:
        answer_response = client.models.generate_content(model='gemini-2.5-flash',
                                                         contents=prompt)
        draft_answer = answer_response.text

    logger.info(f'draft answer: {draft_answer}')
    return {'draft_answer': draft_answer}


@status_update
def critic(agent_state: AgentState) -> dict:
    query = agent_state['query']
    draft_answer = agent_state['draft_answer']
    prompt = f"""
                You are a critic.

                your goal is to check if the draft answer answers the query

                check:
                1. whether the answer addresses the query
                2. check the scope, e.g., are all the tickers addressed in the draft answer, any missing metrics (returns, vols etc)

                Return ONLY valid JSON with this exact shape:
                {{critic_result: {{
                                'status': 'ok'|'retry'
                                'reason': '<short>'
                                }}
                }}

                Query:
                "{query}"

                draft answer:
                {draft_answer}

    """
    if agent_state['mode'] == 'test':
        draft_response = response['critic']
    else:
        answer_response = client.models.generate_content(model='gemini-2.5-flash',
                                                         contents=prompt)
        draft_response = answer_response.text
    critic_result = gemini_json(draft_response)
    status = critic_result["critic_result"].get("status", "").lower()
    critic_result["critic_result"]["status"] = status
    logger.info(f'{critic_result}')
    final_answer = None
    if status == 'ok':
        final_answer = agent_state['draft_answer']
    return {**critic_result,
            'final_answer': final_answer}
