#!/usr/bin/env python3
"""
Roofline Model - Main Hotspots Analysis
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ======== Hardware Parameters ========
PEAK_FLOPS = 50e9      # 50 GFLOPS (AVX2 @ 4.0GHz)
MEMORY_BANDWIDTH = 50e9  # 50 GB/s (DDR4-3200)

# ======== Function Data ========
# AI = FLOPs / Bytes (理论计算值)
# max_inscribed_circle: 134,100 FLOPs / 525,600 bytes ≈ 0.255
# get_closest_points: 5,760 FLOPs / 5,376 bytes ≈ 1.07
# line_plane_multiple: 912 FLOPs / 2,304 bytes ≈ 0.396
# point3d_to_2d: 795 FLOPs / 1,920 bytes ≈ 0.414
functions = [
    ('max_inscribed_circle', 0.255, 78.76, '#e74c3c'),
    ('get_closest_points', 1.07, 18.05, '#3498db'),
    ('line_plane_multiple', 0.396, 1.00, '#2ecc71'),
    ('point3d_to_2d', 0.414, 0.74, '#9b59b6'),
]

# Ridge point
ridge_point = PEAK_FLOPS / MEMORY_BANDWIDTH  # = 1.0 FLOP/Byte

# ======== Plot ========
fig, ax = plt.subplots(figsize=(10, 6))

# X-axis: Operational Intensity (log scale)
ai_range = np.logspace(-1, 2, 100)

# Roofline: diagonal line (memory bound) + horizontal line (compute bound)
# Left of ridge point: performance = AI * memory_bandwidth
# Right of ridge point: performance = peak_flops
ai_left = np.logspace(-1, np.log10(ridge_point), 50)
ai_right = np.logspace(np.log10(ridge_point), 2, 50)

perf_left = ai_left * MEMORY_BANDWIDTH / 1e9   # GFLOPS
perf_right = np.ones_like(ai_right) * PEAK_FLOPS / 1e9

# Draw Roofline (two straight lines meeting at ridge point)
ax.plot(ai_left, perf_left, 'k-', linewidth=2.5, label='Roofline')
ax.plot(ai_right, perf_right, 'k-', linewidth=2.5)

# Mark ridge point - only vertical dashed line, no horizontal
ax.axvline(x=ridge_point, color='gray', linestyle='--', alpha=0.7, linewidth=1.5)
ax.scatter([ridge_point], [PEAK_FLOPS/1e9], c='black', s=80, zorder=5)

# Labels for regions
ax.text(0.15, 12, 'Memory\nBandwidth\nLimited', ha='center', fontsize=11, color='#2c3e50')
ax.text(15, 52, 'Compute\nLimited', ha='center', fontsize=11, color='#2c3e50')

# Plot function points (smaller, without labels)
legend_handles = []
for name, ai, pct, color in functions:
    # Position based on AI, height scaled for visibility in log-log space
    # Place them below the roofline to show they are memory-bound
    # Scale factor adjusted to keep all points visible in log scale (y >= 1)
    perf = ai * MEMORY_BANDWIDTH / 1e9 * 0.25  # Adjusted for visibility

    scatter = ax.scatter([ai], [perf], c=color, s=80, edgecolors='black',
               linewidth=1, zorder=10, marker='o')
    legend_handles.append(scatter)

# Create legend in lower right corner
legend_labels = [f'{name} ({pct:.1f}%)' for name, _, pct, _ in functions]
ax.legend(legend_handles, legend_labels,
          loc='lower right', fontsize=9, framealpha=0.9,
          title='Hotspots (Time %)', title_fontsize=10)

# Axis settings - use log-log for straight diagonal lines
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlim(0.1, 100)
ax.set_ylim(0.5, 100)  # Lower limit to show all points

ax.set_xlabel('Operational Intensity (FLOPs/Byte)', fontsize=12)
ax.set_ylabel('Performance (GFLOPS)', fontsize=12)
ax.set_title(f'Roofline Model: Projection Method Hotspots\n'
             f'Peak: {PEAK_FLOPS/1e9:.0f} GFLOPS | BW: {MEMORY_BANDWIDTH/1e9:.0f} GB/s | Ridge: {ridge_point:.1f}',
             fontsize=13, fontweight='bold')

# Remove background grid, only keep ridge vertical dashed line
ax.grid(False)

plt.tight_layout()
plt.savefig('docs/roofline_plot.png', dpi=150, bbox_inches='tight')
print("Saved: docs/roofline_plot.png")

# ======== Console Summary ========
print("\n" + "="*55)
print("Roofline Analysis Summary (Theoretical Values)")
print("="*55)
print(f"\nHardware: Peak={PEAK_FLOPS/1e9:.0f}GFLOPS, BW={MEMORY_BANDWIDTH/1e9:.0f}GB/s")
print(f"Ridge Point: {ridge_point:.2f} FLOP/Byte")
print("\nFunctions (sorted by time %):")
print("-"*55)
print(f"{'Function':<28} {'AI':>6} {'Time%':>8} {'Bound':>10}")
print("-"*55)
for name, ai, pct, _ in sorted(functions, key=lambda x: -x[2]):
    bound = "Memory" if ai < ridge_point else "Compute"
    print(f"{name:<28} {ai:>6.3f} {pct:>7.1f}% {bound:>10}")
print("-"*55)
