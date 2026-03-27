#!/usr/bin/env python3
"""
Automated Benchmarking Script (Fast Mode) - skips Python baseline, uses cached results
"""

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class SystemInfo:
    cpu_model: str
    physical_cores: int
    logical_threads: int

@dataclass
class TestCase:
    dataset: str
    name: str
    instrument_length: float
    instrument_radius: float
    begin_deep: float
    end_deep: float
    num_step: float

@dataclass
class Configuration:
    name: str
    use_openmp: bool
    use_simd: bool
    adaptive_search: bool
    make_args: str
    two_stage_max_circle: bool = False

@dataclass
class BenchmarkResult:
    time_seconds: Optional[float]
    success: bool
    output: str

# =============================================================================
# System Information Collection
# =============================================================================

def get_system_info() -> SystemInfo:
    """Extract CPU information from /proc/cpuinfo"""
    cpu_model = "Unknown"
    physical_ids = set()
    core_ids = set()
    logical_threads = 0

    with open('/proc/cpuinfo', 'r') as f:
        for line in f:
            if line.startswith('model name'):
                cpu_model = line.split(':', 1)[1].strip()
            elif line.startswith('physical id'):
                physical_ids.add(line.split(':', 1)[1].strip())
            elif line.startswith('core id'):
                core_ids.add(line.split(':', 1)[1].strip())
            elif line.startswith('processor'):
                logical_threads += 1

    physical_cores = len(physical_ids) * len(core_ids)
    return SystemInfo(cpu_model, physical_cores, logical_threads)

def print_system_info(info: SystemInfo):
    """Print system information"""
    print("=" * 70)
    print("System Information")
    print("=" * 70)
    print(f"CPU Model: {info.cpu_model}")
    print(f"Physical cores: {info.physical_cores}")
    print(f"Logical threads: {info.logical_threads}")
    print()

# =============================================================================
# Build Management
# =============================================================================

