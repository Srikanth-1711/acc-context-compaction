from acc.evals.harness import EvaluationHarness
from acc.filters.pipeline import FilterPipeline
from acc.filters.profile_manager import ProfileManager

if __name__ == "__main__":
    harness = EvaluationHarness("benchmarks")
    pm = ProfileManager()
    
    print("=== ACC Quality Score Evaluation (Phase 3 Profiles) ===")
    
    categories = ["pytest", "git", "docker", "kubectl", "conversations", "repositories"]
    for cat in categories:
        profile = pm.load_profile(cat)
        pipeline = FilterPipeline(profile)
        
        res = harness.evaluate_filter(pipeline.execute, cat)
        print(f"\n--- Category: {cat} (Profile: {'Loaded' if profile else 'None'}) ---")
        for k, v in res.items():
            print(f"  {k}: {v}")
