#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对比生成结果目录与期望基准目录中的输出文件，排除耗时列。
默认兼容旧行为：不传参数时比较 output/ 与 data/PassedExample、data/FailedExample。
"""

import argparse
import os
import re
import sys
import pandas as pd
import numpy as np


TIME_COLUMNS = ['当前段耗时(s)', '总耗时(s)']
DEFAULT_EXAMPLE_DIRS = ['PassedExample', 'FailedExample']
FILE_FAMILY_PATTERNS = {
    'pass': r'^pass_last_5m_.*\.txt$',
    'stuck': r'^stuck_point_.*\.txt$',
    'final': r'^final_result_.*\.txt$',
}


def compare_files(generated_file, expected_file, tolerance=1e-6):
    print(f"\n{'='*60}")
    print(f"对比文件: {os.path.basename(generated_file)}")
    print(f"参考文件: {expected_file}")
    print(f"{'='*60}")

    if not os.path.exists(generated_file):
        print(f"❌ 错误: 生成的文件不存在: {generated_file}")
        return False

    if not os.path.exists(expected_file):
        print(f"❌ 错误: 期望的文件不存在: {expected_file}")
        return False

    try:
        df_generated = pd.read_csv(generated_file)
        df_expected = pd.read_csv(expected_file)

        gen_cols = [col.strip() for col in df_generated.columns]
        exp_cols = [col.strip() for col in df_expected.columns]

        df_generated.columns = gen_cols
        df_expected.columns = exp_cols

        compare_columns = [col for col in exp_cols if col not in TIME_COLUMNS]

        print(f"\n对比的列: {compare_columns}")
        print(f"排除的列: {TIME_COLUMNS}")

        if len(df_generated) != len(df_expected):
            print(f"\n❌ 行数不一致:")
            print(f"   生成文件: {len(df_generated)} 行")
            print(f"   期望文件: {len(df_expected)} 行")
            return False

        print(f"\n✓ 行数一致: {len(df_generated)} 行")

        all_match = True
        for col in compare_columns:
            if col not in df_generated.columns:
                print(f"\n❌ 生成文件缺少列: {col}")
                all_match = False
                continue

            diff = np.abs(df_generated[col].values - df_expected[col].values)
            max_diff = np.max(diff)

            if max_diff > tolerance:
                print(f"\n❌ 列 '{col}' 数值不一致:")
                print(f"   最大差异: {max_diff:.10f}")
                print(f"   容差阈值: {tolerance}")
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
            print("✅ 所有数据列均一致！")
            print(f"{'='*60}")
            return True

        print(f"\n{'='*60}")
        print("❌ 存在不一致的数据")
        print(f"{'='*60}")
        return False

    except Exception as e:
        print(f"\n❌ 对比过程出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def split_name_and_depth(filename):
    match = re.match(r'^(.*_)([-+]?\d+(?:\.\d+)?)m\.txt$', filename)
    if match:
        return match.group(1), float(match.group(2))
    return None, None


def detect_family(filename):
    for family, pattern in FILE_FAMILY_PATTERNS.items():
        if re.match(pattern, filename):
            return family
    return None


def find_files_by_family(directory, family):
    pattern = FILE_FAMILY_PATTERNS[family]
    return sorted(
        os.path.join(directory, name)
        for name in os.listdir(directory)
        if name.endswith('.txt') and re.match(pattern, name)
    )


def find_candidate_files(generated_dir, expected_name, strict_filenames=False):
    exact_match = os.path.join(generated_dir, expected_name)
    if os.path.exists(exact_match):
        return [exact_match]

    if strict_filenames:
        return []

    family = detect_family(expected_name)
    if family is not None:
        return find_files_by_family(generated_dir, family)

    prefix, expected_depth = split_name_and_depth(expected_name)
    if prefix is None:
        return []

    candidates = []
    for name in os.listdir(generated_dir):
        if not name.endswith('.txt'):
            continue
        candidate_prefix, candidate_depth = split_name_and_depth(name)
        if candidate_prefix != prefix:
            continue
        candidates.append((abs(candidate_depth - expected_depth), os.path.join(generated_dir, name)))

    candidates.sort(key=lambda item: item[0])
    return [path for _, path in candidates]


def expected_files_for_mode(expected_dir, mode):
    all_txt = sorted(
        os.path.join(expected_dir, name)
        for name in os.listdir(expected_dir)
        if name.endswith('.txt')
    )

    if mode == 'auto':
        return all_txt

    families = ['pass'] if mode == 'pass' else ['stuck', 'final']
    result = []
    for path in all_txt:
        family = detect_family(os.path.basename(path))
        if family in families:
            result.append(path)
    return result


def compare_expected_file(generated_dir, expected_file_path, tolerance=1e-6, strict_filenames=False):
    expected_name = os.path.basename(expected_file_path)
    candidate_files = find_candidate_files(generated_dir, expected_name, strict_filenames=strict_filenames)

    if not candidate_files:
        print(f"\n❌ 未找到可用于对比的生成文件: {expected_name}")
        return False

    if len(candidate_files) > 1:
        print(f"\n❌ 生成目录中存在多个候选文件，无法唯一匹配: {expected_name}")
        for path in candidate_files:
            print(f"   - {path}")
        return False

    return compare_files(candidate_files[0], expected_file_path, tolerance=tolerance)


def parse_args():
    parser = argparse.ArgumentParser(description='对比生成结果目录与期望基准目录')
    parser.add_argument('--generated-dir', help='生成结果目录')
    parser.add_argument('--expected-dir', help='期望基准目录')
    parser.add_argument('--tolerance', type=float, default=1e-6)
    parser.add_argument('--mode', choices=['auto', 'pass', 'fail'], default='auto')
    parser.add_argument('--strict-filenames', action='store_true')
    return parser.parse_args()


def run_single_directory_check(generated_dir, expected_dir, tolerance, mode, strict_filenames):
    expected_file_paths = expected_files_for_mode(expected_dir, mode)
    if not expected_file_paths:
        print(f"❌ 目录中没有找到可对比的 .txt 文件: {expected_dir}")
        return False

    print(f"\n找到 {len(expected_file_paths)} 个期望输出文件:")
    for path in expected_file_paths:
        print(f"  - {path}")

    all_passed = True
    for expected_file_path in expected_file_paths:
        result = compare_expected_file(
            generated_dir,
            expected_file_path,
            tolerance=tolerance,
            strict_filenames=strict_filenames,
        )
        if not result:
            all_passed = False
    return all_passed


def main():
    args = parse_args()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)

    if args.generated_dir and args.expected_dir:
        generated_dir = os.path.abspath(args.generated_dir)
        expected_dir = os.path.abspath(args.expected_dir)
        all_passed = run_single_directory_check(
            generated_dir,
            expected_dir,
            args.tolerance,
            args.mode,
            args.strict_filenames,
        )
    else:
        generated_dir = os.path.join(root_dir, 'output')
        data_dir = os.path.join(root_dir, 'data')
        all_passed = True
        for example_dir_name in DEFAULT_EXAMPLE_DIRS:
            expected_dir = os.path.join(data_dir, example_dir_name)
            if not os.path.exists(expected_dir):
                print(f"❌ 示例目录不存在: {expected_dir}")
                sys.exit(1)
            result = run_single_directory_check(
                generated_dir,
                expected_dir,
                args.tolerance,
                'auto',
                args.strict_filenames,
            )
            if not result:
                all_passed = False

    print(f"\n{'='*60}")
    if all_passed:
        print('🎉 所有文件对比通过！')
    else:
        print('⚠️  部分文件对比失败，请检查上述输出')
    print(f"{'='*60}\n")

    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
