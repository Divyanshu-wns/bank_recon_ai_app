# agents/raw_data_collector.py
import pandas as pd
from .base import BaseAgent

class RawDataCollectorAgent(BaseAgent):
    def run(self, uploaded_file, sop_context=None):
        self.log("Reading Excel sheets: EDW and Journal")

        try:
            edw_df = pd.read_excel(uploaded_file, sheet_name="EDW")
            journal_df = pd.read_excel(uploaded_file, sheet_name="Journal")
            self.log("Successfully read both sheets.")
        except Exception as e:
            self.log(f"Error reading Excel file: {e}")
            raise

        return {"edw_df": edw_df, "journal_df": journal_df}
