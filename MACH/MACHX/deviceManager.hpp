#ifndef DEVICEMANAGER_H
#define DEVICEMANAGER_H

#include <string>
#include <cstring>
#include <sstream>
#include <vector>
#include <stdexcept>
#include <memory>
#include <mutex>

// Constants
constexpr int MAX_DEVICES = 100;
constexpr int PORT_LENGTH = 4;
constexpr int BUFFER_SIZE = 7;
constexpr int VALVE_BUFFER_SIZE = 3;

// Custom exceptions
class DeviceError : public std::runtime_error {
public:
    explicit DeviceError(const std::string& message) : std::runtime_error(message) {}
};

class Valve
{
public:
    Valve() = default;
    Valve(const std::string& port_, double inputVol_ = 0.0, bool state_ = false)
        : port(port_), inputVol(inputVol_), state(state_) {}

    bool state{false};
    std::string port;
    double inputVol{0.0};

    // Validation methods
    bool isValid() const {
        return !port.empty() && port.length() == PORT_LENGTH;
    }
};

class Sensor
{
public:
    Sensor() = default;
    Sensor(const std::string& port_, double minVol_ = 0.0, double maxVol_ = 5.0,
           double minReading_ = 0.0, double maxReading_ = 100.0)
        : port(port_), minVol(minVol_), maxVol(maxVol_),
          minReading(minReading_), maxReading(maxReading_) {}

    double value{0.0};
    double minVol{0.0};
    double maxVol{5.0};
    double minReading{0.0};
    double maxReading{100.0};
    std::string port;

    // Validation methods
    bool isValid() const {
        return !port.empty() && port.length() == PORT_LENGTH &&
               minVol < maxVol && minReading < maxReading;
    }
};

// Device management functions
void create_device(const std::string& input);
void updateSensorValue();
std::string getValues();
void changeValveState(const std::string& port_, bool state_);
double getSensorValue(const std::string& port_);

// Device cleanup
void cleanup_devices();

#endif