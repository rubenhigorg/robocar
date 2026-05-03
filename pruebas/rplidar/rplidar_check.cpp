#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <limits>
#include <numeric>
#include <string>
#include <vector>

#include "sl_lidar.h"
#include "sl_lidar_driver.h"

#ifndef _countof
#define _countof(_Array) (int)(sizeof(_Array) / sizeof(_Array[0]))
#endif

#ifdef _WIN32
#include <Windows.h>
#define delay_ms(x) ::Sleep(x)
#else
#include <unistd.h>
static inline void delay_ms(sl_word_size_t ms)
{
    usleep(ms * 1000);
}
#endif

using namespace sl;

struct Options {
    const char* serial_port = "/dev/ttyUSB0";
    sl_u32 baudrate = 460800;
    int frames = 20;
    int warmup_frames = 3;
    float min_distance_mm = 50.0f;
    float max_distance_mm = 12000.0f;
    int min_points_per_frame = 100;
    float min_angular_coverage_deg = 270.0f;
    float min_valid_ratio = 0.10f;
};

struct FrameStats {
    int total_points = 0;
    int valid_points = 0;
    float min_distance = std::numeric_limits<float>::max();
    float max_distance = 0.0f;
    double sum_distance = 0.0;
    double sum_quality = 0.0;
    bool angle_bucket[360] = {false};
};

static void usage(const char* program)
{
    std::cerr
        << "Usage: " << program << " [options]\n"
        << "  --serial /dev/ttyUSB0\n"
        << "  --baudrate 460800\n"
        << "  --frames 20\n"
        << "  --warmup-frames 3\n"
        << "  --min-points 100\n"
        << "  --min-coverage 270\n"
        << "  --max-distance 12000\n";
}

static std::string serial_to_hex(const sl_lidar_response_device_info_t& info)
{
    char buffer[33];
    for (int i = 0; i < 16; ++i) {
        std::snprintf(buffer + (i * 2), 3, "%02X", info.serialnum[i]);
    }
    buffer[32] = '\0';
    return std::string(buffer);
}

static void fail(const std::string& reason)
{
    std::cout << "\nRESULT: FAIL\n";
    std::cout << "Reason: " << reason << "\n";
}

static bool parse_args(int argc, const char* argv[], Options& options)
{
    for (int i = 1; i < argc; ++i) {
        if ((std::strcmp(argv[i], "--serial") == 0 || std::strcmp(argv[i], "-s") == 0) && i + 1 < argc) {
            options.serial_port = argv[++i];
        } else if ((std::strcmp(argv[i], "--baudrate") == 0 || std::strcmp(argv[i], "-b") == 0) && i + 1 < argc) {
            options.baudrate = static_cast<sl_u32>(std::strtoul(argv[++i], nullptr, 10));
        } else if (std::strcmp(argv[i], "--frames") == 0 && i + 1 < argc) {
            options.frames = std::atoi(argv[++i]);
        } else if (std::strcmp(argv[i], "--warmup-frames") == 0 && i + 1 < argc) {
            options.warmup_frames = std::atoi(argv[++i]);
        } else if (std::strcmp(argv[i], "--min-points") == 0 && i + 1 < argc) {
            options.min_points_per_frame = std::atoi(argv[++i]);
        } else if (std::strcmp(argv[i], "--min-coverage") == 0 && i + 1 < argc) {
            options.min_angular_coverage_deg = std::strtof(argv[++i], nullptr);
        } else if (std::strcmp(argv[i], "--max-distance") == 0 && i + 1 < argc) {
            options.max_distance_mm = std::strtof(argv[++i], nullptr);
        } else if (std::strcmp(argv[i], "--help") == 0 || std::strcmp(argv[i], "-h") == 0) {
            usage(argv[0]);
            return false;
        } else {
            usage(argv[0]);
            return false;
        }
    }
    return options.frames > 0;
}

