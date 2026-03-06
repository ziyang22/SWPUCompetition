import timeit
import matplotlib
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

def line_plane(a, b, c, A, B, C, D, p):
    """
    直线与平面的交点
    a, b, c: 直线的方向的三个分量
    A, B, C： 平面的法向量
    D: 平面的位移
    p： 直线的位移（直线上一点）
    :return: xp, yp, zp 交点坐标分量
    """
    # 获得上平面中心到下平面根据投影方向的点

    if len(p.shape) == 1:

        t_numerator = -(A * p[0] + B * p[1] + C * p[2] + D)
        t_denominator = a * A + b * B + c * C

        if np.any(t_denominator == 0):
            return None

        t = t_numerator / t_denominator

        xp = p[0] + a * t
        yp = p[1] + b * t
        zp = p[2] + c * t

        return np.array([xp, yp, zp])

    if len(p.shape) == 3:
        t_numerator = -(A * p[:, :, 0] + B * p[:, :, 1] + C * p[:, :, 2] + D)
        t_denominator = a * A + b * B + c * C

        if np.any(t_denominator == 0):
            return None

        t = t_numerator / t_denominator

        xp = p[:, :, 0] + a * t
        yp = p[:, :, 1] + b * t
        zp = p[:, :, 2] + c * t

        return np.array([xp, yp, zp]).transpose((1, 2, 0)).reshape(p.shape[0] * p.shape[1], 3)


def projection_direction(n0, n1, n2, delta):
    """
    n0, n1, n2: double 轴线的方向
    delta: double 与轴的夹角
    :return: X, Y, Z list 所有可能投影方向的三个分量
    """

    X = []
    Y = []
    Z = []

    if delta == 0:
        return [[n0], [n1], [n2]]

    if n0 ** 2 + n1 ** 2 != 0:
        zmax = np.sqrt(1 - n2 ** 2) * np.tan(delta)
        z = -zmax
        z_step = 2 * zmax / 12
        while z < zmax:
            if n1 != 0:
                x1 = (-n0 * n2 * z + np.sqrt(zmax ** 2 - z ** 2) * n1) / (n0 ** 2 + n1 ** 2)
                x2 = (-n0 * n2 * z - np.sqrt(zmax ** 2 - z ** 2) * n1) / (n0 ** 2 + n1 ** 2)
                y1 = (n0 * x1 + n2 * z) / n1
                y2 = (n0 * x2 + n2 * z) / n1

                Z.extend([z + n2, z + n2])
                X.extend([x1 + n0, x2 + n0])
                Y.extend([y1 + n1, y2 + n1])

            elif n0 != 0 and n1 == 0:
                x = -n2 * z / n0
                y1 = np.sqrt(np.tan(delta) ** 2 - (z / n0) ** 2)
                y2 = -y1

                Z.extend([z + n2, z + n2])
                X.extend([x + n0, x + n0])
                Y.extend([y1 + n1, y2 + n1])
            # 迭代
            z += z_step
    else:
        # TODO 圆周 的遍历
        print("True")
        x = np.cos() * np.tan(delta) + n0
        y = np.cos() * np.tan(delta) + n1
        z = n2

        Z.append(z)
        X.append(x)
        Y.append(y)

    return [X, Y, Z]


def point_3d_to_2d(A, B, C, P, O, o):
    # Calculate the normal vector of the reference frame
    n = np.array([A, B, C])

    # Calculate the projection axes
    line1 = np.array(o) - np.array(O)
    line2 = np.cross(line1, n)

    # Normalize the projection axes
    norm1 = np.linalg.norm(line1)
    norm2 = np.linalg.norm(line2)
    line1 /= norm1
    line2 /= norm2

    # Project the point onto the axes and calculate the 2D coordinates
    Point_O = np.array(P) - np.array(O)
    X = np.dot(Point_O, line1)
    Y = np.dot(Point_O, line2)

    return np.array([X, Y]).T


