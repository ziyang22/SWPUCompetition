#!/bin/bash
# 自适应搜索模式性能对比测试脚本

echo "=============="
echo "井眼通过能力计算 - 性能对比测试"
echo "===================="
echo ""

# 检查程序是否存在
if [ ! -f "./projection_method" ]; then
    echo "错误: 找不到 projection_method 程序"
    echo "请先运行: make USE_OPENMP=1"
    exit 1
fi

# 测试参数
LENGTH=1.0
RADIUS=0.025
BEGIN=${1:-3000}
END=${2:-4000}
STEP=0.5

echo "测试参数:"
echo "  工具长度: ${LENGTH} m"
echo "  工具半径: ${RADIUS} m"
echo "  起始深度: ${BEGIN} m"
echo "  截止深度: ${END} m"
echo "  步长: ${STEP} m"
echo ""

# 测试 1: 固定步长模式
echo "=============="
echo "测试 1: 固定步长模式"
echo "======================"
echo "开始计算..."
START_TIME=$(date +%s.%N)
FIXED_OUTPUT=$(./projection_method ${LENGTH} ${RADIUS} ${BEGIN} ${END} ${STEP} 0 2>&1)
END_TIME=$(date +%s.%N)
FIXED_TIME=$(echo "$END_TIME - $START_TIME" | bc)
FIXED_WINDOWS=$(echo "$FIXED_OUTPUT" | grep "窗口数:" | awk '{print $2}' | cut -d',' -f1)
FIXED_RESULT=$(echo "$FIXED_OUTPUT" | grep -E "(工具可以通过|工具无法通过)" | head -1)

echo "完成!"
echo "  窗口数: ${FIXED_WINDOWS}"
echo "  总耗时: ${FIXED_TIME} 秒"
echo "  结果: ${FIXED_RESULT}"
echo ""

# 测试 2: 自适应搜索模式
echo "==================="
echo "测试 2: 自适应搜索模式"
echo "========================="
echo "开始计算..."
START_TIME=$(date +%s.%N)
ADAPTIVE_OUTPUT=$(./projection_method ${LENGTH} ${RADIUS} ${BEGIN} ${END} ${STEP} 1 2.0 0.5 10.0 2>&1)
END_TIME=$(date +%s.%N)
ADAPTIVE_TIME=$(echo "$END_TIME - $START_TIME" | bc)

ADAPTIVE_WINDOWS=$(echo "$ADAPTIVE_OUTPUT" | grep "窗口数:" | awk '{print $2}' | cut -d',' -f1)
ADAPTIVE_RESULT=$(echo "$ADAPTIVE_OUTPUT" | grep -E "(工具可以通过|工具无法通过)" | head -1)

echo "完成!"
echo "  窗口数: ${ADAPTIVE_WINDOWS}"
echo "  总耗时: ${ADAPTIVE_TIME} 秒"
echo "  结果: ${ADAPTIVE_RESULT}"
echo ""

# 性能对比
echo "=========================="
echo "性能对比总结"
echo "===================="
echo ""
echo "深度范围: ${BEGIN}m - ${END}m ($(echo "$END - $BEGIN" | bc)m)"
echo ""
echo "固定步长模式:"
echo "  窗口数: ${FIXED_WINDOWS}"
echo "  耗时: ${FIXED_TIME}s"
echo ""
echo "自适应搜索模式:"
echo "  窗口数: ${ADAPTIVE_WINDOWS}"
echo "  耗时: ${ADAPTIVE_TIME}s"
echo ""

if [ -n "$FIXED_WINDOWS" ] && [ -n "$ADAPTIVE_WINDOWS" ] && [ "$ADAPTIVE_WINDOWS" -gt 0 ]; then
    SPEEDUP=$(echo "scale=2; $FIXED_TIME / $ADAPTIVE_TIME" | bc)
    WINDOW_REDUCTION=$(echo "scale=1; 100 * (1 - $ADAPTIVE_WINDOWS / $FIXED_WINDOWS)" | bc)

    echo "性能提升:"
    echo "  速度提升: ${SPEEDUP}x"
    echo "  窗口减少: ${WINDOW_REDUCTION}%"
    echo ""
fi

echo "================"
echo "测试完成!"
echo "================"
