from langgraph_wave_orchestrator import WaveOrchestrator
from langgraph_wave_orchestrator.models import WorkerNode
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage
from typing import List, Dict, Annotated
from langgraph.graph.message import add_messages

load_dotenv()

class State(BaseModel):
    messages: Annotated[List[BaseMessage], add_messages] = Field(default_factory=list)
    search_results: Annotated[List[BaseMessage], add_messages] = Field(default_factory=list)
    user_query: str = Field(default="")
    user_state: Dict[str, str] = Field(default_factory=dict)

def research_worker(state) -> Dict:
    """A simple research worker that processes queries."""
    messages = getattr(state, "research_result", [])
    if messages:
        last_message = messages[-1]
        content = f"Research completed for: {last_message.content}"
        return {"research_result": [HumanMessage(content=content)]}
    return {"research_result": [HumanMessage(content="No research task provided")]}

def verification_worker(state) -> Dict:
    """A simple verification worker that validates information."""
    messages = getattr(state, "verification_result", [])
    if messages:
        last_message = messages[-1]
        content = f"Verification completed for: {last_message.content}"
        return {"verification_result": [HumanMessage(content=content)]}
    return {"verification_result": [HumanMessage(content="No verification task provided")]}

def compilation_worker(state) -> Dict:
    """A simple compilation worker that creates final reports."""
    messages = getattr(state, "compilation_result", [])
    if messages:
        last_message = messages[-1]
        content = f"Compilation completed for: {last_message.content}"
        return {"compilation_result": [HumanMessage(content=content)]}
    return {"compilation_result": [HumanMessage(content="No compilation task provided")]}

wave_orchestrator = WaveOrchestrator(llm=ChatOpenAI(model="gpt-4o-mini", temperature=0.0), user_state_params=State)
    
wave_orchestrator.add_node(WorkerNode(
        function=research_worker,
        state_placeholder="research_result",
        description="Conducts research on given topics",
        name="researcher"
    ))
    
wave_orchestrator.add_node(WorkerNode(
        function=verification_worker,
        state_placeholder="verification_result",
        description="Verifies information and facts",
        name="verifier"
    ))
    
wave_orchestrator.add_node(WorkerNode(
        function=compilation_worker,
        state_placeholder="compilation_result",
        description="Compiles information into final reports",
        name="compiler"
    ))
    
graph = wave_orchestrator.compile()
    