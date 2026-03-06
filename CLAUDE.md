# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a SWPU Competition project that implements a **projection method algorithm** for calculating wellbore passability. The core algorithm determines whether drilling tools can pass through a wellbore by projecting 3D wellbore wall points onto planes and calculating maximum inscribed circles.

**Primary Languages**:
- C++ (high-performance implementation, 134x faster)
- Python 3.8+ (original implementation)

**Core Implementations**:
- C++: `cpp_src/projection_method.cpp` (main algorithm)
- Python: `python_src/TouYingFa.py` (original reference)

## Project Structure

```
.
├── cpp_src/              # C++ source code
├── python_src/           # Python source code
├── data/                 # Dataset directory
│   ├── default/         # Default dataset (used in CLI mode)
│   ├── PassedExample/   # Example where tool passes
│   └── FailedExample/   # Example where tool gets stuck
├── output/              # Output files directory
├── scripts/             # Utility scripts
├── docs/                # Documentation
├── build/               # Build artifacts
└── Makefile             # Build configuration
```

## Environment Setup

### C++ Version (Recommended)

```bash
# Compile
make

# Run interactively (select dataset)
./projection_method

# Run with command line arguments (uses default dataset)
./projection_method 1.0 0.025 3300 3400 0.5
```

### Python Version

The project uses a Conda environment named `SWPUCompetiton`:

```bash
# Activate environment
conda activate SWPUCompetiton

# Run the main script
python python_src/TouYingFa.py

# Run output verification
python scripts/check_output.py
```

**Required Libraries**:
- NumPy (array operations, 3D geometry calculations)
- Pandas (CSV data handling)
- Matplotlib (visualization, optional)
- SciPy (scientific computing)

## Input Data Files

Each dataset directory (under `data/`) contains:
- `all_data.csv`: Wellbore trajectory data with columns including DEPTH, N, E, H (coordinates), DEV, DAZ (deviation/azimuth), and 24 FING columns (finger caliper measurements)
- `Point_3D.npy`: 3D wellbore wall coordinates, shape (37760, 24, 3) representing (depth_points, circumferential_points, xyz_coordinates)

## Core Algorithm Architecture

### C++ Implementation

**Main Entry**: `cpp_src/main.cpp`
- Supports interactive dataset selection
- Supports command line mode with parameters
- Loads data from `data/` directory

**Core Calculator**: `cpp_src/projection_method.cpp`
- `ProjectionCalculator::calculate()` - Main calculation loop
- Same algorithm as Python version, optimized for performance

**Key Parameters**:
- `instrument_length`: Tool length in meters (default: 1m)
- `instrument_radius`: Tool radius in meters (default: 0.025m)
- `begin_deep`, `end_deep`: Depth range to analyze
- `num_step`: Step size in meters (default: 0.5m)

**Algorithm Flow**:
1. Iterates through wellbore depth in sliding windows of `instrument_length`
2. For each window, calculates projection directions around the main axis (within `delta` angle)
3. Projects upper plane points onto lower plane using `linePlane()`
4. Converts 3D projections to 2D using `point3dTo2d()`
5. Finds inner boundary points with `getClosestPoints()`
6. Calculates maximum inscribed circle using `maxIncircle()`
7. Determines if tool radius fits within the maximum inscribed circle

### Python Implementation (Reference)

**Main Function**: `Projection2()` in `python_src/TouYingFa.py`

**Supporting Functions**:
- `line_plane()`: Calculates intersection of line and plane
- `projection_direction()`: Generates projection directions within a cone angle
- `point_3d_to_2d()`: Projects 3D points onto 2D plane
- `get_closest_points()`: Groups points by slope and finds closest points
- `max_incircle()`: Grid-based search for maximum inscribed circle

## Output Files

All output files are saved in the `output/` directory:

**If tool passes through**:
- `output/pass_last_5m_{end_deep}m.txt`: Last 5 meters of data with columns: depth, tool_length, center_x, center_y, diameter, current_time, total_time

**If tool gets stuck**:
- `output/stuck_point_{depth}m.txt`: Last 5 meters before stuck point
- `output/final_result_{depth}m.txt`: Summary with tool_length, tool_radius, stuck_depth, max_passable_diameter

## Testing and Verification

Use `scripts/check_output.py` to verify output correctness:

```bash
python scripts/check_output.py
```

This script:
- Compares generated output files in `output/` against `data/PassedExample/` directory
- Excludes timing columns from comparison (only validates geometric results)
- Reports differences with tolerance of 1e-6
- Useful for regression testing after algorithm modifications

## Dataset Management

The program supports multiple datasets:

1. **Interactive Mode**: Run `./projection_method` without arguments
   - Lists all available datasets in `data/` directory
   - User selects dataset interactively
   - User inputs calculation parameters (or uses defaults)

2. **Command Line Mode**: Run with 5 arguments
   - Uses `data/default/` dataset automatically
   - Parameters: `./projection_method <length> <radius> <begin> <end> <step>`

To add a new dataset:
1. Create a directory under `data/` (e.g., `data/my_dataset/`)
2. Add `all_data.csv` and `Point_3D.npy` to the directory
3. The dataset will appear in interactive mode automatically

## Key Configuration

**Default Parameters**:
```cpp
instrument_length = 1.0      // Tool length (m)
instrument_radius = 0.025    // Tool radius (m)
begin_deep = 3300.0          // Start depth (m)
end_deep = 3400.0            // End depth (m)
num_step = 0.5               // Step size (m)
```

**Important**: `num_step` must be less than `instrument_length` (enforced by exception)

## Algorithm Performance Notes

- C++ version: ~2.65 seconds for 100m depth range
- Python version: ~354 seconds for same range
- Speedup: 134x
- Computation time is tracked per window and cumulatively
- Grid resolution for `maxIncircle()` is configurable
- Projection direction sampling uses multiple angle steps within the cone

## Common Modifications

When modifying the algorithm:

1. **C++ Code**:
   - Adjust `delta` in `projection_method.cpp` to change projection cone angle
   - Modify grid_num in `maxIncircle()` call for accuracy vs speed tradeoff
   - Change angle_step for projection direction sampling density
   - Always run `make clean && make` after changes
   - Run `python scripts/check_output.py` to verify correctness

2. **Python Code**:
   - Located in `python_src/TouYingFa.py`
   - Adjust parameters in the main block
   - Run `python python_src/TouYingFa.py` to test

3. **File Paths**:
   - Data files: `data/<dataset_name>/`
   - Output files: `output/`
   - Scripts: `scripts/`
   - Documentation: `docs/`

## Build System

**Makefile targets**:
```bash
make           # Compile the project
make clean     # Clean build artifacts
make test      # Compile, run, and verify output
```

**Build output**:
- Object files: `build/*.o`
- Executable: `projection_method` (in root directory)

## Important Notes

- The C++ version produces identical results to Python (verified to 1e-10 precision)
- Output files are automatically saved to `output/` directory
- The `output/` directory is preserved in git (contains `.gitkeep`)
- Data files in root directory (`all_data.csv`, `Point_3D.npy`) are kept for backward compatibility
- The `examples/` directory is kept for reference but data is now in `data/` directory
