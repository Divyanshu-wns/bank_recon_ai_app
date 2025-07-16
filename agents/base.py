# agents/base.py
class BaseAgent:
    def __init__(self, name, api_key=None):
        self.name = name
        self.api_key = api_key
        self.logs = []

    def log(self, message):
        self.logs.append(f"[{self.name}] {message}")

    def run(self, input_data, sop_context=None):
        raise NotImplementedError("Each agent must implement a run() method")
