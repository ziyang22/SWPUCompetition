#ifndef PROJECTION_METHOD_H
#define PROJECTION_METHOD_H

#include <vector>
#include <array>
#include <string>
#include <optional>

namespace projection {

// 3D point structure
struct Point3D {
    double x, y, z;

    Point3D() : x(0), y(0), z(0) {}
    Point3D(double x_, double y_, double z_) : x(x_), y(y_), z(z_) {}

    Point3D operator+(const Point3D& other) const {
        return Point3D(x + other.x, y + other.y, z + other.z);
    }

    Point3D operator-(const Point3D& other) const {
        return Point3D(x - other.x, y - other.y, z - other.z);
    }

    Point3D operator*(double scalar) const {
        return Point3D(x * scalar, y * scalar, z * scalar);
    }

    Point3D operator/(double scalar) const {
        return Point3D(x / scalar, y / scalar, z / scalar);
    }

    double dot(const Point3D& other) const {
        return x * other.x + y * other.y + z * other.z;
    }

    Point3D cross(const Point3D& other) const {
        return Point3D(
            y * other.z - z * other.y,
            z * other.x - x * other.z,
            x * other.y - y * other.x
        );
    }

    double norm() const {
        return std::sqrt(x * x + y * y + z * z);
    }

    Point3D normalized() const {
        double n = norm();
        return (n > 0) ? (*this / n) : Point3D(0, 0, 0);
    }
};

// 2D point structure
struct Point2D {
    double x, y;

    Point2D() : x(0), y(0) {}
    Point2D(double x_, double y_) : x(x_), y(y_) {}

    Point2D operator-(const Point2D& other) const {
        return Point2D(x - other.x, y - other.y);
    }

    double norm() const {
        return std::sqrt(x * x + y * y);
    }
};

// Circle structure
struct Circle {
    double center_x, center_y, radius;

    Circle() : center_x(0), center_y(0), radius(0) {}
    Circle(double cx, double cy, double r) : center_x(cx), center_y(cy), radius(r) {}
};

// Trajectory data point
struct TrajectoryPoint {
    double depth;
    Point3D position;  // N, E, H coordinates
};

// Result data structure
struct CalculationResult {
    double depth;
    double tool_length;
    double center_x;
    double center_y;
    double diameter;
    double current_time;
    double total_time;
};

// Main projection calculation class
class ProjectionCalculator {
public:
    ProjectionCalculator(
        const std::vector<TrajectoryPoint>& trajectory,
        const std::vector<std::vector<Point3D>>& point_3d,  // CHANGED: 2D array now
        double instrument_length,
        double instrument_radius,
        double num_step
    );

    // Main calculation function
    bool calculate(
        double begin_deep,
        double end_deep,
        std::vector<CalculationResult>& results,
        double& stuck_depth,
        double& min_radius
    );

private:
    // Calculate line-plane intersection
    std::optional<Point3D> linePlane(
        double a, double b, double c,  // line direction
        double A, double B, double C, double D,  // plane parameters
        const Point3D& p  // point on line
    ) const;

    // Calculate line-plane intersection for multiple points (3D array slice)
    std::vector<Point3D> linePlaneMultiple(
        double a, double b, double c,
        double A, double B, double C, double D,
        const std::vector<std::vector<Point3D>>& points  // slice of point_3d
    ) const;

    // Generate projection directions
    void projectionDirection(
        double n0, double n1, double n2,
        double delta,
        std::vector<double>& X,
        std::vector<double>& Y,
        std::vector<double>& Z
    ) const;

    // Convert 3D points to 2D
    std::vector<Point2D> point3DTo2D(
        double A, double B, double C,
        const std::vector<Point3D>& points,
        const Point3D& origin,
        const Point3D& reference
    ) const;

    // Get closest points (inner boundary)
    std::vector<Point2D> getClosestPoints(const std::vector<Point2D>& points) const;

    // Find maximum inscribed circle
    Circle maxInscribedCircle(const std::vector<Point2D>& points, int grid_num) const;

    // Find trajectory index for given depth
    int findDepthIndex(double depth) const;

private:
    std::vector<TrajectoryPoint> trajectory_;
    std::vector<std::vector<Point3D>> point_3d_;  // CHANGED: 2D array now [depth][24_points]
    double instrument_length_;
    double instrument_radius_;
    double num_step_;
    int step_;
    int h_step_;
};

// Utility functions
std::vector<TrajectoryPoint> loadTrajectoryFromCSV(const std::string& filename);
std::vector<std::vector<Point3D>> loadPoint3DFromNPY(const std::string& filename);  // CHANGED
void saveResults(const std::string& filename, const std::vector<CalculationResult>& results);

} // namespace projection

#endif // PROJECTION_METHOD_H
