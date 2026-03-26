#!/usr/bin/env python3
"""
Comprehensive Benchmarking Script for Wellbore Passability Calculation

Tests all required test cases:
- Two datasets: Dataset-1 and Dataset-2
- Each dataset has two scenarios: cannot_pass and pass
- C++ configurations: 4 levels of optimization

For each dataset-scenario pair with corresponding Python baseline:
1. Python baseline (pass scenario, 100m range)
2. C++ Serial
3. C++ + OpenMP
4. C++ + OpenMP + SIMD
5. C++ + OpenMP + SIMD + Adaptive Search

Output saved to logs/ directory with timestamp.

Usage:
    python automated_benchmark.py [--skip-python]

Options:
    --skip-python: Skip Python baseline tests (Phase 1), start directly from C++ tests (Phase 2)
"""

import os
import re
import subprocess
import sys
import argparse
from datetime import datetime
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

@dataclass
class BenchmarkResult:
    time_seconds: Optional[float]
    success: bool
    output: str

# =============================================================================
# Logging Functions
# =============================================================================

def setup_logging():
    """Create logs directory and return log file path"""
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f"benchmark_{timestamp}.log")

    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"Benchmark_log started at {datetime.now().isoformat()}\n\n")
        f.write(f"Host: {os.uname()}\n")
        f.write(f"Working directory: {os.getcwd()}\n")
        f.write("=" * 70 + "\n\n")

    return log_file

def log_section(log_file, title):
    """Write a section header to log file"""
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write("\n" + "=" * 70 + "\n")
        f.write(f" {title}\n")
        f.write("=" * 70 + "\n\n")

def log_message(log_file, message):
    """Write a message to log file"""
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().isoformat()} - {message}\n")

def log_error(log_file, error):
    """Write an error to log file"""
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().isoformat()} - ERROR: {error}\n")

def log_result(log_file, config_name, dataset_name, scenario_name, time_seconds, success, output):
    """Write test result to log file"""
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\nResult [{config_name}] on {dataset_name}/{scenario_name}:\n")
        if success and time_seconds is not None:
            f.write(f"  Time: {time_seconds:.4f}s\n")
        else:
            f.write(f"  Time: FAILED\n")
        f.write(f" Success: {success}\n")
        f.write(f"  Output preview (last 500 chars):\n")
        f.write("-" * 50 + "\n")
        f.write(output[-500:] if len(output) > 500 else output)
        f.write("-" * 50 + "\n")

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

def log_system_info(log_file, info: SystemInfo):
    """Log system information"""
    log_section(log_file, "System Information")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"CPU Model: {info.cpu_model}\n")
        f.write(f"Physical cores: {info.physical_cores}\n")
        f.write(f"Logical threads: {info.logical_threads}\n")

# =============================================================================
# Build Management
# =============================================================================

