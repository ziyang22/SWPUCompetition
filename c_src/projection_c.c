#include "projection_c.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define PROJECTION_C_EPS 1e-10

static double clamp_non_negative(double value) {
    if (value < 0.0 && value > -PROJECTION_C_EPS) {
        return 0.0;
    }
    return value;
}

typedef struct {
    projection_c_point3d* data;
    size_t size;
    size_t capacity;
} point3d_buffer;

typedef struct {
    projection_c_point2d* data;
    size_t size;
    size_t capacity;
} point2d_buffer;

static void set_error(projection_c_output* output, int code, const char* message) {
    output->error_code = code;
    output->passed = 0;
    output->stuck_depth = 0.0;
    output->min_radius = 0.0;
    if (message == NULL) {
        output->error_message[0] = '\0';
        return;
    }
    snprintf(output->error_message, sizeof(output->error_message), "%s", message);
}

static double point3d_dot(projection_c_point3d a, projection_c_point3d b) {
    return a.x * b.x + a.y * b.y + a.z * b.z;
}

static projection_c_point3d point3d_add(projection_c_point3d a, projection_c_point3d b) {
    projection_c_point3d p = {a.x + b.x, a.y + b.y, a.z + b.z};
    return p;
}

static projection_c_point3d point3d_sub(projection_c_point3d a, projection_c_point3d b) {
    projection_c_point3d p = {a.x - b.x, a.y - b.y, a.z - b.z};
    return p;
}

static projection_c_point3d point3d_scale(projection_c_point3d a, double scalar) {
    projection_c_point3d p = {a.x * scalar, a.y * scalar, a.z * scalar};
    return p;
}

static projection_c_point3d point3d_cross(projection_c_point3d a, projection_c_point3d b) {
    projection_c_point3d p = {
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x
    };
    return p;
}

static double point3d_norm(projection_c_point3d a) {
    return sqrt(a.x * a.x + a.y * a.y + a.z * a.z);
}

static projection_c_point3d point3d_normalized(projection_c_point3d a) {
    double n = point3d_norm(a);
    if (n <= PROJECTION_C_EPS) {
        projection_c_point3d zero = {0.0, 0.0, 0.0};
        return zero;
    }
    return point3d_scale(a, 1.0 / n);
}

static projection_c_point2d point2d_sub(projection_c_point2d a, projection_c_point2d b) {
    projection_c_point2d p = {a.x - b.x, a.y - b.y};
    return p;
}

static double point2d_norm(projection_c_point2d a) {
    return sqrt(a.x * a.x + a.y * a.y);
}

static int ensure_result_capacity(projection_c_output* output, size_t needed) {
    projection_c_result_row* new_results;
    size_t new_capacity;

    if (output->result_capacity >= needed) {
        return 1;
    }

    new_capacity = output->result_capacity == 0 ? 16 : output->result_capacity;
    while (new_capacity < needed) {
        new_capacity *= 2;
    }

    new_results = (projection_c_result_row*)realloc(output->results, new_capacity * sizeof(projection_c_result_row));
    if (new_results == NULL) {
        return 0;
    }

    output->results = new_results;
    output->result_capacity = new_capacity;
    return 1;
}

static int point3d_buffer_push(point3d_buffer* buffer, projection_c_point3d point) {
    projection_c_point3d* new_data;
    size_t new_capacity;

    if (buffer->size == buffer->capacity) {
        new_capacity = buffer->capacity == 0 ? 64 : buffer->capacity * 2;
        new_data = (projection_c_point3d*)realloc(buffer->data, new_capacity * sizeof(projection_c_point3d));
        if (new_data == NULL) {
            return 0;
        }
        buffer->data = new_data;
        buffer->capacity = new_capacity;
    }

    buffer->data[buffer->size++] = point;
    return 1;
}

static int point2d_buffer_push(point2d_buffer* buffer, projection_c_point2d point) {
    projection_c_point2d* new_data;
    size_t new_capacity;

    if (buffer->size == buffer->capacity) {
        new_capacity = buffer->capacity == 0 ? 64 : buffer->capacity * 2;
        new_data = (projection_c_point2d*)realloc(buffer->data, new_capacity * sizeof(projection_c_point2d));
        if (new_data == NULL) {
            return 0;
        }
        buffer->data = new_data;
        buffer->capacity = new_capacity;
    }

    buffer->data[buffer->size++] = point;
    return 1;
}

