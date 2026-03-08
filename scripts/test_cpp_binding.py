#!/usr/bin/env python3
"""
测试 C++ Python 绑定
对比 Python 原始实现和 C++ 实现的结果和性能
"""

import sys
import time
import numpy as np
import pandas as pd
from pathlib import Path

# 添加 python_src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "python_src"))

# 导入原始 Python 实现
from TouYingFa import Projection2

# 导入 C++/C 实现
try:
    from projection_cpp import Projection2_c, Projection2_cpp
    print("✓ C++/C 模块导入成功")
except ImportError as e:
    print(f"✗ C++/C 模块导入失败: {e}")
    print("请先安装: cd cpp_src/python_bindings && pip install -e .")
    sys.exit(1)


def test_cpp_binding():
    """测试 C++ 绑定功能"""
    print("\n" + "="*60)
    print("测试 C++ Python 绑定")
    print("="*60)

    # 加载数据
    print("\n1. 加载测试数据...")
    data_dir = Path(__file__).parent.parent / "data" / "default"
    all_data = pd.read_csv(data_dir / "all_data.csv")
    Point_3D = np.load(data_dir / "Point_3D.npy")
    print(f"   轨迹数据: {len(all_data)} 行")
    print(f"   3D 点数据: {Point_3D.shape}")

    # 测试参数
    instrument_length = 1.0
    instrument_radius = 0.025
    begin_deep = 3300
    end_deep = 3350  # 使用较小范围进行快速测试
    num_step = 0.5

    print(f"\n2. 测试参数:")
    print(f"   工具长度: {instrument_length} m")
    print(f"   工具半径: {instrument_radius} m")
    print(f"   深度范围: {begin_deep} - {end_deep} m")
    print(f"   步长: {num_step} m")

    # 测试 C++ 实现
    print(f"\n3. 运行 C++ 实现...")
    start_time = time.time()
    try:
        deep_cpp, R_cpp, rr_cpp, dd_cpp, p_all_cpp, t_all_cpp, draw_R_cpp = Projection2_cpp(
            all_data, Point_3D,
            instrument_length, instrument_radius,
            begin_deep, end_deep, num_step
        )
        cpp_time = time.time() - start_time
        print(f"   ✓ C++ 计算完成")
        print(f"   卡点深度: {deep_cpp:.3f} m")
        print(f"   最小半径: {R_cpp:.6f} m")
        print(f"   最大通过直径: {R_cpp * 2 * 1000:.3f} mm")
        print(f"   计算耗时: {cpp_time:.3f} 秒")
    except Exception as e:
        print(f"   ✗ C++ 计算失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print(f"\n4. 运行 C 实现...")
    start_time = time.time()
    try:
        deep_c, R_c, rr_c, dd_c, p_all_c, t_all_c, draw_R_c = Projection2_c(
            all_data, Point_3D,
            instrument_length, instrument_radius,
            begin_deep, end_deep, num_step
        )
        c_time = time.time() - start_time
        print(f"   ✓ C 计算完成")
        print(f"   卡点深度: {deep_c:.3f} m")
        print(f"   最小半径: {R_c:.6f} m")
        print(f"   最大通过直径: {R_c * 2 * 1000:.3f} mm")
        print(f"   计算耗时: {c_time:.3f} 秒")
    except Exception as e:
        print(f"   ✗ C 计算失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 测试 Python 实现（可选，用于对比）
    print(f"\n5. 运行 Python 实现（对比）...")
    start_time = time.time()
    try:
        deep_py, R_py, rr_py, dd_py, p_all_py, t_all_py, draw_R_py = Projection2(
            all_data, Point_3D,
            instrument_length, instrument_radius,
            begin_deep, end_deep, num_step,
            if_draw=False
        )
        py_time = time.time() - start_time
        print(f"   ✓ Python 计算完成")
        print(f"   卡点深度: {deep_py:.3f} m")
        print(f"   最小半径: {R_py:.6f} m")
        print(f"   最大通过直径: {R_py * 2 * 1000:.3f} mm")
        print(f"   计算耗时: {py_time:.3f} 秒")
    except Exception as e:
        print(f"   ✗ Python 计算失败: {e}")
        py_time = None
        deep_py = None
        R_py = None

    # 对比结果
    print(f"\n6. 结果对比:")
    depth_diff_cpp_c = abs(deep_cpp - deep_c)
    radius_diff_cpp_c = abs(R_cpp - R_c)
    print(f"   C++ vs C 深度差异: {depth_diff_cpp_c:.6f} m")
    print(f"   C++ vs C 半径差异: {radius_diff_cpp_c:.6f} m")

    if deep_py is not None and R_py is not None:
        depth_diff = abs(deep_cpp - deep_py)
        radius_diff = abs(R_cpp - R_py)

        print(f"   C++ vs Python 深度差异: {depth_diff:.6f} m")
        print(f"   C++ vs Python 半径差异: {radius_diff:.6f} m")

        if depth_diff < 1e-3 and radius_diff < 1e-6 and depth_diff_cpp_c < 1e-3 and radius_diff_cpp_c < 1e-6:
            print(f"   ✓ 结果一致（精度满足要求）")
        else:
            print(f"   ⚠ 结果存在差异")

        if py_time:
            speedup_cpp = py_time / cpp_time
            speedup_c = py_time / c_time
            print(f"\n7. 性能对比:")
            print(f"   Python 耗时: {py_time:.3f} 秒")
            print(f"   C++ 耗时: {cpp_time:.3f} 秒")
            print(f"   C 耗时: {c_time:.3f} 秒")
            print(f"   C++ 加速比: {speedup_cpp:.1f}x")
            print(f"   C 加速比: {speedup_c:.1f}x")
    else:
        print(f"   无法对比（Python 版本未成功运行）")

    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

    return True


def test_simple_call():
    """简单调用测试"""
    print("\n" + "="*60)
    print("简单调用测试")
    print("="*60)

    data_dir = Path(__file__).parent.parent / "data" / "default"
    all_data = pd.read_csv(data_dir / "all_data.csv")
    Point_3D = np.load(data_dir / "Point_3D.npy")

    print("\n调用 Projection2_cpp...")
    try:
        result = Projection2_cpp(
            all_data, Point_3D,
            1.0, 0.025,
            3300, 3310, 0.5
        )
        result_c = Projection2_c(
            all_data, Point_3D,
            1.0, 0.025,
            3300, 3310, 0.5
        )
        print(f"✓ 调用成功")
        print(f"  C++ 返回值类型: {type(result)}")
        print(f"  C++ 返回值长度: {len(result)}")
        print(f"  C++ 深度: {result[0]}")
        print(f"  C++ 半径: {result[1]}")
        print(f"  C 深度: {result_c[0]}")
        print(f"  C 半径: {result_c[1]}")
        return True
    except Exception as e:
        print(f"✗ 调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 先做简单测试
    if not test_simple_call():
        print("\n简单测试失败，退出")
        sys.exit(1)

    # 再做完整测试
    if not test_cpp_binding():
        print("\n完整测试失败")
        sys.exit(1)

    print("\n所有测试通过！")
