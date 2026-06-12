from acc.evals.harness import EvaluationHarness
from acc.filters.pipeline import FilterPipeline

if __name__ == "__main__":
    harness = EvaluationHarness("benchmarks")
    pipeline = FilterPipeline()
    
    print("=== ACC Quality Score Evaluation ===")
    
    categories = ["pytest", "git", "docker", "kubectl", "conversations", "repositories"]
    for cat in categories:
        res = harness.evaluate_filter(pipeline.execute, cat)
        print(f"\n--- Category: {cat} ---")
        for k, v in res.items():
            print(f"  {k}: {v}")
