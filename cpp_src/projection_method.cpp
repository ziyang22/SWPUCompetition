#include "projection_method.h"
#include <cmath>
#include <algorithm>
#include <map>
#include <limits>
#include <chrono>
#include <iostream>
#include <fstream>
#include <sstream>
#include <iomanip>

namespace projection {

ProjectionCalculator::ProjectionCalculator(
    const std::vector<TrajectoryPoint>& trajectory,
    const std::vector<std::vector<Point3D>>& point_3d,
    double instrument_length,
    double instrument_radius,
    double num_step
) : trajectory_(trajectory),
    point_3d_(point_3d),
    instrument_length_(instrument_length),
    instrument_radius_(instrument_radius),
    num_step_(num_step)
{
    // Calculate step size based on trajectory spacing
    double depth_spacing = trajectory_[1].depth - trajectory_[0].depth;
    step_ = static_cast<int>(num_step * 1000.0 / (depth_spacing * 1000.0));
    h_step_ = step_;

    if (instrument_length_ < num_step_) {
        throw std::runtime_error("步进距离不能大于工具长度");
    }
}

std::optional<Point3D> ProjectionCalculator::linePlane(
    double a, double b, double c,
    double A, double B, double C, double D,
    const Point3D& p
) const {
    double t_numerator = -(A * p.x + B * p.y + C * p.z + D);
    double t_denominator = a * A + b * B + c * C;

    if (std::abs(t_denominator) < 1e-10) {
        return std::nullopt;
    }

    double t = t_numerator / t_denominator;

    return Point3D(
        p.x + a * t,
        p.y + b * t,
        p.z + c * t
    );
}

std::vector<Point3D> ProjectionCalculator::linePlaneMultiple(
    double a, double b, double c,
    double A, double B, double C, double D,
    const std::vector<std::vector<Point3D>>& points
) const {
    std::vector<Point3D> result;
    result.reserve(points.size() * points[0].size());

    for (const auto& layer : points) {
        for (const auto& point : layer) {
            auto projected = linePlane(a, b, c, A, B, C, D, point);
            if (projected) {
                result.push_back(*projected);
            }
        }
    }

    return result;
}

void ProjectionCalculator::projectionDirection(
    double n0, double n1, double n2,
    double delta,
    std::vector<double>& X,
    std::vector<double>& Y,
    std::vector<double>& Z
) const {
    X.clear();
    Y.clear();
    Z.clear();

    if (delta < 1e-10) {
        X.push_back(n0);
        Y.push_back(n1);
        Z.push_back(n2);
        return;
    }

    if (n0 * n0 + n1 * n1 > 1e-10) {
        double zmax = std::sqrt(1 - n2 * n2) * std::tan(delta);
        double z = -zmax;
        double z_step = 2 * zmax / 12.0;

        while (z < zmax) {
            if (std::abs(n1) > 1e-10) {
                double sqrt_term = std::sqrt(zmax * zmax - z * z);
                double denom = n0 * n0 + n1 * n1;

                double x1 = (-n0 * n2 * z + sqrt_term * n1) / denom;
                double x2 = (-n0 * n2 * z - sqrt_term * n1) / denom;
                double y1 = (n0 * x1 + n2 * z) / n1;
                double y2 = (n0 * x2 + n2 * z) / n1;

                Z.push_back(z + n2);
                Z.push_back(z + n2);
                X.push_back(x1 + n0);
                X.push_back(x2 + n0);
                Y.push_back(y1 + n1);
                Y.push_back(y2 + n1);
            } else if (std::abs(n0) > 1e-10 && std::abs(n1) < 1e-10) {
                double x = -n2 * z / n0;
                double y1 = std::sqrt(std::tan(delta) * std::tan(delta) - (z / n0) * (z / n0));
                double y2 = -y1;

                Z.push_back(z + n2);
                Z.push_back(z + n2);
                X.push_back(x + n0);
                X.push_back(x + n0);
                Y.push_back(y1 + n1);
                Y.push_back(y2 + n1);
            }
            z += z_step;
        }
    } else {
        // TODO: circular traversal case
        std::cout << "True" << std::endl;
        double x = std::tan(delta) + n0;
        double y = std::tan(delta) + n1;
        double z = n2;

        Z.push_back(z);
        X.push_back(x);
        Y.push_back(y);
    }
}

std::vector<Point2D> ProjectionCalculator::point3DTo2D(
    double A, double B, double C,
    const std::vector<Point3D>& points,
    const Point3D& origin,
    const Point3D& reference
) const {
    Point3D n(A, B, C);

    Point3D line1 = reference - origin;
    Point3D line2 = line1.cross(n);

    double norm1 = line1.norm();
    double norm2 = line2.norm();

    if (norm1 > 1e-10) line1 = line1 / norm1;
    if (norm2 > 1e-10) line2 = line2 / norm2;

    std::vector<Point2D> result;
    result.reserve(points.size());

    for (const auto& p : points) {
        Point3D point_o = p - origin;
        double x = point_o.dot(line1);
        double y = point_o.dot(line2);
        result.emplace_back(x, y);
    }

    return result;
}

std::vector<Point2D> ProjectionCalculator::getClosestPoints(
    const std::vector<Point2D>& points
) const {
    if (points.empty()) return {};

    // Calculate slopes
    std::map<int, std::vector<Point2D>> slope_groups;

    for (const auto& p : points) {
        double slope = std::atan2(p.x, p.y);
        int slope_key = static_cast<int>(std::round(slope * 10.0));
        slope_groups[slope_key].push_back(p);
    }

    // Find closest point for each slope group
    std::vector<Point2D> closest_points;
    for (const auto& [slope, group] : slope_groups) {
        double min_dist = std::numeric_limits<double>::max();
        Point2D closest;

        for (const auto& p : group) {
            double dist = p.norm();
            if (dist < min_dist) {
                min_dist = dist;
                closest = p;
            }
        }
        closest_points.push_back(closest);
    }

    return closest_points;
}

Circle ProjectionCalculator::maxInscribedCircle(
    const std::vector<Point2D>& points,
    int grid_num
) const {
    if (points.empty()) return Circle();

    // Calculate bounds
    double xmin = std::numeric_limits<double>::max();
    double xmax = std::numeric_limits<double>::lowest();
    double ymin = std::numeric_limits<double>::max();
    double ymax = std::numeric_limits<double>::lowest();

    for (const auto& p : points) {
        xmin = std::min(xmin, p.x);
        xmax = std::max(xmax, p.x);
        ymin = std::min(ymin, p.y);
        ymax = std::max(ymax, p.y);
    }

    xmin *= 0.3;
    xmax *= 0.3;
    ymin *= 0.3;
    ymax *= 0.3;

    double x_step = (xmax - xmin) / grid_num;
    double y_step = (ymax - ymin) / grid_num;

    Circle max_circle;
    double max_radius = 0.0;

    for (int i = 0; i < grid_num; ++i) {
        double x0 = xmin + i * x_step;
        for (int j = 0; j < grid_num; ++j) {
            double y0 = ymin + j * y_step;

            Point2D center(x0, y0);
            double min_dist = std::numeric_limits<double>::max();

            for (const auto& p : points) {
                double dist = (p - center).norm();
                min_dist = std::min(min_dist, dist);
            }

            if (min_dist > max_radius) {
                max_radius = min_dist;
                max_circle = Circle(x0, y0, min_dist);
            }
        }
    }

    max_circle.radius *= 0.98;
    return max_circle;
}

int ProjectionCalculator::findDepthIndex(double depth) const {
    for (size_t i = 0; i < trajectory_.size(); ++i) {
        if (std::abs(trajectory_[i].depth - depth) < 1e-6) {
            return static_cast<int>(i);
        }
    }

    // Find closest
    double min_diff = std::numeric_limits<double>::max();
    int closest_idx = 0;

    for (size_t i = 0; i < trajectory_.size(); ++i) {
        double diff = std::abs(trajectory_[i].depth - depth);
        if (diff < min_diff) {
            min_diff = diff;
            closest_idx = static_cast<int>(i);
        }
    }

    return closest_idx;
}

bool ProjectionCalculator::calculate(
    double begin_deep,
    double end_deep,
    std::vector<CalculationResult>& results,
    double& stuck_depth,
    double& min_radius
) {
    if (begin_deep > end_deep) {
        throw std::runtime_error("error: 结束深度小于起始深度");
    }

    int begin = findDepthIndex(begin_deep);
    int end = findDepthIndex(end_deep) + 1;

    if (end > static_cast<int>(point_3d_.size())) {
        end = static_cast<int>(point_3d_.size());
    }

    results.clear();
    double t_all = 0.0;
    int i = begin;

    std::vector<CalculationResult> stuck_point_data;
    std::vector<CalculationResult> pass_point_data;

    while (i < end - 1) {
        auto start_time = std::chrono::high_resolution_clock::now();

        int j = i + h_step_;
        if (j >= static_cast<int>(point_3d_.size())) {
            j = static_cast<int>(point_3d_.size()) - 1;
        }

        Point3D Pi, Pj;
        if (i - step_ < 0) {
            Pi = trajectory_[begin].position;
        } else {
            Pi = trajectory_[i - step_].position;
        }
        Pj = trajectory_[j].position;

        Point3D diff = Pj - Pi;
        double d = diff.norm();
        Point3D n = diff / d;

        double delta = 0.030 / instrument_length_;
        double angle_step = delta / 8.0;

        std::vector<double> DX, DY, DZ;
        double angle = 0.0;
        while (angle < delta) {
            std::vector<double> X_dir, Y_dir, Z_dir;
            projectionDirection(n.x, n.y, n.z, angle, X_dir, Y_dir, Z_dir);
            DX.insert(DX.end(), X_dir.begin(), X_dir.end());
            DY.insert(DY.end(), Y_dir.begin(), Y_dir.end());
            DZ.insert(DZ.end(), Z_dir.begin(), Z_dir.end());
            angle += angle_step;
        }

        // Calculate plane parameters
        Point3D plane_normal = (trajectory_[j - 1].position - trajectory_[j].position).normalized();
        double A = plane_normal.x;
        double B = plane_normal.y;
        double C = plane_normal.z;
        double D = -(A * trajectory_[j].position.x + B * trajectory_[j].position.y + C * trajectory_[j].position.z);

        Circle min_circle;
        double max_r = 0.0;

        for (size_t m = 0; m < DX.size(); ++m) {
            // Get projection points
            std::vector<std::vector<Point3D>> window_points;
            int start_idx = std::max(0, j - step_);
            for (int k = start_idx; k < j; ++k) {
                if (k < static_cast<int>(point_3d_.size())) {
                    // point_3d_[k] is vector<Point3D> (24 points at depth k)
                    window_points.push_back(point_3d_[k]);
                }
            }

            auto P_projection = linePlaneMultiple(DX[m], DY[m], DZ[m], A, B, C, D, window_points);

            if (P_projection.empty()) continue;

            Point3D mean_proj(0, 0, 0);
            for (const auto& p : P_projection) {
                mean_proj = mean_proj + p;
            }
            mean_proj = mean_proj / static_cast<double>(P_projection.size());

            auto P_pro_2d = point3DTo2D(A, B, C, P_projection, mean_proj, P_projection[3]);
            auto S_P_projection_2d = getClosestPoints(P_pro_2d);

            Circle Rm = maxInscribedCircle(S_P_projection_2d, 30);

            if (Rm.radius > max_r) {
                max_r = Rm.radius;
                min_circle = Rm;
            }
        }

        auto end_time = std::chrono::high_resolution_clock::now();
        double elapsed = std::chrono::duration<double>(end_time - start_time).count();
        t_all += elapsed;

        CalculationResult current_result;
        current_result.depth = trajectory_[j].depth;
        current_result.tool_length = instrument_length_;
        current_result.center_x = min_circle.center_x;
        current_result.center_y = min_circle.center_y;
        current_result.diameter = min_circle.radius * 2.0;
        current_result.current_time = elapsed;
        current_result.total_time = t_all;

        std::cout << std::fixed << std::setprecision(3)
                  << "深度:" << trajectory_[j].depth << "/" << trajectory_[end - 1].depth
                  << ", 工具长度: " << std::setprecision(2) << instrument_length_ << "m\n"
                  << " 圆心:(" << std::setprecision(3) << min_circle.center_x << ","
                  << min_circle.center_y << "),直径：" << min_circle.radius * 2.0 << "\n"
                  << " 当前段计算时间:" << std::setprecision(2) << elapsed << "s, 当前总耗时:"
                  << t_all << "s\n" << std::endl;

        if (instrument_radius_ > min_circle.radius) {
            stuck_point_data.push_back(current_result);

            std::cout << "保存最后10个步长信息..." << std::endl;
            std::string stuck_file_name = "output/stuck_point_" + std::to_string(static_cast<int>(trajectory_[j].depth)) + "m.txt";
            std::ofstream stuck_file(stuck_file_name);
            stuck_file << "深度(m),工具长度(m) ,圆心X(m), 圆心Y(m),直径(m) ,当前段耗时(s),总耗时(s)\n";

            int p = static_cast<int>(5.0 / num_step_);
            int start_save = std::max(0, static_cast<int>(stuck_point_data.size()) - p);
            for (size_t idx = start_save; idx < stuck_point_data.size(); ++idx) {
                const auto& data = stuck_point_data[idx];
                stuck_file << std::fixed << std::setprecision(3) << data.depth << ","
                          << std::setprecision(6) << data.tool_length << ","
                          << data.center_x << "," << data.center_y << ","
                          << data.diameter << "," << data.current_time << ","
                          << data.total_time << "\n";
            }
            stuck_file.close();

            std::string final_result_file = "output/final_result_" + std::to_string(static_cast<int>(trajectory_[j].depth)) + "m.txt";
            std::ofstream final_file(final_result_file);
            final_file << "工具长度(m), 工具半径(m), 卡点深度(m), 最大通过直径(m)\n";
            final_file << std::fixed << std::setprecision(3) << instrument_length_ << ","
                      << instrument_radius_ << "," << trajectory_[j].depth << ","
                      << std::setprecision(6) << min_circle.radius * 2.0 << "\n";
            final_file.close();

            std::cout << "无法通过，结果已保存到 " << stuck_file_name << " 和 " << final_result_file << std::endl;

            stuck_depth = trajectory_[j].depth;
            min_radius = min_circle.radius;
            results = stuck_point_data;
            return false;
        }

        stuck_point_data.push_back(current_result);
        pass_point_data.push_back(current_result);

        i = j;
    }

    std::cout << "已至底部, 总耗时:" << std::fixed << std::setprecision(2) << t_all << std::endl;
    std::cout << "保存最后10个步长信息..." << std::endl;

    std::string pass_file_name = "output/pass_last_5m_" + std::to_string(static_cast<int>(end_deep)) + "m.txt";
    std::ofstream pass_file(pass_file_name);
    pass_file << "深度(m),工具长度(m) ,圆心X(m), 圆心Y(m),直径(m) ,当前段耗时(s),总耗时(s)\n";

    int l = static_cast<int>(5.0 / num_step_);
    int start_save = std::max(0, static_cast<int>(pass_point_data.size()) - l);
    for (size_t idx = start_save; idx < pass_point_data.size(); ++idx) {
        const auto& data = pass_point_data[idx];
        pass_file << std::fixed << std::setprecision(3) << data.depth << ","
                  << std::setprecision(6) << data.tool_length << ","
                  << data.center_x << "," << data.center_y << ","
                  << data.diameter << "," << data.current_time << ","
                  << data.total_time << "\n";
    }
    pass_file.close();

    std::cout << "通过数据已保存到 " << pass_file_name << std::endl;

    results = pass_point_data;
    stuck_depth = 0.0;
    min_radius = 0.0;
    return true;
}

} // namespace projection
