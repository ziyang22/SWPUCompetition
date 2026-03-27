#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include "../projection_method.h"
#include <fstream>
#include <iomanip>
#include <limits>

namespace py = pybind11;
using namespace projection;

// Helper function to convert pandas DataFrame to trajectory vector
std::vector<TrajectoryPoint> dataframe_to_trajectory(py::object df) {
    // Get DEPTH, N, E, H columns from DataFrame
    py::array_t<double> depth = df.attr("__getitem__")("DEPTH").attr("values").cast<py::array_t<double>>();
    py::array_t<double> n = df.attr("__getitem__")("N").attr("values").cast<py::array_t<double>>();
    py::array_t<double> e = df.attr("__getitem__")("E").attr("values").cast<py::array_t<double>>();
    py::array_t<double> h = df.attr("__getitem__")("H").attr("values").cast<py::array_t<double>>();

    auto depth_buf = depth.request();
    auto n_buf = n.request();
    auto e_buf = e.request();
    auto h_buf = h.request();

    double* depth_ptr = static_cast<double*>(depth_buf.ptr);
    double* n_ptr = static_cast<double*>(n_buf.ptr);
    double* e_ptr = static_cast<double*>(e_buf.ptr);
    double* h_ptr = static_cast<double*>(h_buf.ptr);

    size_t size = depth_buf.shape[0];
    std::vector<TrajectoryPoint> trajectory;
    trajectory.reserve(size);

    for (size_t i = 0; i < size; ++i) {
        TrajectoryPoint pt;
        pt.depth = depth_ptr[i];
        pt.position.x = n_ptr[i];
        pt.position.y = e_ptr[i];
        pt.position.z = h_ptr[i];
        trajectory.push_back(pt);
    }

    return trajectory;
}

// Helper function to convert numpy array to Point3D vector
std::vector<std::vector<Point3D>> numpy_to_point3d(py::array_t<double> arr) {
    auto buf = arr.request();

    if (buf.ndim != 3) {
        throw std::runtime_error("Point_3D array must be 3-dimensional");
    }

    size_t depth_size = buf.shape[0];
    size_t points_per_depth = buf.shape[1];
    size_t coords = buf.shape[2];

    if (coords != 3) {
        throw std::runtime_error("Last dimension must be 3 (x, y, z)");
    }

    double* ptr = static_cast<double*>(buf.ptr);
    std::vector<std::vector<Point3D>> result;
    result.reserve(depth_size);

    for (size_t i = 0; i < depth_size; ++i) {
        std::vector<Point3D> layer;
        layer.reserve(points_per_depth);

        for (size_t j = 0; j < points_per_depth; ++j) {
            size_t idx = (i * points_per_depth + j) * 3;
            Point3D pt(ptr[idx], ptr[idx + 1], ptr[idx + 2]);
            layer.push_back(pt);
        }
        result.push_back(layer);
    }

    return result;
}

std::vector<projection_c_trajectory_point> dataframe_to_trajectory_c(py::object df) {
    auto trajectory = dataframe_to_trajectory(df);
    std::vector<projection_c_trajectory_point> trajectory_c;
    trajectory_c.reserve(trajectory.size());
    for (const auto& pt : trajectory) {
        trajectory_c.push_back(projection_c_trajectory_point{
            pt.depth,
            pt.position.x,
            pt.position.y,
            pt.position.z
        });
    }
    return trajectory_c;
}

std::vector<projection_c_point3d> numpy_to_point3d_c(py::array_t<double> arr, size_t& depth_size, size_t& points_per_depth) {
    auto buf = arr.request();

    if (buf.ndim != 3) {
        throw std::runtime_error("Point_3D array must be 3-dimensional");
    }

    depth_size = buf.shape[0];
    points_per_depth = buf.shape[1];
    size_t coords = buf.shape[2];

    if (coords != 3) {
        throw std::runtime_error("Last dimension must be 3 (x, y, z)");
    }

    double* ptr = static_cast<double*>(buf.ptr);
    std::vector<projection_c_point3d> result;
    result.reserve(depth_size * points_per_depth);

    for (size_t i = 0; i < depth_size; ++i) {
        for (size_t j = 0; j < points_per_depth; ++j) {
            size_t idx = (i * points_per_depth + j) * 3;
            result.push_back(projection_c_point3d{ptr[idx], ptr[idx + 1], ptr[idx + 2]});
        }
    }

    return result;
}

