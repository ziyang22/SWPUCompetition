#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能对比脚本：比较 Python 和 C++ 版本的执行时间
"""

import subprocess
import time
import sys
import os

def run_python_version():
    """运行 Python 版本并计时"""
    print("=" * 60)
    print("运行 Python 版本...")
    print("=" * 60)

    start_time = time.time()

    # 修改 TouYingFa.py 的参数并运行
    result = subprocess.run(
        ['/opt/homebrew/Caskroom/miniconda/base/bin/conda', 'run', '-n', 'SWPUCompetiton', 'python', 'python_src/TouYingFa.py'],
        capture_output=True,
        text=True
    )

    end_time = time.time()
    elapsed = end_time - start_time

    print(result.stdout)
    if result.stderr:
        print("错误:", result.stderr)

    return elapsed, result.returncode == 0

def run_cpp_version():
    """运行 C++ 版本并计时"""
    print("\n" + "=" * 60)
    print("运行 C++ 版本...")
    print("=" * 60)

    # 检查可执行文件是否存在
    executable = None
    if os.path.exists('./build/projection_method'):
        executable = './build/projection_method'
    elif os.path.exists('./projection_method'):
        executable = './projection_method'
    else:
        print("错误: 找不到 C++ 可执行文件")
        print("请先运行: make 或 ./build_and_test.sh")
        return None, False

    start_time = time.time()

    result = subprocess.run(
        [executable, '1.0', '0.025', '3300', '3400', '0.5'],
        capture_output=True,
        text=True
    )

    end_time = time.time()
    elapsed = end_time - start_time

    print(result.stdout)
    if result.stderr:
        print("错误:", result.stderr)

    return elapsed, result.returncode == 0

def main():
    print("\n" + "=" * 60)
    print("投影法算法性能对比测试")
    print("=" * 60)
    print()

    # 运行 Python 版本
    py_time, py_success = run_python_version()

    # 运行 C++ 版本
    cpp_time, cpp_success = run_cpp_version()

    # 输出对比结果
    print("\n" + "=" * 60)
    print("性能对比结果")
    print("=" * 60)

    if py_success:
        print(f"Python 版本总耗时: {py_time:.2f} 秒")
    else:
        print("Python 版本执行失败")

    if cpp_time is not None and cpp_success:
        print(f"C++ 版本总耗时:    {cpp_time:.2f} 秒")

        if py_success:
            speedup = py_time / cpp_time
            print(f"\n加速比: {speedup:.2f}x")
            print(f"性能提升: {((speedup - 1) * 100):.1f}%")
    else:
        print("C++ 版本执行失败或未找到")

    print("=" * 60)
    print()

if __name__ == "__main__":
    main()
