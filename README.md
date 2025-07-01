# LangGraph Wave Orchestrator

A parallel task execution framework built on LangGraph that distributes AI-powered tasks across multiple worker nodes in organized execution waves. Efficiently coordinates complex, multi-step AI workflows while maximizing parallelization and maintaining proper task dependencies.

## Features

- **Parallel Wave Execution**: Organizes tasks into execution waves for optimal parallel processing
- **Dynamic State Management**: Creates flexible worker state handling using Pydantic models
- **Worker Node Management**: Manages worker node lifecycle and task distribution
- **Intelligent Task Planning**: LLM-powered task decomposition and worker assignment

## Installation

### Install from PyPI

```bash
pip install Lanngraph-Wave-Orchestrator
```

### Install from TestPyPI (for testing)

```bash
pip install -i https://test.pypi.org/simple/ Lanngraph-Wave-Orchestrator
```

### Install from Source

```bash
git clone https://github.com/benrben/Lanngraph-Wave-Orchestrator.git
cd Lanngraph-Wave-Orchestrator
pip install -e .
```

### Dependencies

The package automatically installs these dependencies:
- `pydantic>=2.0.0` - For data validation and settings management
- `langchain-core>=0.1.0` - Core LangChain functionality
- `langgraph>=0.1.0` - Graph-based LLM application framework
- `python-dotenv>=1.0.0` - Environment variable management

### Optional Dependencies

For OpenAI integration (recommended):
```bash
pip install langchain-openai
```

## Usage

```python
from langgraph_wave_orchestrator import WaveOrchestrator, WorkerNode
from langchain_openai import ChatOpenAI

# Create LLM and orchestrator
llm = ChatOpenAI(model="gpt-4")
wave_orchestrator = WaveOrchestrator(llm)

# Add worker nodes
wave_orchestrator.add_node(search_node)
wave_orchestrator.add_node(financial_node)

# Compile and use
graph = wave_orchestrator.compile()
result = graph.invoke({"messages": [{"content": "Your query here"}]})
```

## Creating Worker Nodes

### 1. Define State Model
```python
from pydantic import BaseModel
from typing import List, Annotated
from langchain_core.messages import BaseMessage, add_messages

class SearchModel(BaseModel):
    messages: Annotated[List[BaseMessage], add_messages] = []
```

### 2. Create Worker Function
```python
from langchain_core.messages import AIMessage

def search_worker(state):
    # Access the task from state
    task = state.search_state.messages[-1].content
    
    # Process the task (your custom logic here)
    result = f"Search results for: {task}"
    
    # Return updated state
    return {"search_state": {"messages": [AIMessage(content=result)]}}
```

### 3. Build and Add Node
```python
search_node = WorkerNode(
    function=search_worker,
    model=SearchModel, 
    state_placeholder="search_state",
    description="search the web for information and current data",
    name="search"
)

wave_orchestrator.add_node(search_node)
```

## Development

### Setup
```bash
uv sync
pytest tests/
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

Follow PEP 8 style guidelines and include type hints.

## License

MIT License - see LICENSE file for details.
