#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C++ 和 Python 输出对比工具
比较两个版本生成的输出文件，排除耗时列
"""

import pandas as pd
import numpy as np
import sys

def compare_outputs(cpp_file, py_file, tolerance=1e-6):
    """
    对比 C++ 和 Python 版本的输出

    Args:
        cpp_file: C++ 版本生成的文件
        py_file: Python 版本生成的文件
        tolerance: 数值容差

    Returns:
        bool: 是否一致
    """
    print(f"\n对比文件:")
    print(f"  C++:    {cpp_file}")
    print(f"  Python: {py_file}")
    print("=" * 60)

    try:
        df_cpp = pd.read_csv(cpp_file)
        df_py = pd.read_csv(py_file)

        # 标准化列名
        cpp_cols = [col.strip() for col in df_cpp.columns]
        py_cols = [col.strip() for col in df_py.columns]

        df_cpp.columns = cpp_cols
        df_py.columns = py_cols

        # 排除耗时列
        time_columns = ['当前段耗时(s)', '总耗时(s)']
        compare_columns = [col for col in py_cols if col not in time_columns]

        print(f"\n对比列: {compare_columns}")

        # 检查行数
        if len(df_cpp) != len(df_py):
            print(f"\n❌ 行数不一致:")
            print(f"   C++:    {len(df_cpp)} 行")
            print(f"   Python: {len(df_py)} 行")
            return False

        print(f"✓ 行数一致: {len(df_cpp)} 行")

        # 逐列对比
        all_match = True
        for col in compare_columns:
            if col not in df_cpp.columns:
                print(f"\n❌ C++ 输出缺少列: {col}")
                all_match = False
                continue

            diff = np.abs(df_cpp[col].values - df_py[col].values)
            max_diff = np.max(diff)

            if max_diff > tolerance:
                print(f"\n❌ 列 '{col}' 不一致:")
                print(f"   最大差异: {max_diff:.10f}")

                # 显示前几个不一致的行
                mismatch_indices = np.where(diff > tolerance)[0]
                print(f"   不一致行数: {len(mismatch_indices)}")
                for idx in mismatch_indices[:3]:
                    print(f"   行 {idx}: C++={df_cpp[col].iloc[idx]:.10f}, "
                          f"Python={df_py[col].iloc[idx]:.10f}, "
                          f"差异={diff[idx]:.10f}")
                all_match = False
            else:
                print(f"✓ 列 '{col}' 一致 (最大差异: {max_diff:.10e})")

        if all_match:
            print("\n" + "=" * 60)
            print("✅ C++ 和 Python 版本输出完全一致!")
            print("=" * 60)
            return True
        else:
            print("\n" + "=" * 60)
            print("❌ 发现差异")
            print("=" * 60)
            return False

    except Exception as e:
        print(f"\n❌ 对比出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    if len(sys.argv) < 3:
        print("用法: python compare_cpp_py.py <cpp_output_file> <py_output_file>")
        print("\n示例:")
        print("  python compare_cpp_py.py pass_last_5m_3400m.txt PassedExample/pass_last_5m_3400m.txt")
        sys.exit(1)

    cpp_file = sys.argv[1]
    py_file = sys.argv[2]

    result = compare_outputs(cpp_file, py_file)
    sys.exit(0 if result else 1)

if __name__ == "__main__":
    main()
