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
You are a finance assistant. Use the following SOP when analyzing:
### SOP:
{sop_context or '''No SOP provided. Use standard reconciliation rules:
1. Match transactions based on Account Number, Transaction Code, and Date
2. Compare amounts ensuring Debit matches sum of absolute EDW amounts
3. Flag partial matches when amounts don't fully reconcile'''}

Now, match Journal and EDW transactions using:
- Account Number, Tran Code, and Date match
- Debit = Sum of absolute EDW amounts

Output ONLY a CSV table with these exact columns (no other text):
No,Item Type,Reconciliation,SIDE,Value Date,Ref 1,Amount,Amt CCY,Bus Entity,Stmt Date,Rule,ENTRY DATE,Ref 2,Ref 3,Ref 4,Tran Code,Status

For the Status column, use ONLY these values:
- "MATCHED" for reconciled transactions
- "UNMATCHED" for transactions that don't match
- "PARTIAL" for partially matched transactions

### EDW:
{edw_csv}

### Journal:
{journal_csv}

Remember: Output ONLY the CSV data with the exact columns specified, no additional text or explanations.
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

            try:
                # Try parsing with pandas
                recon_df = pd.read_csv(StringIO(gpt_output))
                # Ensure Status column is string and standardized
                recon_df['Status'] = recon_df['Status'].fillna('UNMATCHED').astype(str).str.upper()
            except Exception as e:
                self.log(f"Error parsing CSV: {e}")
                # If parsing fails, try to fix common issues
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
