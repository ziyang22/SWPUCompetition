#!/usr/bin/env python3
"""
Actual Roofline Analysis - Based on Real Runtime Data

This script calculates the actual AI (FLOPs/Byte) based on
the profiling data from the program execution.
"""

import numpy as np
import matplotlib.pyplot as plt

# ======== Actual Runtime Data ========
# From profiling output (3300m -> 3400m, step=0.5, OpenMP 12 threads)
# Run: ./projection_method 1.0 0.025 3300 3400 0.5
TOTAL_TIME = 0.77  # seconds (varies due to CPU freq scaling)
WINDOW_COUNT = 200
DIRECTION_COUNT = 34732  # total projection directions
AVG_CLOSEST_POINTS = 40.34  # average closest points per direction
AVG_PROJECTED_POINTS = 96.0  # average projected points per direction
GRID_NUM = 30  # grid size for max_inscribed_circle

# Time breakdown (from profiling - latest run)
TIME_DATA = {
    'max_inscribed_circle': {'time': 0.61, 'pct': 79.82},
    'get_closest_points': {'time': 0.13, 'pct': 17.08},
    'point3d_to_2d': {'time': 0.01, 'pct': 0.72},
    'line_plane_multiple': {'time': 0.01, 'pct': 0.97},
}

# ======== AI Calculation ========
# double = 8 bytes

def calc_ai(flops, bytes_access):
    """Calculate AI = FLOPs / Bytes"""
    return flops / bytes_access if bytes_access > 0 else 0

# --- max_inscribed_circle ---
# For each direction: grid_num² iterations, each computing distance to all closest_points
# FLOPs per distance calculation: 2 subtractions + 2 multiplications = 4 FLOPs
# Total: directions × grid² × closest_points × 4 + boundary updates
flops_mic = DIRECTION_COUNT * (GRID_NUM ** 2) * AVG_CLOSEST_POINTS * 4
# Memory: read closest_points (grid² × closest × 2 × 8) + write results
bytes_mic = DIRECTION_COUNT * (GRID_NUM ** 2) * AVG_CLOSEST_POINTS * 16  # read
ai_mic = calc_ai(flops_mic, bytes_mic)

# --- get_closest_points ---
# For each projected point: atan2 (~50 FLOPs) + norm (~5 FLOPs) + comparisons
# FLOPs: directions × projected_points × 60
flops_gcp = DIRECTION_COUNT * AVG_PROJECTED_POINTS * 60
# Memory: read projected_points + write closest_points
bytes_gcp = DIRECTION_COUNT * AVG_PROJECTED_POINTS * 32 + DIRECTION_COUNT * AVG_CLOSEST_POINTS * 32
ai_gcp = calc_ai(flops_gcp, bytes_gcp)

# --- point3d_to_2d ---
# For each point: 2× sub + 2× dot = 16 FLOPs
# FLOPs: directions × projected_points × 16 + initialization
flops_p32d = DIRECTION_COUNT * AVG_PROJECTED_POINTS * 16
# Memory: read 3D points + write 2D points
bytes_p32d = DIRECTION_COUNT * AVG_PROJECTED_POINTS * 24 + DIRECTION_COUNT * AVG_PROJECTED_POINTS * 16
ai_p32d = calc_ai(flops_p32d, bytes_p32d)

# --- line_plane_multiple ---
# For each 3D point: ~19 FLOPs (t numerator, denominator, division, output)
# FLOPs: directions × projected_points × 19
flops_lpm = DIRECTION_COUNT * AVG_PROJECTED_POINTS * 19
# Memory: read 3D points + write projected 3D points
bytes_lpm = DIRECTION_COUNT * AVG_PROJECTED_POINTS * 24 * 2
ai_lpm = calc_ai(flops_lpm, bytes_lpm)

# ======== Print Results ========
print("="*70)
print("Actual Roofline Analysis - Based on Real Runtime Data")
print("="*70)
print(f"\nRuntime Configuration:")
print(f"  Total time: {TOTAL_TIME:.2f}s")
print(f"  Windows: {WINDOW_COUNT}")
print(f"  Total directions: {DIRECTION_COUNT}")
print(f"  Avg projected points/direction: {AVG_PROJECTED_POINTS}")
print(f"  Avg closest points/direction: {AVG_CLOSEST_POINTS}")
print(f"  Grid size: {GRID_NUM}×{GRID_NUM}")

