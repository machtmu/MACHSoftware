#ifndef LABJACK_H
#define LABJACK_H

#include <string>
#include <stdexcept>

// Custom exception for LabJack operations
class LabJackError : public std::runtime_error {
public:
    explicit LabJackError(const std::string& message) : std::runtime_error(message) {}
};

// Constants
constexpr int MAX_RETRIES = 3;
constexpr int RETRY_DELAY_MS = 100;
constexpr double MIN_VOLTAGE = 0.0;
constexpr double MAX_VOLTAGE = 5.0;

// LabJack operations
void startConnection();
void endConnection();
double sensorFeedback(const std::string& port);
void setValve(const std::string& port, double value);

#endif