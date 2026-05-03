#include <csignal>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iostream>
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

static volatile std::sig_atomic_t stop_requested = 0;

static void handle_signal(int)
{
    stop_requested = 1;
}

static void usage(const char* program)
{
    std::cerr << "Usage: " << program << " --serial /dev/ttyUSB0 --baudrate 460800 --max-distance 12000\n";
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

static std::string json_escape(const char* text)
{
    std::string out;
    for (const char* p = text; *p; ++p) {
        if (*p == '"' || *p == '\\') {
            out.push_back('\\');
        }
        out.push_back(*p);
    }
    return out;
}

int main(int argc, const char* argv[])
{
    const char* serial_port = "/dev/ttyUSB0";
    sl_u32 baudrate = 460800;
    float max_distance_mm = 12000.0f;

    for (int i = 1; i < argc; ++i) {
        if ((std::strcmp(argv[i], "--serial") == 0 || std::strcmp(argv[i], "-s") == 0) && i + 1 < argc) {
            serial_port = argv[++i];
        } else if ((std::strcmp(argv[i], "--baudrate") == 0 || std::strcmp(argv[i], "-b") == 0) && i + 1 < argc) {
            baudrate = static_cast<sl_u32>(std::strtoul(argv[++i], nullptr, 10));
        } else if (std::strcmp(argv[i], "--max-distance") == 0 && i + 1 < argc) {
            max_distance_mm = std::strtof(argv[++i], nullptr);
        } else {
            usage(argv[0]);
            return 2;
        }
    }

    std::signal(SIGINT, handle_signal);
    std::signal(SIGTERM, handle_signal);

    IChannel* channel = *createSerialPortChannel(serial_port, baudrate);
    ILidarDriver* lidar = *createLidarDriver();

    if (!channel || !lidar) {
        std::cerr << "No se pudo inicializar el SDK.\n";
        return 1;
    }

    if (SL_IS_FAIL(lidar->connect(channel))) {
        std::cerr << "No se pudo abrir " << serial_port << " a " << baudrate << " baudios.\n";
        delete lidar;
        delete channel;
        return 1;
    }

    sl_lidar_response_device_info_t info;
    if (SL_IS_FAIL(lidar->getDeviceInfo(info))) {
        std::cerr << "No se pudo leer device info.\n";
        delete lidar;
        delete channel;
        return 1;
    }

    std::cout << "{\"type\":\"device\",\"serial\":\"" << serial_to_hex(info) << "\","
              << "\"firmware\":\"" << (info.firmware_version >> 8) << "." << (info.firmware_version & 0xFF) << "\","
              << "\"hardware\":" << static_cast<int>(info.hardware_version) << ","
              << "\"model\":" << static_cast<int>(info.model) << "}" << std::endl;

    sl_lidar_response_device_health_t health;
    if (SL_IS_OK(lidar->getHealth(health))) {
        std::cout << "{\"type\":\"health\",\"status\":" << static_cast<int>(health.status)
                  << ",\"error_code\":" << health.error_code << "}" << std::endl;
    }

    std::vector<LidarScanMode> modes;
    if (SL_IS_OK(lidar->getAllSupportedScanModes(modes))) {
        std::cout << "{\"type\":\"scan_modes\",\"modes\":[";
        for (size_t i = 0; i < modes.size(); ++i) {
            if (i > 0) {
                std::cout << ",";
            }
            std::cout << "{\"id\":" << modes[i].id
                      << ",\"name\":\"" << json_escape(modes[i].scan_mode) << "\""
                      << ",\"us_per_sample\":" << modes[i].us_per_sample
                      << ",\"max_distance\":" << modes[i].max_distance << "}";
        }
        std::cout << "]}" << std::endl;
    }

    lidar->setMotorSpeed();

    LidarScanMode used_mode;
    if (SL_IS_FAIL(lidar->startScan(false, true, 0, &used_mode))) {
        std::cerr << "No se pudo iniciar el escaneo.\n";
        lidar->setMotorSpeed(0);
        delete lidar;
        delete channel;
        return 1;
    }

    std::cout << "{\"type\":\"started\",\"mode\":\"" << json_escape(used_mode.scan_mode)
              << "\",\"max_distance\":" << used_mode.max_distance
              << ",\"us_per_sample\":" << used_mode.us_per_sample << "}" << std::endl;

    while (!stop_requested) {
        sl_lidar_response_measurement_node_hq_t nodes[8192];
        size_t count = _countof(nodes);
        sl_result result = lidar->grabScanDataHq(nodes, count, 1000);

        if (SL_IS_OK(result) || result == SL_RESULT_OPERATION_TIMEOUT) {
            lidar->ascendScanData(nodes, count);

            std::cout << "{\"type\":\"scan\",\"points\":[";
            bool first = true;
            for (size_t i = 0; i < count; ++i) {
                const float angle = (nodes[i].angle_z_q14 * 90.0f) / 16384.0f;
                const float distance = nodes[i].dist_mm_q2 / 4.0f;
                const int quality = nodes[i].quality >> SL_LIDAR_RESP_MEASUREMENT_QUALITY_SHIFT;

                if (distance <= 0.0f || distance > max_distance_mm || quality <= 0) {
                    continue;
                }

                if (!first) {
                    std::cout << ",";
                }
                first = false;
                std::cout << "[" << angle << "," << distance << "," << quality << "]";
            }
            std::cout << "]}" << std::endl;
        } else {
            std::cerr << "Error leyendo scan: " << std::hex << result << std::dec << "\n";
            delay_ms(100);
        }
    }

    lidar->stop();
    delay_ms(20);
    lidar->setMotorSpeed(0);
    delete lidar;
    delete channel;
    return 0;
}
