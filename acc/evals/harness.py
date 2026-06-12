import os
import json
import time
import tiktoken

def count_tokens(text: str, model="gpt-4o") -> int:
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
        # Fallback approximation if tiktoken fails
        return len(text) // 4

class EvaluationHarness:
    def __init__(self, benchmarks_dir="benchmarks"):
        self.benchmarks_dir = benchmarks_dir

    def evaluate_filter(self, filter_func, category: str):
        """
        Evaluates a deterministic or LLM filter against the ground truth datasets for a category.
        Returns the average ACC Quality Score and metrics across all samples in the category.
        """
        cat_dir = os.path.join(self.benchmarks_dir, category)
        if not os.path.exists(cat_dir):
            raise ValueError(f"Category {category} not found in {self.benchmarks_dir}")
            
        samples = [d for d in os.listdir(cat_dir) if os.path.isdir(os.path.join(cat_dir, d))]
        
        total_input_tokens = 0
        total_output_tokens = 0
        total_latency = 0
        total_signal_preserved = 0
        total_signal_count = 0
        
        for sample in samples:
            sample_dir = os.path.join(cat_dir, sample)
            with open(os.path.join(sample_dir, "raw_input.txt"), "r") as f:
                raw_input = f.read()
                
            with open(os.path.join(sample_dir, "expected_signal.json"), "r") as f:
                expected_signal = json.load(f)
                
            # Measure latency
            start_time = time.time()
            compressed_output = filter_func(raw_input)
            latency = time.time() - start_time
            
            # Count tokens
            input_tokens = count_tokens(raw_input)
            output_tokens = count_tokens(compressed_output)
            
            total_input_tokens += input_tokens
            total_output_tokens += output_tokens
            total_latency += latency
            
            # Measure signal preservation
            signal_count = 0
            preserved_count = 0
            for key, signals in expected_signal.items():
                for sig in signals:
                    signal_count += 1
                    # A naive check: does the string exist in the compressed output?
                    # For semantic compression, this would use an LLM grader.
                    if sig in compressed_output:
                        preserved_count += 1
                        
            total_signal_count += signal_count
            total_signal_preserved += preserved_count
            
        # Calculate averages
        avg_compression_ratio = 1.0 - (total_output_tokens / max(total_input_tokens, 1))
        avg_signal_preservation = (total_signal_preserved / max(total_signal_count, 1))
        avg_latency = total_latency / len(samples)
        
        # Mock Task Success (in a real scenario, this involves running the agent end-to-end)
        # For now, we assume task success correlates highly with signal preservation.
        task_success = avg_signal_preservation 
        
        # ACC Score = 0.50 * Task Success + 0.25 * Signal Preservation + 0.15 * Compression Ratio + 0.10 * Latency Score
        # Latency Score: 1.0 if < 100ms, scaling down.
        latency_score = max(0.0, 1.0 - (avg_latency / 2.0))
        
        acc_score = (
            0.50 * task_success +
            0.25 * avg_signal_preservation +
            0.15 * avg_compression_ratio +
            0.10 * latency_score
        )
        
        return {
            "acc_score": round(acc_score, 4),
            "compression_ratio": round(avg_compression_ratio, 4),
            "signal_preservation": round(avg_signal_preservation, 4),
            "task_success": round(task_success, 4),
            "latency_sec": round(avg_latency, 4),
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens
        }
