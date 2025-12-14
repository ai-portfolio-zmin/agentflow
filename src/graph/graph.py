from langgraph.graph import StateGraph, END
from src.graph.state import AgentState
from src.graph.nodes import planner, executor, router, answer, critic


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node('planner', planner)
    graph.add_node('executor', executor)
    graph.add_node('router', router)
    graph.add_node('answer', answer)
    graph.add_node('critic', critic)

    graph.set_entry_point('router')
    graph.add_edge('planner', 'router')
    graph.add_edge('executor', 'router')
    graph.add_edge('answer', 'critic')
    graph.add_edge('critic', 'router')

    graph.add_conditional_edges('router',
                                lambda agent_stage: agent_stage['next_node'],
                                {'planner': 'planner',
                                 'executor': 'executor',
                                 'answer': 'answer',
                                 'END': END})
    return graph


if __name__ == '__main__':
    graph = build_graph()
    graph_app = graph.compile()
    query = 'load the data of AAPL and MSFT for 2 years, plot the price chat and then comparare the performance and risk of AAPL and MSFT for past 1 year'
    query = 'plot the price chat for AAPL and MSFT and then comparare the performance and risk for past 1 year'
    initial_state = AgentState(query=query, mode = 'test',run_id='test_0003')
    result = graph_app.invoke(initial_state)
