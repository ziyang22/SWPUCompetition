#ifndef PROJECTION_C_H
#define PROJECTION_C_H

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    double x;
    double y;
    double z;
} projection_c_point3d;

typedef struct {
    double x;
    double y;
} projection_c_point2d;

typedef struct {
    double center_x;
    double center_y;
    double radius;
} projection_c_circle;

typedef struct {
    double depth;
    double position_x;
    double position_y;
    double position_z;
} projection_c_trajectory_point;

typedef struct {
    double depth;
    double tool_length;
    double center_x;
    double center_y;
    double diameter;
    double current_time;
    double total_time;
} projection_c_result_row;

typedef struct {
    double setup_time;
    double direction_generation_time;
    double direction_loop_time;
    double projection_time;
    double mean_reduction_time;
    double point3d_to_2d_time;
    double closest_points_time;
    double max_inscribed_circle_time;
    double residual_time;
    size_t window_count;
    size_t direction_count_total;
    size_t empty_projection_direction_count;
    size_t projected_points_total;
    size_t closest_points_total;
    size_t projected_points_max;
    size_t closest_points_max;
} projection_c_profile_summary;

typedef struct {
    const projection_c_trajectory_point* trajectory;
    size_t trajectory_count;
    const projection_c_point3d* point_3d;
    size_t depth_count;
    size_t ring_count;
} projection_c_input_view;

typedef struct {
    double instrument_length;
    double instrument_radius;
    double num_step;
    double begin_deep;
    double end_deep;
} projection_c_config;

typedef struct {
    projection_c_result_row* results;
    size_t result_count;
    size_t result_capacity;
    int passed;
    double stuck_depth;
    double min_radius;
    projection_c_profile_summary profile;
    int error_code;
    char error_message[256];
} projection_c_output;

enum {
    PROJECTION_C_OK = 0,
    PROJECTION_C_ERROR_INVALID_ARGUMENT = 1,
    PROJECTION_C_ERROR_INVALID_RANGE = 2,
    PROJECTION_C_ERROR_ALLOCATION_FAILED = 3,
    PROJECTION_C_ERROR_NUM_STEP = 4,
    PROJECTION_C_ERROR_EMPTY_DATA = 5
};

int projection_c_calculate(
    const projection_c_input_view* input,
    const projection_c_config* config,
    projection_c_output* output
);

void projection_c_free_output(projection_c_output* output);

#ifdef __cplusplus
}
#endif

#endif
