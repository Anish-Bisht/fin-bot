import os
import json
import asyncio
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from app.agent import run_agent
from app.db import search_documents

# Mock Ground Truths for a subset of queries
GROUND_TRUTH_MAP = {
    "What is the Q1 revenue?": "The Q1 revenue for 2024 is documented in the quarterly financial report.",
    "How to handle a database outage?": "Database outages follow the engineering incident runbook in the master doc.",
    "What are our brand colors?": "Our brand colors include indigo and emerald as primary gradients.",
    "How many leaves do I get?": "Employees are entitled to 25 days of annual leave according to the handbook.",
    "What is the CEO's strategy?": "The CEO's strategy focuses on AI-driven financial services expansion."
}

def generate_test_dataset():
    """Generate a representative evaluation dataset by querying the agent."""
    print("🚀 Generating test dataset for RAGAs evaluation...")
    
    sample_questions = [
        ("What is the Q1 revenue?", "finance", "Finance"),
        ("How to handle a database outage?", "engineering", "Engineering"),
        ("What are our brand colors?", "marketing", "Marketing"),
        ("How many leaves do I get?", "employee", "Employee"),
        ("What is the CEO's strategy?", "c_level", "Executive"),
    ]
    
    data = {"question": [], "ground_truth": [], "answer": [], "contexts": []}
    
    for q, role, display_role in sample_questions:
        try:
            print(f"  🧐 Evaluating query: '{q}' as {display_role}")
            # Query the live agent
            response_obj = run_agent(q, "eval_thread_" + role, user_role=role)
            
            # Fetch retrieval context for metrics
            chunks, _ = search_documents(q, role, top_k=3)
            context_texts = [c["text"] for c in chunks]
            
            data["question"].append(q)
            data["answer"].append(response_obj["result"])
            data["contexts"].append(context_texts)
            data["ground_truth"].append(GROUND_TRUTH_MAP.get(q, "Ground truth not defined."))
            
        except Exception as e:
            print(f"  ❌ Failed eval for {q}: {e}")
            
    return Dataset.from_dict(data)

def run_evaluation():
    """Run RAGAs evaluation and output a summary report."""
    dataset = generate_test_dataset()
    if len(dataset) == 0:
        print("Empty dataset. Skipping evaluation.")
        return
        
    print("📊 Calculating RAGAs metrics (this may take a minute)...")
    try:
        # Note: RAGAs 0.1+ requires a dataset for evaluate
        result = evaluate(
            dataset,
            metrics=[
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall,
            ]
        )
        
        print("\n" + "="*40)
        print("🏆 RAGAs Evaluation Report")
        print("="*40)
        print(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("-"*40)
        for metric, score in result.items():
            print(f"{metric.capitalize():<20} : {score:.4f}")
        print("="*40)
        
        # Save results to a file for persistence
        output_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "eval_results.json")
        with open(output_file, "w") as f:
            # result is a Result object, convert to dict
            json.dump(dict(result), f, indent=2)
        print(f"Results saved to {output_file}")

    except Exception as e:
        print(f"Evaluation failed: {e}")

if __name__ == "__main__":
    import time
    run_evaluation()