static void accumulate_frame(
    const sl_lidar_response_measurement_node_hq_t* nodes,
    size_t count,
    const Options& options,
    FrameStats& stats)
{
    stats.total_points = static_cast<int>(count);
    for (size_t i = 0; i < count; ++i) {
        const float angle = (nodes[i].angle_z_q14 * 90.0f) / 16384.0f;
        const float distance = nodes[i].dist_mm_q2 / 4.0f;
        const int quality = nodes[i].quality >> SL_LIDAR_RESP_MEASUREMENT_QUALITY_SHIFT;

        if (distance < options.min_distance_mm || distance > options.max_distance_mm || quality <= 0) {
            continue;
        }

        const int bucket = std::max(0, std::min(359, static_cast<int>(angle)));
        stats.angle_bucket[bucket] = true;
        stats.valid_points += 1;
        stats.min_distance = std::min(stats.min_distance, distance);
        stats.max_distance = std::max(stats.max_distance, distance);
        stats.sum_distance += distance;
        stats.sum_quality += quality;
    }
}

int main(int argc, const char* argv[])
{
    Options options;
    if (!parse_args(argc, argv, options)) {
        return 2;
    }

    std::cout << "RPLIDAR C1 functional test\n";
    std::cout << "Port: " << options.serial_port << "\n";
    std::cout << "Baudrate: " << options.baudrate << "\n";
    std::cout << "Frames: " << options.frames << "\n\n";

    IChannel* channel = *createSerialPortChannel(options.serial_port, options.baudrate);
    ILidarDriver* lidar = *createLidarDriver();

    if (!channel || !lidar) {
        fail("No se pudo inicializar el SDK");
        return 1;
    }

    if (SL_IS_FAIL(lidar->connect(channel))) {
        fail("No se pudo abrir el puerto serie");
        delete lidar;
        delete channel;
        return 1;
    }

    sl_lidar_response_device_info_t info;
    if (SL_IS_FAIL(lidar->getDeviceInfo(info))) {
        fail("No se pudo leer device info");
        delete lidar;
        delete channel;
        return 1;
    }

    std::cout << "Device info: OK\n";
    std::cout << "  Serial: " << serial_to_hex(info) << "\n";
    std::cout << "  Firmware: " << (info.firmware_version >> 8) << "." << (info.firmware_version & 0xFF) << "\n";
    std::cout << "  Hardware: " << static_cast<int>(info.hardware_version) << "\n";
    std::cout << "  Model: " << static_cast<int>(info.model) << "\n";

    sl_lidar_response_device_health_t health;
    if (SL_IS_FAIL(lidar->getHealth(health))) {
        fail("No se pudo leer health status");
        delete lidar;
        delete channel;
        return 1;
    }
    if (health.status == SL_LIDAR_STATUS_ERROR) {
        fail("El LIDAR reporta health status ERROR");
        delete lidar;
        delete channel;
        return 1;
    }
    std::cout << "Health: OK";
    if (health.status == SL_LIDAR_STATUS_WARNING) {
        std::cout << " (WARNING)";
    }
    std::cout << " error_code=" << health.error_code << "\n";

    std::vector<LidarScanMode> modes;
    if (SL_IS_OK(lidar->getAllSupportedScanModes(modes))) {
        std::cout << "Scan modes: ";
        for (size_t i = 0; i < modes.size(); ++i) {
            if (i > 0) {
                std::cout << ", ";
            }
            std::cout << modes[i].scan_mode;
        }
        std::cout << "\n";
    } else {
        std::cout << "Scan modes: no disponibles\n";
    }

    lidar->setMotorSpeed();

    LidarScanMode used_mode;
    if (SL_IS_FAIL(lidar->startScan(false, true, 0, &used_mode))) {
        fail("No se pudo iniciar el escaneo");
        lidar->setMotorSpeed(0);
        delete lidar;
        delete channel;
        return 1;
    }

    std::cout << "Scan start: OK";
    if (used_mode.scan_mode[0] != '\0') {
        std::cout << " (" << used_mode.scan_mode << ")";
    }
    std::cout << "\n\n";

    delay_ms(500);

    std::vector<FrameStats> frames;
    frames.reserve(options.frames);
    const auto start = std::chrono::steady_clock::now();

    for (int frame = 0; frame < options.frames + options.warmup_frames; ++frame) {
        sl_lidar_response_measurement_node_hq_t nodes[8192];
        size_t count = _countof(nodes);
        sl_result result = lidar->grabScanDataHq(nodes, count, 1500);

        if (SL_IS_FAIL(result) && result != SL_RESULT_OPERATION_TIMEOUT) {
            fail("Error capturando scan data");
            lidar->stop();
            lidar->setMotorSpeed(0);
            delete lidar;
            delete channel;
            return 1;
        }

        lidar->ascendScanData(nodes, count);
        if (frame < options.warmup_frames) {
            continue;
        }

        FrameStats stats;
        accumulate_frame(nodes, count, options, stats);
        frames.push_back(stats);
    }

    const auto end = std::chrono::steady_clock::now();
    const double elapsed_seconds = std::chrono::duration<double>(end - start).count();

    lidar->stop();
    delay_ms(20);
    lidar->setMotorSpeed(0);
    delete lidar;
    delete channel;

    int total_points = 0;
    int total_valid = 0;
    int min_valid_frame = std::numeric_limits<int>::max();
    int max_valid_frame = 0;
    float min_distance = std::numeric_limits<float>::max();
    float max_distance = 0.0f;
    double sum_distance = 0.0;
    double sum_quality = 0.0;
    bool global_angle_bucket[360] = {false};

    for (const FrameStats& stats : frames) {
        total_points += stats.total_points;
        total_valid += stats.valid_points;
        min_valid_frame = std::min(min_valid_frame, stats.valid_points);
        max_valid_frame = std::max(max_valid_frame, stats.valid_points);
        min_distance = std::min(min_distance, stats.min_distance);
        max_distance = std::max(max_distance, stats.max_distance);
        sum_distance += stats.sum_distance;
        sum_quality += stats.sum_quality;
        for (int i = 0; i < 360; ++i) {
            global_angle_bucket[i] = global_angle_bucket[i] || stats.angle_bucket[i];
        }
    }

    int angular_buckets = 0;
    for (bool seen : global_angle_bucket) {
        if (seen) {
            angular_buckets += 1;
        }
    }

    const double avg_points_per_frame = frames.empty() ? 0.0 : static_cast<double>(total_valid) / frames.size();
    const double valid_ratio = total_points > 0 ? static_cast<double>(total_valid) / total_points : 0.0;
    const double avg_distance = total_valid > 0 ? sum_distance / total_valid : 0.0;
    const double avg_quality = total_valid > 0 ? sum_quality / total_valid : 0.0;
    const double fps = elapsed_seconds > 0.0 ? frames.size() / elapsed_seconds : 0.0;

    if (total_valid == 0) {
        min_distance = 0.0f;
    }
    if (min_valid_frame == std::numeric_limits<int>::max()) {
        min_valid_frame = 0;
    }

    std::cout << "Samples:\n";
    std::cout << "  Frames: " << frames.size() << "\n";
    std::cout << "  Approx FPS: " << fps << "\n";
    std::cout << "  Avg valid points/frame: " << avg_points_per_frame << "\n";
    std::cout << "  Min valid points/frame: " << min_valid_frame << "\n";
    std::cout << "  Max valid points/frame: " << max_valid_frame << "\n";
    std::cout << "  Valid ratio: " << valid_ratio * 100.0 << " %\n";
    std::cout << "  Angular coverage: " << angular_buckets << " deg\n";
    std::cout << "  Min distance: " << min_distance << " mm\n";
    std::cout << "  Max distance: " << max_distance << " mm\n";
    std::cout << "  Avg distance: " << avg_distance << " mm\n";
    std::cout << "  Avg quality: " << avg_quality << "\n";

    if (avg_points_per_frame < options.min_points_per_frame) {
        fail("Pocos puntos validos por frame");
        return 1;
    }
    if (angular_buckets < options.min_angular_coverage_deg) {
        fail("Cobertura angular insuficiente");
        return 1;
    }
    if (valid_ratio < options.min_valid_ratio) {
        fail("Ratio de puntos validos insuficiente");
        return 1;
    }

    std::cout << "\nRESULT: OK\n";
    return 0;
}
