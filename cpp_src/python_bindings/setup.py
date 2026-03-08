import os
import sys
from pathlib import Path
from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup

# Get the parent directory (cpp_src)
cpp_src_dir = Path(__file__).parent.parent.absolute()
project_root = cpp_src_dir.parent.absolute()

compile_args = [
    "-O3",
    "-march=native",
    "-ffast-math",
]
link_args = []
include_dirs = [
    str(cpp_src_dir),
    str(project_root / "c_src"),
]

if os.environ.get("PROJECTION_USE_OPENMP") == "1":
    if sys.platform == "darwin":
        default_libomp_prefix = os.popen("brew --prefix libomp 2>/dev/null").read().strip() or "/opt/homebrew/opt/libomp"
        libomp_prefix = Path(os.environ.get("LIBOMP_PREFIX", default_libomp_prefix))
        compile_args.extend(["-Xpreprocessor", "-fopenmp", f"-I{libomp_prefix / 'include'}"])
        link_args.extend([f"-L{libomp_prefix / 'lib'}", "-lomp"])
    else:
        compile_args.append("-fopenmp")
        link_args.append("-fopenmp")

# Define the extension module
ext_modules = [
    Pybind11Extension(
        "projection_cpp",
        sources=[
            str(cpp_src_dir / "python_bindings" / "bindings.cpp"),
            str(cpp_src_dir / "projection_method.cpp"),
            str(cpp_src_dir / "file_io_improved.cpp"),
            str(project_root / "c_src" / "projection_c_python_adapter.cpp"),
        ],
        include_dirs=include_dirs,
        cxx_std=17,
        extra_compile_args=compile_args,
        extra_link_args=link_args,
        define_macros=[
            ("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION"),
        ],
    ),
]

setup(
    name="projection_cpp",
    version="1.0.0",
    author="SWPU Competition Team",
    description="C++ implementation of projection method for wellbore passability",
    long_description="High-performance C++ implementation of the projection method algorithm "
                     "for calculating wellbore passability. Provides 134x speedup over pure Python.",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.19.0",
        "pandas>=1.0.0",
    ],
)
