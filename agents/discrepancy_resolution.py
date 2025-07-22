# agents/discrepancy_resolution.py
from .base import BaseAgent
from openai import AzureOpenAI
import pandas as pd
from io import StringIO
import re

class DiscrepancyResolutionAgent(BaseAgent):
    def run(self, input_data, sop_context=None):
        recon_df = input_data["recon_df"]
        self.log("Filtering unmatched rows.")

        if sop_context and sop_context.strip():
            self.log("Using provided SOP for discrepancy resolution.")
            self.log(f"SOP length: {len(sop_context.split())} words")
        else:
            self.log("No SOP provided, using default resolution guidelines.")

        # Convert Status column to string and handle missing values
        recon_df['Status'] = recon_df['Status'].fillna('').astype(str)
        unmatched_df = recon_df[recon_df['Status'].str.upper() != 'MATCHED']
        
        if unmatched_df.empty:
            self.log("No unmatched transactions found.")
            return {"recon_df": recon_df}

        csv_data = unmatched_df.to_csv(index=False)
        prompt = f"""
You are a bank reconciliation expert. Your job is to analyze unmatched transactions and suggest resolutions.

**Instructions:**
- Output ONLY a CSV table with EXACTLY these columns, in this order, and NO extra columns or text:
Ref 1,Issue,Suggested Resolution
- If a field contains a comma, wrap it in double quotes.
- Do NOT add any explanations, markdown, code blocks, summary lines, or extra headers.
- Every row must have exactly 3 columns, matching the header above.

**SOP:**
{sop_context or 'No SOP provided. Use general resolution guidelines: 1. Check for date mismatches within a 3-day window. 2. Look for amount splits or combined entries. 3. Verify similar transaction codes. 4. Investigate currency conversion differences. 5. Check for reversed or correction entries.'}

**Unmatched Transactions:**
{csv_data}

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
            self.log("Received resolution suggestions from GPT.")

            # Clean up the output
            # Remove any markdown code block syntax
            gpt_output = re.sub(r'```\w*\n?', '', gpt_output)
            gpt_output = gpt_output.strip()

            # Ensure we have the header
            expected_header = "Ref 1,Issue,Suggested Resolution"
            if not gpt_output.startswith(expected_header):
                gpt_output = expected_header + "\n" + gpt_output

            try:
                # Try parsing with pandas
                suggestions_df = pd.read_csv(StringIO(gpt_output))
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
                suggestions_df = pd.read_csv(StringIO(cleaned_csv))

            self.log("Successfully parsed suggestions.")
            return {
                "recon_df": recon_df,
                "suggestions_df": suggestions_df
            }

        except Exception as e:
            self.log(f"Error resolving discrepancies: {e}")
            raise