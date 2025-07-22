# agents/transaction_analyzer.py
from .base import BaseAgent
import pandas as pd
from openai import AzureOpenAI
from io import StringIO
import re

class TransactionAnalyzerAgent(BaseAgent):
    def run(self, input_data, sop_context=None):
        edw_df = input_data["edw_df"]
        journal_df = input_data["journal_df"]
        
        if sop_context and sop_context.strip():
            self.log("Using provided SOP for transaction analysis.")
            self.log(f"SOP length: {len(sop_context.split())} words")
        else:
            self.log("No SOP provided, using default reconciliation rules.")
        
        self.log("Preparing data for GPT prompt.")
        edw_csv = edw_df.to_csv(index=False)
        journal_csv = journal_df.to_csv(index=False)

        prompt = f"""
You are a highly precise finance assistant. Your job is to match Journal and EDW transactions for reconciliation.

**Instructions:**
- Use the SOP below for your logic.
- Output ONLY a CSV table with EXACTLY these columns, in this order, and NO extra columns or text:
No,Item Type,Reconciliation,SIDE,Value Date,Ref 1,Amount,Amt CCY,Bus Entity,Stmt Date,Rule,ENTRY DATE,Ref 2,Ref 3,Ref 4,Tran Code,Status
- If a field contains a comma, wrap it in double quotes.
- Do NOT add any explanations, markdown, code blocks, summary lines, or extra headers.
- Every row must have exactly 17 columns, matching the header above.

**Status column values:**
- Use ONLY: MATCHED, UNMATCHED, or PARTIAL.

**SOP:**
{sop_context or 'No SOP provided. Use standard reconciliation rules: 1. Match transactions based on Account Number, Transaction Code, and Date. 2. Compare amounts ensuring Debit matches sum of absolute EDW amounts. 3. Flag partial matches when amounts do not fully reconcile.'}

**EDW:**
{edw_csv}

**Journal:**
{journal_csv}

Remember: Output ONLY the CSV data, with the exact columns and order specified above. No extra text, explanations, or formatting.
"""

        try:
            # Use AzureOpenAI client
            client = AzureOpenAI(
                api_key=self.llm_config.get("api_key"),
                api_version=self.llm_config.get("api_version"),
                azure_endpoint=self.llm_config.get("azure_endpoint")
            )
            response = client.chat.completions.create(
                model=self.llm_config.get("model_name"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            content = response.choices[0].message.content
            gpt_output = content.strip() if content else ""
            self.log("Received response from GPT.")

            # Clean up the output
            # Remove any markdown code block syntax
            gpt_output = re.sub(r'```\w*\n?', '', gpt_output)
            gpt_output = gpt_output.strip()

            # Ensure we have the header
            expected_header = "No,Item Type,Reconciliation,SIDE,Value Date,Ref 1,Amount,Amt CCY,Bus Entity,Stmt Date,Rule,ENTRY DATE,Ref 2,Ref 3,Ref 4,Tran Code,Status"
            if not gpt_output.startswith(expected_header):
                gpt_output = expected_header + "\n" + gpt_output

            lines = gpt_output.split('\n')
            cleaned_lines = []
            num_columns = len(expected_header.split(','))
            
            for line in lines:
                if line.strip():  # Skip empty lines
                    fields = line.split(',')
                    if len(fields) > num_columns:
                        # If we have too many columns, combine excess columns
                        fields = fields[:num_columns-1] + [','.join(fields[num_columns-1:])]
                    elif len(fields) < num_columns:
                        # If we have too few columns, pad with empty strings
                        fields.extend([''] * (num_columns - len(fields)))
                    cleaned_lines.append(','.join(fields))
            
            cleaned_csv = '\n'.join(cleaned_lines)
            recon_df = pd.read_csv(StringIO(cleaned_csv))
            # Ensure Status column is string and standardized
            recon_df['Status'] = recon_df['Status'].fillna('UNMATCHED').astype(str).str.upper()

            self.log("Successfully parsed GPT response to DataFrame.")

        except Exception as e:
            self.log(f"Error in transaction analysis: {e}")
            raise

        return {"recon_df": recon_df}
