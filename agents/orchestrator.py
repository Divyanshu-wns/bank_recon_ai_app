# agents/orchestrator.py
from .raw_data_collector import RawDataCollectorAgent
from .transaction_analyzer import TransactionAnalyzerAgent
from .discrepancy_resolution import DiscrepancyResolutionAgent
from .report_generator import ReportGeneratorAgent

class AgentOrchestrator:
    def __init__(self, api_key):
        self.api_key = api_key
        self.logs = []

    def run_all(self, uploaded_file, sop_text):
        try:
            # Step 1: Collect raw data
            raw_agent = RawDataCollectorAgent(name="RawDataCollector", api_key=self.api_key)
            step1 = raw_agent.run(uploaded_file)
            self.logs.extend(raw_agent.logs)

            # Store original data
            edw_df = step1["edw_df"]
            journal_df = step1["journal_df"]

            # Step 2: Analyze transactions
            tx_agent = TransactionAnalyzerAgent(name="TransactionAnalyzer", api_key=self.api_key)
            step2 = tx_agent.run(step1, sop_context=sop_text)
            self.logs.extend(tx_agent.logs)

            # Step 3: Resolve discrepancies
            disc_agent = DiscrepancyResolutionAgent(name="DiscrepancyResolver", api_key=self.api_key)
            step3 = disc_agent.run(step2, sop_context=sop_text)
            self.logs.extend(disc_agent.logs)

            # Step 4: Generate report (include original data)
            report_agent = ReportGeneratorAgent(name="ReportGenerator", api_key=self.api_key)
            final_data = {
                "recon_df": step3["recon_df"],
                "suggestions_df": step3.get("suggestions_df", None),
                "edw_df": edw_df,
                "journal_df": journal_df
            }
            step4 = report_agent.run(final_data)
            self.logs.extend(report_agent.logs)

            return step4["excel_file"], self.logs

        except Exception as e:
            self.logs.append(f"[Orchestrator] ❌ Error: {e}")
            raise