static void save_final_result_file(double instrument_length, double instrument_radius, double stuck_depth, double min_radius) {
    std::string final_filename = "output/final_result_" + std::to_string(static_cast<int>(stuck_depth)) + "m.txt";
    std::ofstream final_file(final_filename);
    final_file << "工具长度(m), 工具半径(m), 卡点深度(m), 最大通过直径(m)\n";
    final_file << std::fixed << std::setprecision(3) << instrument_length << ","
               << std::setprecision(3) << instrument_radius << ","
               << std::setprecision(3) << stuck_depth << ","
               << std::setprecision(6) << min_radius * 2 << "\n";
}

static int find_depth_index_cpp(const std::vector<TrajectoryPoint>& trajectory, double depth) {
    for (size_t i = 0; i < trajectory.size(); ++i) {
        if (std::abs(trajectory[i].depth - depth) < 1e-6) {
            return static_cast<int>(i);
        }
    }

    double min_diff = std::numeric_limits<double>::max();
    int closest_idx = 0;
    for (size_t i = 0; i < trajectory.size(); ++i) {
        double diff = std::abs(trajectory[i].depth - depth);
        if (diff < min_diff) {
            min_diff = diff;
            closest_idx = static_cast<int>(i);
        }
    }
    return closest_idx;
}

static double compute_python_style_deep(
    const std::vector<TrajectoryPoint>& trajectory,
    const std::vector<CalculationResult>& results,
    double begin_depth,
    double num_step,
    bool passed,
    double fallback_depth
) {
    if (results.empty() || trajectory.size() < 2) {
        return fallback_depth;
    }

    int begin = find_depth_index_cpp(trajectory, begin_depth);
    double depth_spacing = trajectory[1].depth - trajectory[0].depth;
    int h_step = static_cast<int>(num_step * 1000.0 / (depth_spacing * 1000.0));
    if (h_step < 1) {
        h_step = 1;
    }

    size_t min_idx = 0;
    double min_r = std::numeric_limits<double>::max();
    for (size_t i = 0; i < results.size(); ++i) {
        double r = results[i].diameter / 2.0;
        if (r < min_r) {
            min_r = r;
            min_idx = i;
        }
    }

    int traj_idx = begin + static_cast<int>(min_idx) * h_step + (passed ? 0 : 1);
    if (traj_idx < 0) {
        traj_idx = 0;
    }
    if (traj_idx >= static_cast<int>(trajectory.size())) {
        traj_idx = static_cast<int>(trajectory.size()) - 1;
    }
    return trajectory[traj_idx].depth;
}

static py::tuple pack_python_result(double deep, double R, const std::vector<CalculationResult>& results) {
    py::list rr;
    py::list dd;
    py::list p_all;
    py::list draw_R;
    double t_all = 0.0;
    if (!results.empty()) {
        t_all = results.back().total_time;
    }
    return py::make_tuple(deep, R, rr, dd, p_all, t_all, draw_R);
}

// Main Python interface function - compatible with original Projection2
py::tuple Projection2_cpp(
    py::object all_data,
    py::array_t<double> Point_3D,
    double Instrument_length = 1.0,
    double Instrument_Radius = 0.025,
    py::object begin_deep = py::none(),
    py::object end_deep = py::none(),
    double num_step = 0.5,
    bool if_draw = false,
    bool enable_two_stage_max_circle = false
) {
    (void)if_draw;
    std::vector<TrajectoryPoint> trajectory = dataframe_to_trajectory(all_data);
    std::vector<std::vector<Point3D>> point_3d = numpy_to_point3d(Point_3D);

    double begin_depth = begin_deep.is_none() ? trajectory[0].depth : begin_deep.cast<double>();
    double end_depth = end_deep.is_none() ? trajectory.back().depth : end_deep.cast<double>();

    ProjectionCalculator calculator(
        trajectory,
        point_3d,
        Instrument_length,
        Instrument_Radius,
        num_step
    );

    std::vector<CalculationResult> results;
    double stuck_depth = 0.0;
    double min_radius = 0.0;

    bool passed = calculator.calculate(
        begin_depth,
        end_depth,
        results,
        stuck_depth,
        min_radius,
        0,
        2.0,
        0.5,
        10.0,
        {},
        enable_two_stage_max_circle ? 1 : 0
    );

    double deep = compute_python_style_deep(trajectory, results, begin_depth, num_step, passed, stuck_depth);
    return pack_python_result(deep, min_radius, results);
}

