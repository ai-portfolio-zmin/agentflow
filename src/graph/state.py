from typing import TypedDict, Annotated
from deepmerge import always_merger


# def merge_dicts(old: dict | None, new: dict) -> dict:
#     if old is None:
#         return new.copy()
#     merged = old.copy()
#     merged.update(new)
#     return merged

def add_message(msg1, msg2):
    return msg1 + msg2


class AgentState(TypedDict):
    query: str

    plans: list
    next_plan_index: int

    next_node: str

    call_stack: Annotated[list, add_message]
    nsteps: int

    execution_status: Annotated[list, add_message]
    data: Annotated[dict, always_merger.merge]
    execution_result: Annotated[dict, always_merger.merge]

    draft_answer: str
    final_answer: str
    critic_result: dict

    mode: str
    run_id: str
