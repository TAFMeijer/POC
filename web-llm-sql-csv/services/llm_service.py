import google.generativeai as genai
import os

def translate_to_pseudo_sql(query):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro-latest')
    
    system_prompt = """
You are an assistant that writes ONLY T-SQL SELECT queries for SQL Server.

Logical schema (you MUST use exactly these names):

Table: GC7Budget
Columns:
  country
  implementation_period_name
  intervention
  total_amount

Rules:
- Use ONLY the table and columns listed above.
- Do NOT invent other table or column names.
- Do NOT use square brackets or quotes for identifiers.
- Do NOT include schema prefixes like dbo.
- Return ONLY a single SELECT query, nothing else.
- If the question cannot be answered from this schema, return exactly: CANNOT_ANSWER
"""
    
    full_prompt = f"{system_prompt}\n\nUser Question: {query}\nSQL Query:"
    
    response = model.generate_content(full_prompt)
    text = response.text.strip()
    
    # Clean up common LLM artifacts
    if text.startswith("```"):
        text = text.replace("```sql", "").replace("```", "")
    
    if text.lower().startswith("sql:"):
        text = text[4:]
        
    return text.strip()