py::tuple Projection2_c(
    py::object all_data,
    py::array_t<double> Point_3D,
    double Instrument_length = 1.0,
    double Instrument_Radius = 0.025,
    py::object begin_deep = py::none(),
    py::object end_deep = py::none(),
    double num_step = 0.5,
    bool if_draw = false,
    bool enable_two_stage_max_circle = false
) {
    (void)if_draw;
    auto trajectory_c = dataframe_to_trajectory_c(all_data);
    size_t depth_size = 0;
    size_t points_per_depth = 0;
    auto point_3d_c = numpy_to_point3d_c(Point_3D, depth_size, points_per_depth);

    double begin_depth = begin_deep.is_none() ? trajectory_c.front().depth : begin_deep.cast<double>();
    double end_depth = end_deep.is_none() ? trajectory_c.back().depth : end_deep.cast<double>();

    projection_c_input_view input_view{};
    input_view.trajectory = trajectory_c.data();
    input_view.trajectory_count = trajectory_c.size();
    input_view.point_3d = point_3d_c.data();
    input_view.depth_count = depth_size;
    input_view.ring_count = points_per_depth;

    projection_c_config config{};
    config.instrument_length = Instrument_length;
    config.instrument_radius = Instrument_Radius;
    config.num_step = num_step;
    config.begin_deep = begin_depth;
    config.end_deep = end_depth;
    config.enable_two_stage_max_circle = enable_two_stage_max_circle ? 1 : 0;

    projection_c_output output{};
    int status = projection_c_calculate(&input_view, &config, &output);
    if (status != PROJECTION_C_OK) {
        std::string message = output.error_message[0] != '\0' ? output.error_message : "C backend failed";
        projection_c_free_output(&output);
        throw std::runtime_error(message);
    }

    std::vector<CalculationResult> results;
    results.reserve(output.result_count);
    for (size_t idx = 0; idx < output.result_count; ++idx) {
        const auto& row = output.results[idx];
        results.push_back(CalculationResult{
            row.depth,
            row.tool_length,
            row.center_x,
            row.center_y,
            row.diameter,
            row.current_time,
            row.total_time
        });
    }

    std::vector<TrajectoryPoint> trajectory;
    trajectory.reserve(trajectory_c.size());
    for (const auto& pt : trajectory_c) {
        trajectory.push_back(TrajectoryPoint{pt.depth, Point3D(pt.position_x, pt.position_y, pt.position_z)});
    }

    auto py_result = pack_python_result(
        compute_python_style_deep(trajectory, results, begin_depth, num_step, output.passed != 0, output.stuck_depth),
        output.min_radius,
        results
    );
    projection_c_free_output(&output);
    return py_result;
}

PYBIND11_MODULE(projection_cpp, m) {
    m.doc() = "C++/C implementation of projection method for wellbore passability calculation";

    m.def("Projection2_cpp", &Projection2_cpp,
          py::arg("all_data"),
          py::arg("Point_3D"),
          py::arg("Instrument_length") = 1.0,
          py::arg("Instrument_Radius") = 0.025,
          py::arg("begin_deep") = py::none(),
          py::arg("end_deep") = py::none(),
          py::arg("num_step") = 0.5,
          py::arg("if_draw") = false,
          py::arg("enable_two_stage_max_circle") = false,
          "Calculate wellbore passability using projection method (C++ adapter over current implementation)");

    m.def("Projection2_c", &Projection2_c,
          py::arg("all_data"),
          py::arg("Point_3D"),
          py::arg("Instrument_length") = 1.0,
          py::arg("Instrument_Radius") = 0.025,
          py::arg("begin_deep") = py::none(),
          py::arg("end_deep") = py::none(),
          py::arg("num_step") = 0.5,
          py::arg("if_draw") = false,
          py::arg("enable_two_stage_max_circle") = false,
          "Calculate wellbore passability using projection method (pure C core backend)");
}
