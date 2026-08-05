import json
import csv
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))
from backend.app.services.llm_factory import LLMFactory
from langchain_core.prompts import ChatPromptTemplate

categories = [
    "Groceries", "Dining", "Transportation", "Utilities", 
    "Shopping", "Entertainment", "Income", "Transfer", 
    "Healthcare", "Subscriptions", "Uncategorized"
]

def generate():
    llm = LLMFactory.get_llm(temperature=0.7)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a synthetic data generator for a personal finance app. Generate exactly 50 realistic bank transaction descriptions that a user might see on a credit card or bank statement. Distribute them randomly but evenly across these exact categories: " + ", ".join(categories) + ".\nReturn ONLY a valid JSON array of objects. Each object must have two keys: 'description' (the raw bank statement text) and 'category' (the exact category from the list). Do not use markdown blocks."),
        ("user", "Generate the data.")
    ])
    
    chain = prompt | llm
    all_data = []
    
    print("Generating synthetic data in batches...")
    for i in range(4): # 200 total
        try:
            res = chain.invoke({})
            content = str(res.content).strip()
            if content.startswith("```json"): content = content[7:]
            if content.startswith("```"): content = content[3:]
            if content.endswith("```"): content = content[:-3]
            batch = json.loads(content.strip())
            all_data.extend(batch)
            print(f"Batch {i+1} complete. Total: {len(all_data)}")
        except Exception as e:
            print(f"Error in batch {i+1}: {e}")
            
    with open('data/training.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['description', 'category'])
        writer.writeheader()
        writer.writerows(all_data)
        
    print(f"Generated {len(all_data)} rows in data/training.csv")

if __name__ == "__main__":
    generate()
