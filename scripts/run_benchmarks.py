import os
import sys
import time
from sidon_benchmark import find_maximal_sidon, verify_sidon

# Define N values to test
Ns = [50, 100, 284, 586, 1000, 5000, 10000, 25000, 50000, 75000, 100000]

print("Starting Mass Benchmark SIDON Generator...")
print("Results will be saved in 'datasets/' directory.")

out_dir = "datasets"
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

results = []

for N in Ns:
    print(f"\n--- Testing N = {N} ---")
    
    # Hide stdout from find_maximal_sidon to avoid clutter
    import io
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    t0 = time.time()
    best_set, meta = find_maximal_sidon(N)
    t1 = time.time()
    
    # Restore stdout
    sys.stdout = old_stdout
    
    exec_time = t1 - t0
    K = len(best_set)
    density = K / (N**0.5)
    
    is_valid = verify_sidon(best_set)
    
    print(f"[*] Completed in {exec_time:.3f} seconds.")
    print(f"[*] Found K = {K} (Density: {density:.3f}) | Sidon Valid: {is_valid}")
    
    # Save to file
    filename = os.path.join(out_dir, f"sidon_N{N}_K{K}.txt")
    with open(filename, "w") as f:
        f.write(f"# Maximal Sidon Set per N={N}\n")
        f.write(f"# Cardinality (K): {K}\n")
        f.write(f"# Base Geometry: Singer q={meta.get('q', '?')} (v={meta.get('v', '?')})\n")
        f.write(f"# Hall Multiplier: k={meta.get('multiplier', '?')}\n")
        f.write(f"# Density: {density:.3f} * sqrt(N)\n")
        f.write(f"# Execution Time: {exec_time:.3f} seconds\n\n")
        
        formatted = [best_set[i:i+10] for i in range(0, len(best_set), 10)]
        for row in formatted:
            f.write("  " + ", ".join(f"{x:6d}" for x in row) + "\n")
            
    print(f"[*] Saved to {filename}")
    
    results.append({
        'N': N,
        'K': K,
        'Time': exec_time,
        'Density': density
    })

print("\n--- BENCHMARK SUMMARY ---")
print("| N | K | Density | Real Execution Time |")
print("|---|---|---|---|")
for r in results:
    print(f"| {r['N']} | {r['K']} | {r['Density']:.3f} | {r['Time']:.3f} s |")
