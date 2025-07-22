# agents/base.py
class BaseAgent:
    def __init__(self, name, llm_config=None):
        self.name = name
        self.llm_config = llm_config or {}
        self.logs = []

    def log(self, message):
        self.logs.append(f"[{self.name}] {message}")

    def run(self, input_data, sop_context=None):
        raise NotImplementedError("Each agent must implement a run() method")