static const projection_c_point3d* point_3d_at(const projection_c_input_view* input, size_t depth_index, size_t ring_index) {
    return &input->point_3d[depth_index * input->ring_count + ring_index];
}

static int line_plane(
    double a,
    double b,
    double c,
    double A,
    double B,
    double C,
    double D,
    projection_c_point3d p,
    projection_c_point3d* out_point
) {
    double t_numerator = -(A * p.x + B * p.y + C * p.z + D);
    double t_denominator = a * A + b * B + c * C;
    double t;

    if (fabs(t_denominator) < PROJECTION_C_EPS) {
        return 0;
    }

    t = t_numerator / t_denominator;
    out_point->x = p.x + a * t;
    out_point->y = p.y + b * t;
    out_point->z = p.z + c * t;
    return 1;
}

static int line_plane_multiple(
    const projection_c_input_view* input,
    int start_idx,
    int end_idx,
    double a,
    double b,
    double c,
    double A,
    double B,
    double C,
    double D,
    point3d_buffer* projected
) {
    int k;
    size_t r;
    projection_c_point3d out_point;

    projected->size = 0;

    for (k = start_idx; k < end_idx; ++k) {
        if (k < 0 || (size_t)k >= input->depth_count) {
            continue;
        }
        for (r = 0; r < input->ring_count; ++r) {
            if (line_plane(a, b, c, A, B, C, D, *point_3d_at(input, (size_t)k, r), &out_point)) {
                if (!point3d_buffer_push(projected, out_point)) {
                    return 0;
                }
            }
        }
    }

    return 1;
}

static void projection_direction(
    double n0,
    double n1,
    double n2,
    double delta,
    point3d_buffer* directions
) {
    double zmax;
    double z;
    double z_step;

    directions->size = 0;

    if (delta < PROJECTION_C_EPS) {
        projection_c_point3d dir = {n0, n1, n2};
        point3d_buffer_push(directions, dir);
        return;
    }

    if (n0 * n0 + n1 * n1 > PROJECTION_C_EPS) {
        double radial_sq = clamp_non_negative(1.0 - n2 * n2);
        zmax = sqrt(radial_sq) * tan(delta);
        z = -zmax;
        z_step = 2.0 * zmax / 12.0;

        while (z < zmax) {
            if (fabs(n1) > PROJECTION_C_EPS) {
                double sqrt_term = sqrt(clamp_non_negative(zmax * zmax - z * z));
                double denom = n0 * n0 + n1 * n1;
                double x1 = (-n0 * n2 * z + sqrt_term * n1) / denom;
                double x2 = (-n0 * n2 * z - sqrt_term * n1) / denom;
                double y1 = (n0 * x1 + n2 * z) / n1;
                double y2 = (n0 * x2 + n2 * z) / n1;
                projection_c_point3d dir1 = {x1 + n0, y1 + n1, z + n2};
                projection_c_point3d dir2 = {x2 + n0, y2 + n1, z + n2};
                point3d_buffer_push(directions, dir1);
                point3d_buffer_push(directions, dir2);
            } else if (fabs(n0) > PROJECTION_C_EPS && fabs(n1) < PROJECTION_C_EPS) {
                double x = -n2 * z / n0;
                double y1 = sqrt(clamp_non_negative(tan(delta) * tan(delta) - (z / n0) * (z / n0)));
                double y2 = -y1;
                projection_c_point3d dir1 = {x + n0, y1 + n1, z + n2};
                projection_c_point3d dir2 = {x + n0, y2 + n1, z + n2};
                point3d_buffer_push(directions, dir1);
                point3d_buffer_push(directions, dir2);
            }
            z += z_step;
        }
    } else {
        projection_c_point3d dir = {tan(delta) + n0, tan(delta) + n1, n2};
        point3d_buffer_push(directions, dir);
    }
}

static int point3d_to_2d(
    double A,
    double B,
    double C,
    const point3d_buffer* points,
    projection_c_point3d origin,
    projection_c_point3d reference,
    point2d_buffer* output
) {
    projection_c_point3d n = {A, B, C};
    projection_c_point3d line1 = point3d_sub(reference, origin);
    projection_c_point3d line2 = point3d_cross(line1, n);
    double norm1 = point3d_norm(line1);
    double norm2 = point3d_norm(line2);
    size_t i;

    output->size = 0;

    if (norm1 > PROJECTION_C_EPS) {
        line1 = point3d_scale(line1, 1.0 / norm1);
    }
    if (norm2 > PROJECTION_C_EPS) {
        line2 = point3d_scale(line2, 1.0 / norm2);
    }

    for (i = 0; i < points->size; ++i) {
        projection_c_point3d point_o = point3d_sub(points->data[i], origin);
        projection_c_point2d out_point = {
            point3d_dot(point_o, line1),
            point3d_dot(point_o, line2)
        };
        if (!point2d_buffer_push(output, out_point)) {
            return 0;
        }
    }

    return 1;
}