def build_configuration(log_file, config: Configuration) -> bool:
    """Clean and build project with given configuration"""
    log_message(log_file, f"Building configuration: {config.name}")
    log_message(log_file, f"  OpenMP: {config.use_openmp}, SIMD: {config.use_simd}, Adaptive: {config.adaptive_search}")

    # Clean first
    clean_cmd = ["make", "clean"]
    result = subprocess.run(clean_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log_error(log_file, f"make clean failed: {result.stderr}")
        return False

    log_message(log_file, "Clean succeeded")

    # Build with configuration arguments
    build_cmd = ["make"]
    if config.make_args:
        build_cmd.extend(config.make_args.split())

    result = subprocess.run(build_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log_error(log_file, f"make failed: {result.stderr}")
        return False

    log_message(log_file, "Build succeeded")
    return True

# =============================================================================
# Test Execution
# =============================================================================

def run_single_test(log_file, test_case: TestCase, adaptive_search: bool) -> BenchmarkResult:
    """Run a single test case and extract execution time"""
    # Prepare interactive input
    datasets = sorted([d for d in os.listdir('data') if os.path.isdir(os.path.join('data', d))])
    try:
        dataset_index = datasets.index(test_case.dataset) + 1  # 1-based indexing
    except ValueError:
        error_msg = f"Dataset {test_case.dataset} not found in data/ directory. Available: {datasets}"
        log_error(log_file, error_msg)
        return BenchmarkResult(None, False, error_msg)

    enable_adaptive_input = '1' if adaptive_search else '0'
    input_str = (
        f"{dataset_index}\n"
        f"{test_case.instrument_length}\n"
        f"{test_case.instrument_radius}\n"
        f"{test_case.begin_deep}\n"
        f"{test_case.end_deep}\n"
        f"{test_case.num_step}\n"
        f"{enable_adaptive_input}\n"
    )

    log_message(log_file, f"Running test: {test_case.dataset}/{test_case.name}")
    log_message(log_file, f"  Params: L={test_case.instrument_length}m, R={test_case.instrument_radius}m, range={test_case.begin_deep}-{test_case.end_deep}m")

    try:
        result = subprocess.run(
            ['./projection_method'],
            input=input_str,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
    except subprocess.TimeoutExpired as e:
        error_msg = f"Timeout after 300s: {e}"
        log_error(log_file, error_msg)
        return BenchmarkResult(None, False, error_msg)

    output = result.stdout + result.stderr

    # Extract total time using regex
    # Need to find LAST occurrence because intermediate steps have "当前总耗时"
    pattern = r'总耗时[:\s]*(\d+\.?\d*)'
    matches = list(re.finditer(pattern, output))

    if not matches:
        # Try English pattern just in case
        pattern = r'Total time[:\s]*(\d+\.?\d*)'
        matches = list(re.finditer(pattern, output))

    if not matches:
        log_error(log_file, "Could not find total time in output")
        log_message(log_file, f"Output preview (last 500 chars):\n{output[-500:]}")
        return BenchmarkResult(None, False, output)

    # Take the last match (final total vs intermediate current total)
    time_seconds = float(matches[-1].group(1))
    # Program returns: 0 = tool passed all, 1 = tool found stuck (both are successful runs)
    # Only non-zero/zero on actual error (crash, etc.)
    success = result.returncode == 0 or result.returncode == 1

    log_result(log_file, "Current test", test_case.dataset, test_case.name, time_seconds, success, output)
    return BenchmarkResult(time_seconds, success, output)

def run_python_baseline(log_file, dataset: str, instrument_length: float, instrument_radius: float,
                       begin_deep: float, end_deep: float) -> BenchmarkResult:
    """Run Python baseline version"""
    log_message(log_file, f"Running Python baseline on {dataset}...")

    cmd = [
        sys.executable,
        'python_src/TouYingFa.py',
        '--dataset', dataset,
        '--instrument-length', str(instrument_length),
        '--instrument-radius', str(instrument_radius),
        '--begin-deep', str(begin_deep),
        '--end-deep', str(end_deep),
        '--num-step', '0.5',
        '--output-dir', 'output',
    ]

    try:
        start_time = datetime.now()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout for Python
        )
        end_time = datetime.now()
    except subprocess.TimeoutExpired as e:
        error_msg = f"Timeout: {e}"
        log_error(log_file, error_msg)
        return BenchmarkResult(None, False, error_msg)

    output = result.stdout + result.stderr
    time_seconds = (end_time - start_time).total_seconds()
    success = result.returncode == 0

    if not success:
        log_error(log_file, "Python baseline failed")
        log_message(log_file, f"Output preview (last 500 chars):\n{output[-500:]}")
        return BenchmarkResult(None, False, output)

    log_result(log_file, "Python baseline", dataset, "pass", time_seconds, success, output)
    return BenchmarkResult(time_seconds, success, output)


# =============================================================================
# Result Reporting
# =============================================================================

def print_results_table(log_file, dataset_name: str, results: List[Tuple[str, float]], baseline_time: float):
    """Print formatted results table"""
    log_message(log_file, f"Results for Dataset: {dataset_name}")
    log_message(log_file, "=" * 70)
    log_message(log_file, f"{'Configuration':<40} {'Time (s)':>10} {'Speedup':>10}")
    log_message(log_file, "-" * 62)

    # Print baseline first
    speedup = baseline_time / baseline_time
    log_message(log_file, f"{'Python Baseline':<40} {baseline_time:>10.2f} {speedup:>10.1f}x")

    # Print other configurations
    for config_name, time in results:
        if time <= 0:
            log_message(log_file, f"{config_name:<40} {'N/A':>10}")
        else:
            speedup = baseline_time / time
            log_message(log_file, f"{config_name:<40} {time:>10.2f} {speedup:>10.1f}x")

    log_message(log_file, "")
    log_message(log_file, "")

    print()

# =============================================================================
# Main Benchmark Workflow
# =============================================================================

def main():
    """Main benchmark workflow"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skip-python', action='store_true',
                       help='Skip Python baseline tests (Phase 1), start directly from C++ tests (Phase 2)')

    args = parser.parse_args()
    skip_python = args.skip_python

    # Setup logging
    log_file = setup_logging()

    # Define test cases: two datasets × two scenarios each
    test_cases = [
        TestCase("Dataset-1", "cannot_pass", 1.0, 0.05, 3300.0, 3400.0, 0.5),
        TestCase("Dataset-1", "pass", 1.0, 0.025, 3300.0, 3400.0, 0.5),
        TestCase("Dataset-2", "cannot_pass", 1.0, 0.055, 4300.0, 4400.0, 0.5),
        TestCase("Dataset-2", "pass", 1.0, 0.05, 4300.0, 4400.0, 0.5),
    ]

    # Define configurations: 4 optimization levels
    configurations = [
        Configuration(
            name="C++ Serial",
            use_openmp=False,
            use_simd=False,
            adaptive_search=False,
            make_args="USE_OPENMP=0 USE_SIMD=0"
        ),
        Configuration(
            name="C++ + OpenMP",
            use_openmp=True,
            use_simd=False,
            adaptive_search=False,
            make_args="USE_OPENMP=1 USE_SIMD=0"
        ),
        Configuration(
            name="C++ + OpenMP + SIMD",
            use_openmp=True,
            use_simd=True,
            adaptive_search=False,
            make_args="USE_OPENMP=1 USE_SIMD=1"
        ),
        Configuration(
            name="C++ + OpenMP + SIMD + Adaptive Search",
            use_openmp=True,
            use_simd=True,
            adaptive_search=True,
            make_args="USE_OPENMP=1 USE_SIMD=1"
        ),
    ]

    # Change to project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    # Collect system info
    info = get_system_info()
    log_system_info(log_file, info)

    # Store all results
    all_results: Dict[str, Dict[str, Optional[float]]] = {}
    baseline_results: Dict[str, float] = {}

    # Phase 1: Python baseline tests (only if not skipped)
    if not skip_python:
        log_section(log_file, "Phase 1: Python Baseline Tests")
        log_message(log_file, "Running Python baselines for each dataset (pass scenario, 100m range)...")
        log_message(log_file, "This will be used as reference for speedup calculation.")

        # Only run baselines for pass scenarios as those are 100m
        pass_scenarios = [tc for tc in test_cases if tc.name == "pass"]
        for tc in pass_scenarios:
            if tc.dataset not in baseline_results:
                baseline_results[tc.dataset] = None

            log_message(log_file, f"Running Python baseline {tc.dataset}/pass")
            result = run_python_baseline(log_file, tc.dataset, tc.instrument_length,
                                          tc.instrument_radius, tc.begin_deep, tc.end_deep)
            if result.success and result.time_seconds is not None:
                baseline_results[tc.dataset] = result.time_seconds
                log_message(log_file, f"Python baseline time: {result.time_seconds:.2f}s")
            else:
                baseline_results[tc.dataset] = None
                log_error(log_file, f"Python baseline FAILED")
    else:
        log_section(log_file, "Phase 2: C++ Configuration Tests")
        log_message(log_file, "Skipping Python baselines, directly testing C++ optimizations...")

    # Phase 2: Test each C++ configuration
    for config in configurations:
        log_section(log_file, f"Phase 2: Testing configuration: {config.name}")

        # Build configuration
        if not build_configuration(log_file, config):
            # Mark all test cases as failed for this config
            for tc in test_cases:
                ds_key = f"{tc.dataset}_{tc.name}"
                if ds_key not in all_results:
                    all_results[ds_key] = {}
                if config.name not in all_results[ds_key]:
                    all_results[ds_key][config.name] = None
            continue

        # Run all test cases for this configuration
        for tc in test_cases:
            ds_key = f"{tc.dataset}_{tc.name}"
            if ds_key not in all_results:
                all_results[ds_key] = {}
            if config.name not in all_results[ds_key]:
                    all_results[ds_key][config.name] = None

            log_message(log_file, f"Running test: {tc.dataset}/{tc.name}")
            log_message(log_file, f"  Params: L={tc.instrument_length}m, R={tc.instrument_radius}m, range={tc.begin_deep}-{tc.end_deep}m")

            result = run_single_test(log_file, tc, config.adaptive_search)
            if result.success and result.time_seconds is not None:
                all_results[ds_key][config.name] = result.time_seconds
                log_message(log_file, f"Result: {result.time_seconds:.4f}s")
            else:
                all_results[ds_key][config.name] = None
                log_error(log_file, f"Test FAILED")

    # Generate final report
    log_section(log_file, "Phase 3: Final Benchmark Results Summary")
    log_message(log_file, f"Benchmark_log completed at {datetime.now().isoformat()}")

    # Print results to console
    print("\n")
    print("=" * 70)
    print("FINAL BENCHMARK RESULTS")
    print("=" * 70)

    # For each dataset, create a table for both scenarios (pass and cannot_pass)
    datasets = sorted(set([tc.dataset for tc in test_cases]))

    for dataset in datasets:
        # Get baseline time for this dataset
        log_message(log_file, f"\n=== Dataset: {dataset} ===")
        baseline_time = baseline_results.get(dataset)
        if baseline_time is None:
            continue

        # Print results for both scenarios
        scenarios = sorted(set([tc.name for tc in test_cases if tc.dataset == dataset]))
        for scenario in scenarios:
            print(f"\n{dataset} - {scenario}:")

            # Get the results for this dataset-scenario combination
            ds_key = f"{dataset}_{scenario}"
            results_dict = all_results.get(ds_key, {})

            if results_dict:
                log_message(log_file, f"{'Configuration':<35} {'Time (s)':>10}")
                log_message(log_file, "-" * 47)

                # Print Python baseline first if available
                baseline_for_scenario = baseline_time
                if baseline_for_scenario is not None:
                    log_message(log_file, f"{'Python Baseline':<35} {baseline_for_scenario:>10.2f} 1.0x")

                # Print C++ configuration results
                for config_name, time in results_dict.items():
                    if time is None:
                        log_message(log_file, f"{config_name:<35} {'FAILED':>10}")
                    else:
                        speedup = baseline_for_scenario / time if baseline_for_scenario is not None and time > 0 else 0
                        log_message(log_file, f"{config_name:<35} {time:>10.2f} ({speedup:.1f}x)")
                log_message(log_file, "")
                print()

    log_message(log_file, f"Benchmark completed!")
    print(f"Full log saved to: {log_file}")
    print("\nBenchmark completed!")

if __name__ == "__main__":
    main()