def get_closest_points(points):
    # Calculate slopes of lines connecting points to centroid
    slopes = np.around(np.arctan2(points[:, 0], points[:, 1]), 1)

    # Group points by slope
    unique_slopes = np.unique(slopes)
    slope_groups = {slope: points[slopes == slope] for slope in unique_slopes}

    # Find the closest point for each slope group
    closest_points = []
    for slope, group_points in slope_groups.items():
        closest_point = group_points[np.argmin(np.linalg.norm(group_points, axis=1))]
        closest_points.append(closest_point)

    return np.array(closest_points)

def max_incircle(points, grid_num):
    # 计算点集所代表的区域范围
    xmin, ymin = np.min(points, axis=0) * 0.3
    xmax, ymax = np.max(points, axis=0) * 0.3
    # 计算网格数
    x_step = (xmax - xmin) / grid_num
    y_step = (ymax - ymin) / grid_num
    # 初始化最大内切圆
    max_circle = None
    max_radius = 0
    # 遍历所有网格
    for i in range(grid_num):
        x0 = xmin + i * x_step
        for j in range(grid_num):
            # 计算网格边界
            y0 = ymin + j * y_step
            # 计算网格内的最大圆
            # 计算圆心和半径
            center = np.array([x0, y0])
            radius = np.min(np.sqrt(np.sum((points - center) ** 2, axis=1)))
            # 更新最大内切圆
            if radius > max_radius:
                max_circle = center, radius
                max_radius = radius
    return np.array([max_circle[0][0], max_circle[0][1], max_circle[1] * 0.98])