def build_configuration(config: Configuration) -> bool:
    """Clean and build the project with given configuration"""
    print(f"\nBuilding configuration: {config.name}")
    print(f"  OpenMP: {config.use_openmp}, SIMD: {config.use_simd}, Adaptive: {config.adaptive_search}")

    # Clean first
    clean_cmd = ["make", "clean"]
    result = subprocess.run(clean_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: make clean failed")
        print(f"  Output: {result.stderr}")
        return False

    # Build with configuration arguments
    build_cmd = ["make"]
    if config.make_args:
        build_cmd.extend(config.make_args.split())

    result = subprocess.run(build_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: make failed")
        print(f"  Output: {result.stderr}")
        return False

    print("  Build succeeded")
    return True

# =============================================================================
# Test Execution
# =============================================================================

def run_single_test(test_case: TestCase, adaptive_search: bool, two_stage_max_circle: bool = False) -> BenchmarkResult:
    """Run a single test case and extract the execution time"""
    # Prepare interactive input
    datasets = sorted([d for d in os.listdir('data') if os.path.isdir(os.path.join('data', d))])
    # Filter to only dirs that have data files (same as the C++ program)
    datasets = [d for d in datasets if
                os.path.isfile(os.path.join('data', d, 'all_data.csv')) and
                os.path.isfile(os.path.join('data', d, 'Point_3D.npy'))]
    try:
        dataset_index = datasets.index(test_case.dataset) + 1
    except ValueError:
        print(f"  ERROR: Dataset {test_case.dataset} not found in data/ directory")
        print(f"  Available datasets: {datasets}")
        return BenchmarkResult(None, False, "")

    enable_adaptive_input = '1' if adaptive_search else '0'
    two_stage_input = '1' if two_stage_max_circle else '0'
    input_str = (
        f"{dataset_index}\n"
        f"{test_case.instrument_length}\n"
        f"{test_case.instrument_radius}\n"
        f"{test_case.begin_deep}\n"
        f"{test_case.end_deep}\n"
        f"{test_case.num_step}\n"
        f"{enable_adaptive_input}\n"
        f"\n"  # enable_outer_parallel (default)
        f"\n"  # outer_tasks (default)
        f"\n"  # enable_inner_parallel (default)
        f"\n"  # inner_threads (default)
        f"{two_stage_input}\n"
    )

    try:
        result = subprocess.run(
            ['./projection_method'],
            input=input_str,
            capture_output=True,
            text=True,
            timeout=300
        )
    except subprocess.TimeoutExpired as e:
        return BenchmarkResult(None, False, f"Timeout: {e}")

    output = result.stdout + result.stderr

    # Extract total time using regex
    # Pattern matches: "总耗时 0.11 秒" or "总耗时: 2.65 秒"
    # Need to find the LAST occurrence because intermediate steps have "当前总耗时"
    pattern = r'总耗时[:\s]*(\d+\.?\d*)'
    matches = list(re.finditer(pattern, output))

    if not matches:
        # Try English pattern just in case
        pattern = r'Total time[:\s]*(\d+\.?\d*)'
        matches = list(re.finditer(pattern, output))

    if not matches:
        print(f"  ERROR: Could not find total time in output")
        print(f"  Output preview: {output[-500:]}")
        return BenchmarkResult(None, False, output)

    # Take the last match (final total vs intermediate current total)
    time_seconds = float(matches[-1].group(1))
    # Program returns: 0 = tool passed all, 1 = tool found stuck (both are successful runs)
    # Only non-zero/zero on actual error (crash, etc.)
    success = result.returncode == 0 or result.returncode == 1
    return BenchmarkResult(time_seconds, success, output)

# =============================================================================
# Result Reporting
# =============================================================================

def print_results_table(dataset_name: str, results: List[Tuple[str, float]], baseline_time: float):
    """Print formatted results table"""
    print(f"\n{'=' * 70}")
    print(f"Results for Dataset: {dataset_name} (100m pass test)")
    print(f"{'=' * 70}")

    print(f"\n{'Configuration':<40} {'Time (s)':>10} {'Speedup':>10}")
    print(f"{'-' * 40} {'-' * 10} {'-' * 10}")

    speedup = baseline_time / baseline_time
    print(f"{'Python Baseline':<40} {baseline_time:>10.2f} {speedup:>10.1f}×")

    for config_name, time in results:
        if time is None or time <= 0:
            print(f"{config_name:<40} {'FAILED':>10} {'N/A':>10}")
        else:
            speedup = baseline_time / time
            print(f"{config_name:<40} {time:>10.2f} {speedup:>10.1f}×")

    print()

# =============================================================================
# Main
# =============================================================================

def main():
    # Test cases
    test_cases = [
        TestCase("Dataset-1", "cannot_pass", 1.0, 0.05, 3300.0, 3400.0, 0.5),
        TestCase("Dataset-1", "pass", 1.0, 0.025, 3300.0, 3400.0, 0.5),
        TestCase("Dataset-2", "cannot_pass", 1.0, 0.055, 4300.0, 4400.0, 0.5),
        TestCase("Dataset-2", "pass", 1.0, 0.05, 4300.0, 4400.0, 0.5),
    ]

    configurations = [
        Configuration("C++ Serial", False, False, False, "USE_OPENMP=0 USE_SIMD=0"),
        Configuration("C++ + OpenMP", True, False, False, "USE_OPENMP=1 USE_SIMD=0"),
        Configuration("C++ + OpenMP + SIMD", True, True, False, "USE_OPENMP=1 USE_SIMD=1"),
        Configuration("C++ + OpenMP + SIMD + Adaptive Search", True, True, True, "USE_OPENMP=1 USE_SIMD=1"),
        Configuration("C++ + OpenMP + SIMD + Adaptive + TwoStage", True, True, True, "USE_OPENMP=1 USE_SIMD=1", two_stage_max_circle=True),
    ]

    # Cached baseline times from previous run
    baseline_results = {
        "Dataset-1": 198.99,
        "Dataset-2": 200.92,
    }

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    info = get_system_info()
    print_system_info(info)

    print("Using cached baseline times (Python baseline already run):")
    for dataset, baseline in baseline_results.items():
        print(f"  {dataset}: {baseline:.2f}s")
    print()

    all_results: Dict[str, Dict[str, Dict[str, Optional[float]]]] = {}

    for config in configurations:
        print(f"\n{'=' * 70}")
        print(f"Testing configuration: {config.name}")
        print(f"{'=' * 70}")

        if not build_configuration(config):
            for tc in test_cases:
                if tc.dataset not in all_results:
                    all_results[tc.dataset] = {}
                if tc.name not in all_results[tc.dataset]:
                    all_results[tc.dataset][tc.name] = {}
                all_results[tc.dataset][tc.name][config.name] = None
            continue

        for tc in test_cases:
            if tc.dataset not in all_results:
                all_results[tc.dataset] = {}
            if tc.name not in all_results[tc.dataset]:
                all_results[tc.dataset][tc.name] = {}

            print(f"\n  Running test: {tc.dataset}/{tc.name}")
            print(f"    Params: L={tc.instrument_length}m, R={tc.instrument_radius}m, range={tc.begin_deep}-{tc.end_deep}m")

            result = run_single_test(tc, config.adaptive_search, config.two_stage_max_circle)
            if result.success and result.time_seconds is not None:
                all_results[tc.dataset][tc.name][config.name] = result.time_seconds
                print(f"    Result: {result.time_seconds:.4f}s")
            else:
                all_results[tc.dataset][tc.name][config.name] = None
                print(f"    Result: FAILED")

    print("\n")
    print("=" * 70)
    print("FINAL BENCHMARK RESULTS")
    print("=" * 70)

    datasets = ["Dataset-1", "Dataset-2"]
    for dataset in datasets:
        baseline_time = baseline_results.get(dataset)
        if baseline_time is None:
            continue

        if dataset not in all_results or "pass" not in all_results[dataset]:
            continue

        pass_results = all_results[dataset]["pass"]
        result_list = [(config_name, time)
                      for config_name, time in pass_results.items()
                      if time is not None]

        if result_list:
            print_results_table(dataset, result_list, baseline_time)

    print("\nDetailed Results (all test cases):")
    print("-" * 70)

    for dataset in sorted(all_results.keys()):
        for scenario in sorted(all_results[dataset].keys()):
            print(f"\n  {dataset} - {scenario}:")
            print(f"    {'Configuration':<35} {'Time (s)':>10}")
            print(f"    {'-' * 35} {'-' * 10}")

            baseline = baseline_results.get(dataset)

            for config_name, time in all_results[dataset][scenario].items():
                if time is None:
                    print(f"    {config_name:<35} {'FAILED':>10}")
                else:
                    if baseline is not None and time > 0:
                        speedup = baseline / time
                        print(f"    {config_name:<35} {time:>10.2f} ({speedup:.1f}×)")
                    else:
                        print(f"    {config_name:<35} {time:>10.2f}")

    print("\nBenchmark completed!")

if __name__ == "__main__":
    main()