static int get_closest_points(const point2d_buffer* points, point2d_buffer* closest_points) {
    double* min_dist;
    projection_c_point2d* chosen;
    int* used;
    size_t group_count = 0;
    size_t i;

    closest_points->size = 0;

    if (points->size == 0) {
        return 1;
    }

    min_dist = (double*)malloc(points->size * sizeof(double));
    chosen = (projection_c_point2d*)malloc(points->size * sizeof(projection_c_point2d));
    used = (int*)malloc(points->size * sizeof(int));
    if (min_dist == NULL || chosen == NULL || used == NULL) {
        free(min_dist);
        free(chosen);
        free(used);
        return 0;
    }

    for (i = 0; i < points->size; ++i) {
        double slope = atan2(points->data[i].x, points->data[i].y);
        int slope_key = (int)llround(slope * 10.0);
        size_t g;
        int found = 0;
        double dist = point2d_norm(points->data[i]);

        for (g = 0; g < group_count; ++g) {
            if (used[g] == slope_key) {
                if (dist < min_dist[g]) {
                    min_dist[g] = dist;
                    chosen[g] = points->data[i];
                }
                found = 1;
                break;
            }
        }

        if (!found) {
            used[group_count] = slope_key;
            min_dist[group_count] = dist;
            chosen[group_count] = points->data[i];
            group_count += 1;
        }
    }

    for (i = 0; i < group_count; ++i) {
        if (!point2d_buffer_push(closest_points, chosen[i])) {
            free(min_dist);
            free(chosen);
            free(used);
            return 0;
        }
    }

    free(min_dist);
    free(chosen);
    free(used);
    return 1;
}

static projection_c_circle max_inscribed_circle(const point2d_buffer* points, int grid_num) {
    projection_c_circle max_circle = {0.0, 0.0, 0.0};
    double max_radius = 0.0;
    double xmin;
    double xmax;
    double ymin;
    double ymax;
    double x_step;
    double y_step;
    int i;
    int j;
    size_t p;

    if (points->size == 0) {
        return max_circle;
    }

    xmin = xmax = points->data[0].x;
    ymin = ymax = points->data[0].y;

    for (p = 1; p < points->size; ++p) {
        if (points->data[p].x < xmin) xmin = points->data[p].x;
        if (points->data[p].x > xmax) xmax = points->data[p].x;
        if (points->data[p].y < ymin) ymin = points->data[p].y;
        if (points->data[p].y > ymax) ymax = points->data[p].y;
    }

    xmin *= 0.3;
    xmax *= 0.3;
    ymin *= 0.3;
    ymax *= 0.3;

    x_step = (xmax - xmin) / grid_num;
    y_step = (ymax - ymin) / grid_num;

    for (i = 0; i < grid_num; ++i) {
        double x0 = xmin + i * x_step;
        for (j = 0; j < grid_num; ++j) {
            double y0 = ymin + j * y_step;
            projection_c_point2d center = {x0, y0};
            double min_dist = 1e300;
            for (p = 0; p < points->size; ++p) {
                projection_c_point2d delta = point2d_sub(points->data[p], center);
                double dist = point2d_norm(delta);
                if (dist < min_dist) {
                    min_dist = dist;
                }
            }
            if (min_dist > max_radius) {
                max_radius = min_dist;
                max_circle.center_x = x0;
                max_circle.center_y = y0;
                max_circle.radius = min_dist;
            }
        }
    }

    max_circle.radius *= 0.98;
    return max_circle;
}

static int find_depth_index(const projection_c_input_view* input, double depth) {
    size_t i;
    double min_diff = 1e300;
    int closest_idx = 0;

    for (i = 0; i < input->trajectory_count; ++i) {
        double diff = fabs(input->trajectory[i].depth - depth);
        if (diff < 1e-6) {
            return (int)i;
        }
        if (diff < min_diff) {
            min_diff = diff;
            closest_idx = (int)i;
        }
    }

    return closest_idx;
}