def Projection2(all_data, Point_3D, Instrument_length=1, Instrument_Radius=0.01, begin_deep=None, end_deep=None,
                num_step=1, if_draw=False):
    """
    投影法计算通过能力
    :param num_step:
    :param all_data: data_pre_concat 输出的多臂与井眼轨迹拼接的整体数据 DataFrame
    :param Point_3D: 井壁的三维坐标 array (deep, par_deep_num_deep, 3)
    :param Instrument_length: 仪器长度 double
    :param Instrument_Radius: 仪器半径 double
    :param begin_deep: 起始深度 double
    :param end_deep: 结束深度 double
    :return:    最小半径位于的井深,
                最大可通过半径（最小半径），
            R_all 每个窗口额最大通过半径，
            dir_all 通过方向，
            P_all 窗口的上下平面的重心，
            t_all 运行总时间。
    """
    if begin_deep is not None and end_deep is not None:
        if begin_deep > end_deep:
            print("error: 结束深度小于起始深度")
            raise Exception("截止深度小于起始深度!")
    # 可能的数据切片
    if begin_deep is None:
        begin = 0
    else:
        begin = all_data[all_data["DEPTH"].isin([begin_deep])]
        if len(begin) == 0:
            begin = (all_data["DEPTH"] - begin_deep).abs().idxmin()
        else:
            begin = begin.index[0]

    if end_deep is None:
        # 读取井眼曲线数据
        end = len(Point_3D) + 1
    else:
        end = all_data[all_data["DEPTH"].isin([end_deep])]
        if len(end) == 0:
            end = (all_data["DEPTH"] - end_deep).abs().idxmin() + 1
        else:
            end = end.index[0] + 1

    traj = np.array(all_data[["DEPTH", "N", "E", "H"]])
    point = Point_3D
    h = Instrument_length  # 仪器长度 单位 m
    r = Instrument_Radius

    step = int(num_step * 1000 / ((traj[1, 0] - traj[0, 0]) * 1000))

    if h < num_step:
        raise Exception("步进距离不能大于工具长度")

    h_step = int(num_step * 1000 / ((traj[1, 0] - traj[0, 0]) * 1000))
    # if h_step < 1:
    #     h_step = 1

    P_all = []
    R_all = []
    dir_all = []
    t_all = 0

    id = 0
    i = begin
    draw_R = []
    if if_draw:
        matplotlib.use('Agg')  # Set the backend to Agg
        di = 0
        fig, axs = plt.subplots(nrows=3, ncols=3, figsize=(13, 13))

    stuck_point_data = []  # 用于保存卡点附近的数据
    pass_point_data = []  # 用于保存通过时的最后数据

    while i < end - 1:
        a = timeit.default_timer()
        j = i + h_step

        if id == 1:
            return traj[np.argmin(np.array(R_all)[:, 2]) * h_step, 0], np.min(
                np.array(R_all)[:, 2]), R_all, dir_all, P_all, t_all, draw_R

        if j > (len(point)):  # 触底退出
            j = len(point) - 1
            id = id + 1

        if i - step < 0:
            # print("True1")
            Pi = traj[begin, 1:]  # 刚入井时 为进口轴心
        else:
            # print("True2")
            Pi = traj[i - step, 1:]  # 初始上平面的圆心 工具尾部中心
        Pj = traj[j, 1:]  # 当前深度点平面的圆心
        P_all.append(Pi)

        d = np.linalg.norm(Pj - Pi)
        n0, n1, n2 = np.array(Pj - Pi) / d  # 主投影方向

        delta = 0.030 / Instrument_length
        angle_step = delta / 8

        # 获得所有可能投影方向
        angle = 0.0
        DX = []
        DY = []
        DZ = []
        while angle < delta:
            X_dir, Y_dir, Z_dir = projection_direction(n0, n1, n2, angle)
            DX.extend(X_dir)
            DY.extend(Y_dir)
            DZ.extend(Z_dir)
            angle += angle_step

        # 获得上平面各个点点根据投影方向在下面的投影
        # 下平面公式的参数
        A, B, C = (traj[j - 1, 1:] - traj[j, 1:]) / np.linalg.norm((traj[j - 1, 1:] - traj[j, 1:]))
        D = - A * traj[j, 1] - B * traj[j, 2] - C * traj[j, 3]
        min_R = np.array([0, 0, 0])
        min_dir = np.array([0, 0, 0])

        for m in range(len(DX)):
            # 各层投影
            if (j - step) < 0:
                P_projection = line_plane(DX[m], DY[m], DZ[m], A, B, C, D, point[0:j, :, :])
            else:
                P_projection = line_plane(DX[m], DY[m], DZ[m], A, B, C, D, point[j - step:j, :, :])

            # 投影后内边界点获取
            P_pro_2d = point_3d_to_2d(A, B, C, P_projection, np.mean(P_projection, axis=0), P_projection[3, :])
            PPj = point_3d_to_2d(A, B, C, traj[j, 1:], np.mean(P_projection, axis=0), P_projection[3, :])
            # P_pro_2d = point_3d_to_2d(A, B, C, P_projection, traj[j, 1:], P_projection[3, :])
            # PPj = traj[j, 1:]
            S_P_projection_2d = get_closest_points(P_pro_2d)

            Rm = max_incircle(S_P_projection_2d, 30)

            if min_R[2] < Rm[2]:
                min_R = Rm
                min_dir = DX[m], DY[m], DZ[m]
                pp = np.mean(P_projection, axis=0)
                pp_L = P_pro_2d
                pp_S = S_P_projection_2d
                ppj = PPj
                ml = m
        # print(ml)
        R_all.append(min_R)
        dir_all.append(min_dir)
        # print(traj[j - h_step, 0], '\n', np.array(min_R), np.array(min_R).shape)
        draw_R.append(np.insert(min_R, 0, traj[j - h_step, :]))
        draw_R.append(np.insert(min_R, 0, traj[j, :]))

        if if_draw:
            if di <= 8:
                mm = di // 3
                nn = di % 3
                axs[mm, nn].scatter(pp_L[:, 0], pp_L[:, 1], label='projection_point')
                axs[mm, nn].scatter(pp_S[:, 0], pp_S[:, 1], label='inner_point')
                axs[mm, nn].scatter(ppj[0], ppj[1], label='deep_j_center_point')
                c = plt.Circle((min_R[0], min_R[1]), min_R[2], color='y', fill=False, label="max_in_cirecle")
                axs[mm, nn].add_artist(c)
                axs[mm, nn].set_title('Well-Deep:' + str(traj[j, 0] - Instrument_length) + '-' + str(traj[j, 0]))
                # # 添加图例
                # axs.legend()
                # 显示图表
                di = di + 1
            if di > 8:
                plt.savefig(f"figure_{traj[j, 0]}m_{Instrument_length}m.png")
                plt.close(fig)  # Close the figure to free memory
                di = 0
                fig, axs = plt.subplots(nrows=3, ncols=3, figsize=(13, 13))



        b = timeit.default_timer()
        i = j
        t_all += b - a
        print("深度:%.3f/%.3f, 工具长度: %.2fm\n 圆心:(%.3f,%.3f),直径：%.3f\n 当前段计算时间:%.2fs, 当前总耗时:%.2fs\n"
              % (traj[j, 0], traj[end - 1, 0], Instrument_length, min_R[0], min_R[1], min_R[2] * 2, b - a, t_all))

        # 在计算完每个窗口后，保存结果
        current_result = {
            "depth": traj[j, 0],
            "tool_len":Instrument_length,
            "center_x": min_R[0],
            "center_y": min_R[1],
            "diameter":min_R[2] * 2,
            "now-time": b - a,
            "all-time": t_all
        }

        if r > min_R[2]:
            # 保存当前卡点数据
            stuck_point_data.append(current_result)

            # 保存前五米数据
            print("保存最后10个步长信息...")
            stuck_file_name = f"stuck_point_{traj[j, 0]}m.txt"
            with open(stuck_file_name, 'w',encoding='utf-8') as f:
                f.write("深度(m),工具长度(m) ,圆心X(m), 圆心Y(m),直径(m) ,当前段耗时(s),总耗时(s)\n")
                p = int(5 / num_step)
                for data in stuck_point_data[-p:]:  # 保存最后10个点（约前五米）
                    f.write(
                        f"{data['depth']:.3f},{data['tool_len']:.6f},{data['center_x']:.6f},{data['center_y']:.6f},{data['diameter']:.6f},{data['now-time']:.6f},{data['all-time']:.6f}\n")

            # 保存最后结果
            final_result_file = f"final_result_{traj[j, 0]}m.txt"
            with open(final_result_file, 'w', encoding='utf-8') as f:
                f.write("工具长度(m), 工具半径(m), 卡点深度(m), 最大通过直径(m)\n")
                f.write(f"{Instrument_length:.3f},{Instrument_Radius:.3f},{traj[j, 0]:.3f},{min_R[2] * 2:.6f}\n")

            print(f"无法通过，结果已保存到 {stuck_file_name} 和 {final_result_file}")
            return traj[np.argmin(np.array(R_all)[:, 2]) * h_step + begin + 1, 0], np.min(
                np.array(R_all)[:, 2]), R_all, dir_all, P_all, t_all, draw_R

        # 保存当前结果
        stuck_point_data.append(current_result)
        pass_point_data.append(current_result)

    # 如果能通过，保存最后五米数据
    print("已至底部, 总耗时:%.2f" % t_all)
    print("保存最后10个步长信息...")
    pass_file_name = f"pass_last_5m_{end_deep}m.txt"
    with open(pass_file_name, 'w', encoding='utf-8') as f:
        l=int(5/num_step)
        f.write("深度(m),工具长度(m) ,圆心X(m), 圆心Y(m),直径(m) ,当前段耗时(s),总耗时(s)\n")
        for data in pass_point_data[-l:]:  # 保存最后10个点（约最后五米）
            f.write(
                f"{data['depth']:.3f},{data['tool_len']:.6f},{data['center_x']:.6f},{data['center_y']:.6f},{data['diameter']:.6f},{data['now-time']:.6f},{data['all-time']:.6f}\n")

    print(f"通过数据已保存到 {pass_file_name}")
    return traj[np.argmin(np.array(R_all)[:, 2]) * h_step + begin, 0], np.min(
        np.array(R_all)[:, 2]), R_all, dir_all, P_all, t_all, draw_R


if __name__ == '__main__':
    all_data = pd.read_csv('all_data.csv')
    Point_3D = np.load('Point_3D.npy')
    instrument_length=1  #工具长度
    instrument_Radius=0.025  #工具半径
    begin_deep=3300   #起始深度
    end_deep=3400     #截至深度
    num_step=0.5      #步长
    deep, R, rr, dd, p_all, t_all, draw_R =Projection2(all_data, Point_3D, instrument_length,instrument_Radius, begin_deep, end_deep,num_step)
    print("工具长度:%.3fm 最大通过直径:%.3fmm 卡口深度:%.3fm\n"
          % (instrument_length, R * 2 * 1000, deep))