#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检验 TouYingFa.py 在项目根目录下生成的文件与 PassedExample 中正确输出之间的差异
排除耗时部分的对比
"""

import os
import sys
import pandas as pd
import numpy as np


def compare_files(generated_file, expected_file, tolerance=1e-6):
    """
    对比两个输出文件，排除耗时列
    
    Args:
        generated_file: 生成的文件路径
        expected_file: 期望的正确文件路径
        tolerance: 数值对比的容差
    
    Returns:
        bool: 是否一致
    """
    print(f"\n{'='*60}")
    print(f"对比文件: {os.path.basename(generated_file)}")
    print(f"{'='*60}")
    
    # 检查文件是否存在
    if not os.path.exists(generated_file):
        print(f"❌ 错误: 生成的文件不存在: {generated_file}")
        return False
    
    if not os.path.exists(expected_file):
        print(f"❌ 错误: 期望的文件不存在: {expected_file}")
        return False
    
    try:
        # 读取文件
        df_generated = pd.read_csv(generated_file)
        df_expected = pd.read_csv(expected_file)
        
        # 获取列名（去除空格）
        gen_cols = [col.strip() for col in df_generated.columns]
        exp_cols = [col.strip() for col in df_expected.columns]
        
        df_generated.columns = gen_cols
        df_expected.columns = exp_cols
        
        # 排除耗时列
        time_columns = ['当前段耗时(s)', '总耗时(s)']
        compare_columns = [col for col in exp_cols if col not in time_columns]
        
        print(f"\n对比的列: {compare_columns}")
        print(f"排除的列: {time_columns}")
        
        # 检查行数
        if len(df_generated) != len(df_expected):
            print(f"\n❌ 行数不一致:")
            print(f"   生成文件: {len(df_generated)} 行")
            print(f"   期望文件: {len(df_expected)} 行")
            return False
        else:
            print(f"\n✓ 行数一致: {len(df_generated)} 行")
        
        # 逐列对比
        all_match = True
        for col in compare_columns:
            if col not in df_generated.columns:
                print(f"\n❌ 生成文件缺少列: {col}")
                all_match = False
                continue
            
            # 数值对比
            diff = np.abs(df_generated[col].values - df_expected[col].values)
            max_diff = np.max(diff)
            
            if max_diff > tolerance:
                print(f"\n❌ 列 '{col}' 数值不一致:")
                print(f"   最大差异: {max_diff:.10f}")
                print(f"   容差阈值: {tolerance}")
                
                # 显示前几个不一致的行
                mismatch_indices = np.where(diff > tolerance)[0]
                print(f"   不一致的行数: {len(mismatch_indices)}")
                print(f"\n   前5个不一致的行:")
                for idx in mismatch_indices[:5]:
                    print(f"   行 {idx}: 生成={df_generated[col].iloc[idx]:.10f}, "
                          f"期望={df_expected[col].iloc[idx]:.10f}, "
                          f"差异={diff[idx]:.10f}")
                all_match = False
            else:
                print(f"✓ 列 '{col}' 一致 (最大差异: {max_diff:.10e})")
        
        if all_match:
            print(f"\n{'='*60}")
            print(f"✅ 所有数据列均一致！")
            print(f"{'='*60}")
            return True
        else:
            print(f"\n{'='*60}")
            print(f"❌ 存在不一致的数据")
            print(f"{'='*60}")
            return False
            
    except Exception as e:
        print(f"\n❌ 对比过程出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    # 定义文件路径 - 从项目根目录查找
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)  # 上一级目录（项目根目录）
    output_dir = os.path.join(root_dir, "output")
    passed_example_dir = os.path.join(root_dir, "data", "PassedExample")

    # 查找所有需要对比的文件
    if not os.path.exists(passed_example_dir):
        print(f"❌ PassedExample 目录不存在: {passed_example_dir}")
        sys.exit(1)

    # 获取 PassedExample 中的所有 txt 文件
    expected_files = [f for f in os.listdir(passed_example_dir) if f.endswith('.txt')]

    if not expected_files:
        print(f"❌ PassedExample 目录中没有找到 .txt 文件")
        sys.exit(1)

    print(f"\n找到 {len(expected_files)} 个期望输出文件:")
    for f in expected_files:
        print(f"  - {f}")

    # 对比每个文件
    all_passed = True
    for expected_file in expected_files:
        generated_file = os.path.join(output_dir, expected_file)  # 在 output/ 目录查找
        expected_file_path = os.path.join(passed_example_dir, expected_file)

        result = compare_files(generated_file, expected_file_path)
        if not result:
            all_passed = False

    # 总结
    print(f"\n{'='*60}")
    if all_passed:
        print("🎉 所有文件对比通过！")
    else:
        print("⚠️  部分文件对比失败，请检查上述输出")
    print(f"{'='*60}\n")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
