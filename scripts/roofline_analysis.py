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
functions = [
    ('max_inscribed_circle', 0.375, 78.76, '#e74c3c'),
    ('get_closest_points', 0.625, 18.05, '#3498db'),
    ('line_plane_multiple', 0.104, 1.00, '#2ecc71'),
    ('point3d_to_2d', 0.156, 0.74, '#9b59b6'),
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

# Mark ridge point
ax.scatter([ridge_point], [PEAK_FLOPS/1e9], c='black', s=100, zorder=5)
ax.axvline(x=ridge_point, color='gray', linestyle='--', alpha=0.5)

# Labels for regions
ax.text(0.15, 35, 'Memory\nBandwidth\nLimited', ha='center', fontsize=11, color='#2c3e50')
ax.text(10, 52, 'Compute\nLimited', ha='center', fontsize=11, color='#2c3e50')

# Plot function points
for name, ai, pct, color in functions:
    # Position based on AI, height based on time percentage (scaled)
    perf = ai * MEMORY_BANDWIDTH / 1e9 * 0.3  # Scaled for visibility

    ax.scatter([ai], [perf], c=color, s=150+pct*3, edgecolors='black',
               linewidth=1.5, zorder=10, marker='o')

    # Label
    y_offset = 3 if name != 'max_inscribed_circle' else -4
    ax.annotate(f'{name}\n({pct:.1f}%)',
                xy=(ai, perf), xytext=(ai*1.5, perf+y_offset),
                fontsize=9, ha='left',
                arrowprops=dict(arrowstyle='->', color=color, alpha=0.7))

# Axis settings
ax.set_xscale('log')
ax.set_xlim(0.1, 100)
ax.set_ylim(0, 55)

ax.set_xlabel('Operational Intensity (FLOPs/Byte)', fontsize=12)
ax.set_ylabel('Performance (GFLOPS)', fontsize=12)
ax.set_title(f'Roofline Model: Projection Method Hotspots\n'
             f'Peak: {PEAK_FLOPS/1e9:.0f} GFLOPS | BW: {MEMORY_BANDWIDTH/1e9:.0f} GB/s | Ridge: {ridge_point:.1f}',
             fontsize=13, fontweight='bold')

ax.grid(True, alpha=0.3, which='both')

plt.tight_layout()
plt.savefig('docs/roofline_plot.png', dpi=150, bbox_inches='tight')
print("Saved: docs/roofline_plot.png")

# ======== Console Summary ========
print("\n" + "="*55)
print("Roofline Analysis Summary")
print("="*55)
print(f"\nHardware: Peak={PEAK_FLOPS/1e9:.0f}GFLOPS, BW={MEMORY_BANDWIDTH/1e9:.0f}GB/s")
print(f"Ridge Point: {ridge_point:.1f} FLOP/Byte")
print("\nFunctions (sorted by time %):")
print("-"*55)
print(f"{'Function':<28} {'AI':>6} {'Time%':>8} {'Bound':>10}")
print("-"*55)
for name, ai, pct, _ in sorted(functions, key=lambda x: -x[2]):
    bound = "Memory" if ai < ridge_point else "Compute"
    print(f"{name:<28} {ai:>6.3f} {pct:>7.1f}% {bound:>10}")
print("-"*55)
print("\nConclusion: All hotspots are MEMORY-BANDWIDTH limited (AI < 1.0)")
print("Next optimization: Reduce memory access, increase data reuse")