static int append_result(projection_c_output* output, projection_c_result_row row) {
    if (!ensure_result_capacity(output, output->result_count + 1)) {
        return 0;
    }
    output->results[output->result_count++] = row;
    return 1;
}

static double now_seconds(void) {
    return (double)clock() / (double)CLOCKS_PER_SEC;
}

int projection_c_calculate(
    const projection_c_input_view* input,
    const projection_c_config* config,
    projection_c_output* output
) {
    int begin;
    int end;
    double depth_spacing;
    int step;
    int h_step;
    int i;
    double t_all = 0.0;
    point3d_buffer directions = {NULL, 0, 0};
    point3d_buffer projected = {NULL, 0, 0};
    point2d_buffer projected_2d = {NULL, 0, 0};
    point2d_buffer closest_2d = {NULL, 0, 0};

    if (output == NULL) {
        return PROJECTION_C_ERROR_INVALID_ARGUMENT;
    }

    memset(output, 0, sizeof(*output));

    if (input == NULL || config == NULL || input->trajectory == NULL || input->point_3d == NULL) {
        set_error(output, PROJECTION_C_ERROR_INVALID_ARGUMENT, "invalid input");
        return output->error_code;
    }

    if (input->trajectory_count < 2 || input->depth_count == 0 || input->ring_count == 0) {
        set_error(output, PROJECTION_C_ERROR_EMPTY_DATA, "empty trajectory or point data");
        return output->error_code;
    }

    if (config->begin_deep > config->end_deep) {
        set_error(output, PROJECTION_C_ERROR_INVALID_RANGE, "error: 结束深度小于起始深度");
        return output->error_code;
    }

    depth_spacing = input->trajectory[1].depth - input->trajectory[0].depth;
    step = (int)(config->num_step * 1000.0 / (depth_spacing * 1000.0));
    h_step = step;

    if (config->instrument_length < config->num_step) {
        set_error(output, PROJECTION_C_ERROR_NUM_STEP, "步进距离不能大于工具长度");
        return output->error_code;
    }

    begin = find_depth_index(input, config->begin_deep);
    end = find_depth_index(input, config->end_deep) + 1;
    if (end > (int)input->depth_count) {
        end = (int)input->depth_count;
    }

    i = begin;
    while (i < end - 1) {
        int j = i + h_step;
        projection_c_point3d Pi;
        projection_c_point3d Pj;
        projection_c_point3d diff;
        double d;
        projection_c_point3d n;
        double delta = 0.030 / config->instrument_length;
        double angle_step = delta / 8.0;
        double angle = 0.0;
        projection_c_point3d plane_normal;
        double A;
        double B;
        double C;
        double D;
        projection_c_circle min_circle = {0.0, 0.0, 0.0};
        double max_r = 0.0;
        double start_time = now_seconds();
        size_t m;
        projection_c_result_row row;

        if (j >= (int)input->depth_count) {
            j = (int)input->depth_count - 1;
        }

        if (i - step < 0) {
            Pi.x = input->trajectory[begin].position_x;
            Pi.y = input->trajectory[begin].position_y;
            Pi.z = input->trajectory[begin].position_z;
        } else {
            Pi.x = input->trajectory[i - step].position_x;
            Pi.y = input->trajectory[i - step].position_y;
            Pi.z = input->trajectory[i - step].position_z;
        }
        Pj.x = input->trajectory[j].position_x;
        Pj.y = input->trajectory[j].position_y;
        Pj.z = input->trajectory[j].position_z;

        diff = point3d_sub(Pj, Pi);
        d = point3d_norm(diff);
        n = point3d_scale(diff, 1.0 / d);

        directions.size = 0;
        while (angle < delta) {
            point3d_buffer local_directions = {NULL, 0, 0};
            size_t idx;
            projection_direction(n.x, n.y, n.z, angle, &local_directions);
            for (idx = 0; idx < local_directions.size; ++idx) {
                if (!point3d_buffer_push(&directions, local_directions.data[idx])) {
                    free(local_directions.data);
                    set_error(output, PROJECTION_C_ERROR_ALLOCATION_FAILED, "allocation failed");
                    goto cleanup;
                }
            }
            free(local_directions.data);
            angle += angle_step;
        }

        plane_normal.x = input->trajectory[j - 1].position_x - input->trajectory[j].position_x;
        plane_normal.y = input->trajectory[j - 1].position_y - input->trajectory[j].position_y;
        plane_normal.z = input->trajectory[j - 1].position_z - input->trajectory[j].position_z;
        plane_normal = point3d_normalized(plane_normal);

        A = plane_normal.x;
        B = plane_normal.y;
        C = plane_normal.z;
        D = -(A * input->trajectory[j].position_x + B * input->trajectory[j].position_y + C * input->trajectory[j].position_z);

        for (m = 0; m < directions.size; ++m) {
            int start_idx = j - step;
            projection_c_point3d mean_proj = {0.0, 0.0, 0.0};
            projection_c_circle current_circle;
            size_t p;

            if (start_idx < 0) {
                start_idx = 0;
            }

            if (!line_plane_multiple(
                    input,
                    start_idx,
                    j,
                    directions.data[m].x,
                    directions.data[m].y,
                    directions.data[m].z,
                    A,
                    B,
                    C,
                    D,
                    &projected)) {
                set_error(output, PROJECTION_C_ERROR_ALLOCATION_FAILED, "allocation failed");
                goto cleanup;
            }

            if (projected.size == 0) {
                continue;
            }

            for (p = 0; p < projected.size; ++p) {
                mean_proj = point3d_add(mean_proj, projected.data[p]);
            }
            mean_proj = point3d_scale(mean_proj, 1.0 / (double)projected.size);

            if (!point3d_to_2d(A, B, C, &projected, mean_proj, projected.data[3], &projected_2d)) {
                set_error(output, PROJECTION_C_ERROR_ALLOCATION_FAILED, "allocation failed");
                goto cleanup;
            }

            if (!get_closest_points(&projected_2d, &closest_2d)) {
                set_error(output, PROJECTION_C_ERROR_ALLOCATION_FAILED, "allocation failed");
                goto cleanup;
            }

            current_circle = max_inscribed_circle(&closest_2d, 30);
            if (current_circle.radius > max_r) {
                max_r = current_circle.radius;
                min_circle = current_circle;
            }
        }

        row.depth = input->trajectory[j].depth;
        row.tool_length = config->instrument_length;
        row.center_x = min_circle.center_x;
        row.center_y = min_circle.center_y;
        row.diameter = min_circle.radius * 2.0;
        row.current_time = now_seconds() - start_time;
        t_all += row.current_time;
        row.total_time = t_all;

        printf("深度:%.3f/%.3f, 工具长度: %.2fm\n 圆心:(%.3f,%.3f),直径：%.3f\n 当前段计算时间:%.2fs, 当前总耗时:%.2fs\n\n",
               input->trajectory[j].depth,
               input->trajectory[end - 1].depth,
               config->instrument_length,
               min_circle.center_x,
               min_circle.center_y,
               min_circle.radius * 2.0,
               row.current_time,
               t_all);

        if (!append_result(output, row)) {
            set_error(output, PROJECTION_C_ERROR_ALLOCATION_FAILED, "allocation failed");
            goto cleanup;
        }

        if (config->instrument_radius > min_circle.radius) {
            output->passed = 0;
            output->stuck_depth = input->trajectory[j].depth;
            output->min_radius = min_circle.radius;
            output->error_code = PROJECTION_C_OK;
            output->error_message[0] = '\0';
            goto cleanup;
        }

        i = j;
    }

    if (output->result_count > 0) {
        size_t idx;
        double min_r = 1e300;
        double min_r_depth = 0.0;
        for (idx = 0; idx < output->result_count; ++idx) {
            double r = output->results[idx].diameter / 2.0;
            if (r < min_r) {
                min_r = r;
                min_r_depth = output->results[idx].depth;
            }
        }
        output->passed = 1;
        output->stuck_depth = min_r_depth;
        output->min_radius = min_r;
    } else {
        output->passed = 1;
        output->stuck_depth = 0.0;
        output->min_radius = 0.0;
    }
    output->error_code = PROJECTION_C_OK;
    output->error_message[0] = '\0';

cleanup:
    free(directions.data);
    free(projected.data);
    free(projected_2d.data);
    free(closest_2d.data);
    return output->error_code;
}

void projection_c_free_output(projection_c_output* output) {
    if (output == NULL) {
        return;
    }
    free(output->results);
    output->results = NULL;
    output->result_count = 0;
    output->result_capacity = 0;
}
