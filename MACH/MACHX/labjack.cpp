#include <iostream>
#include <thread>
#include <chrono>
#include <string>
#include "LabJackM.h"
#include "labjack.hpp"

using namespace std;

// Global state
static int g_handle = 0;
static bool g_connected = false;

// Helper functions
void checkError(int error, const string& operation) {
    if (error != LJME_NOERROR) {
        char errorString[LJM_MAX_NAME_SIZE];
        LJM_ErrorToString(error, errorString);
        throw LabJackError(operation + " failed: " + errorString);
    }
}

void retryOperation(const string& operation, function<void()> op) {
    int retries = 0;
    while (retries < MAX_RETRIES) {
        try {
            op();
            return;
        }
        catch (const LabJackError& e) {
            if (++retries == MAX_RETRIES) {
                throw;
            }
            this_thread::sleep_for(chrono::milliseconds(RETRY_DELAY_MS));
        }
    }
}

void startConnection() {
    if (g_connected) {
        return;
    }

    try {
        int error = LJM_Open(LJM_dtANY, LJM_ctANY, "LJM_idANY", &g_handle);
        checkError(error, "Opening LabJack connection");

        // Configure analog inputs
        const vector<pair<string, double>> configs = {
            {"AIN0_NEGATIVE_CH", 1.0},
            {"AIN0_RANGE", 0.01},
            {"AIN2_NEGATIVE_CH", 3.0},
            {"AIN2_RANGE", 0.01},
            {"AIN4_NEGATIVE_CH", 5.0},
            {"AIN4_RANGE", 0.01}
        };

        for (const auto& config : configs) {
            error = LJM_eWriteName(g_handle, config.first.c_str(), config.second);
            checkError(error, "Configuring " + config.first);
        }

        g_connected = true;
    }
    catch (const exception& e) {
        if (g_handle) {
            LJM_Close(g_handle);
            g_handle = 0;
        }
        throw LabJackError("Failed to start connection: " + string(e.what()));
    }
}

double sensorFeedback(const string& port) {
    if (!g_connected) {
        throw LabJackError("LabJack not connected");
    }

    double voltage = 0.0;
    retryOperation("Reading sensor value", [&]() {
        int error = LJM_eReadName(g_handle, port.c_str(), &voltage);
        checkError(error, "Reading sensor " + port);
    });

    return voltage;
}

void setValve(const string& port, double value) {
    if (!g_connected) {
        throw LabJackError("LabJack not connected");
    }

    if (value < MIN_VOLTAGE || value > MAX_VOLTAGE) {
        throw LabJackError("Invalid voltage value: " + to_string(value));
    }

    retryOperation("Setting valve", [&]() {
        int error = LJM_eWriteName(g_handle, port.c_str(), value);
        checkError(error, "Setting valve " + port);
    });
}

void endConnection() {
    if (g_connected) {
        try {
            int error = LJM_Close(g_handle);
            checkError(error, "Closing LabJack connection");
        }
        catch (const exception& e) {
            cerr << "Error closing connection: " << e.what() << endl;
        }
        g_handle = 0;
        g_connected = false;
    }
} 