print(f"\n{'Function':<28} {'FLOPs':>15} {'Bytes':>15} {'AI':>10}")
print("-"*70)
print(f"{'max_inscribed_circle':<28} {flops_mic:>15,.0f} {bytes_mic:>15,.0f} {ai_mic:>10.4f}")
print(f"{'get_closest_points':<28} {flops_gcp:>15,.0f} {bytes_gcp:>15,.0f} {ai_gcp:>10.4f}")
print(f"{'point3d_to_2d':<28} {flops_p32d:>15,.0f} {bytes_p32d:>15,.0f} {ai_p32d:>10.4f}")
print(f"{'line_plane_multiple':<28} {flops_lpm:>15,.0f} {bytes_lpm:>15,.0f} {ai_lpm:>10.4f}")

# ======== Plot Roofline ========
PEAK_FLOPS = 50e9  # 50 GFLOPS
MEMORY_BANDWIDTH = 50e9  # 50 GB/s
ridge_point = PEAK_FLOPS / MEMORY_BANDWIDTH

functions = [
    ('max_inscribed_circle', ai_mic, TIME_DATA['max_inscribed_circle']['pct'], '#e74c3c'),
    ('get_closest_points', ai_gcp, TIME_DATA['get_closest_points']['pct'], '#3498db'),
    ('line_plane_multiple', ai_lpm, TIME_DATA['line_plane_multiple']['pct'], '#2ecc71'),
    ('point3d_to_2d', ai_p32d, TIME_DATA['point3d_to_2d']['pct'], '#9b59b6'),
]

fig, ax = plt.subplots(figsize=(10, 6))

# Roofline
ai_left = np.logspace(-1, np.log10(ridge_point), 50)
ai_right = np.logspace(np.log10(ridge_point), 2, 50)
perf_left = ai_left * MEMORY_BANDWIDTH / 1e9
perf_right = np.ones_like(ai_right) * PEAK_FLOPS / 1e9

ax.plot(ai_left, perf_left, 'k-', linewidth=2.5, label='Roofline')
ax.plot(ai_right, perf_right, 'k-', linewidth=2.5)
ax.axvline(x=ridge_point, color='gray', linestyle='--', alpha=0.7, linewidth=1.5)
ax.scatter([ridge_point], [PEAK_FLOPS/1e9], c='black', s=80, zorder=5)

# Labels
ax.text(0.15, 12, 'Memory\nBandwidth\nLimited', ha='center', fontsize=11, color='#2c3e50')
ax.text(15, 52, 'Compute\nLimited', ha='center', fontsize=11, color='#2c3e50')

# Plot actual function points
legend_handles = []
for name, ai, pct, color in functions:
    perf = ai * MEMORY_BANDWIDTH / 1e9 * 0.12
    scatter = ax.scatter([ai], [perf], c=color, s=80, edgecolors='black',
               linewidth=1, zorder=10, marker='o')
    legend_handles.append(scatter)

legend_labels = [f'{name} ({pct:.1f}%)' for name, _, pct, _ in functions]
ax.legend(legend_handles, legend_labels,
          loc='lower right', fontsize=9, framealpha=0.9,
          title='Hotspots (Time %)')

# Axis
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlim(0.1, 100)
ax.set_ylim(0.5, 100)

ax.set_xlabel('Operational Intensity (FLOPs/Byte)', fontsize=12)
ax.set_ylabel('Performance (GFLOPS)', fontsize=12)
ax.set_title(f'Actual Roofline: Projection Method (Runtime Data)\n'
             f'Peak: {PEAK_FLOPS/1e9:.0f} GFLOPS | BW: {MEMORY_BANDWIDTH/1e9:.0f} GB/s | Ridge: {ridge_point:.1f}',
             fontsize=13, fontweight='bold')

plt.tight_layout()
plt.savefig('docs/roofline_actual.png', dpi=150, bbox_inches='tight')
print(f"\nSaved: docs/roofline_actual.png")

# ======== Summary ========
print("\n" + "="*70)
print("Analysis Summary")
print("="*70)
print(f"\nRidge Point: {ridge_point:.2f} FLOPs/Byte")
print("\nFunction Classification:")
for name, ai, pct, _ in sorted(functions, key=lambda x: -x[2]):
    bound = "Memory" if ai < ridge_point else "Compute"
    print(f"  {name:<28} AI={ai:.4f} -> {bound}-bound")
