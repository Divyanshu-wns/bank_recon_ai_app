# agents/report_generator.py
from .base import BaseAgent
from io import BytesIO
import pandas as pd

class ReportGeneratorAgent(BaseAgent):
    def run(self, input_data, sop_context=None):
        self.log("Generating final Excel report.")

        try:
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                # Write reconciliation results
                if "recon_df" in input_data and not input_data["recon_df"].empty:
                    input_data["recon_df"].to_excel(writer, sheet_name="Reconciliation", index=False)
                    self.log("Added reconciliation results.")

                # Write EDW data
                if "edw_df" in input_data and not input_data["edw_df"].empty:
                    input_data["edw_df"].to_excel(writer, sheet_name="EDW", index=False)
                    self.log("Added EDW data.")

                # Write Journal data
                if "journal_df" in input_data and not input_data["journal_df"].empty:
                    input_data["journal_df"].to_excel(writer, sheet_name="Journal", index=False)
                    self.log("Added Journal data.")

                # Write resolution suggestions if available
                if "suggestions_df" in input_data and not input_data["suggestions_df"].empty:
                    input_data["suggestions_df"].to_excel(writer, sheet_name="Resolution Suggestions", index=False)
                    self.log("Added resolution suggestions.")

            buffer.seek(0)
            self.log("Excel file generated successfully.")
            return {"excel_file": buffer}

        except Exception as e:
            self.log(f"Error generating report: {e}")
            raise
