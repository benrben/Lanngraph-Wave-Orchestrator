from langgraph_wave_orchestrator import WaveOrchestrator
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

def main():
    wave_orchestrator = WaveOrchestrator(llm=ChatOpenAI(model="gpt-4o-mini", temperature=0.0))

    print("Hello from waveorchestrator!")


if __name__ == "__main__":
    main()
