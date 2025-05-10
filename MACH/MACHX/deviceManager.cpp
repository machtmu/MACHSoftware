#include <iostream>
#include <mutex>
#include <algorithm>
#include <sstream>
#include "deviceManager.hpp"
#include "labjack.hpp"

using namespace std;

// Thread-safe device storage
static vector<Valve> valves;
static vector<Sensor> sensors;
static mutex device_mutex;

//for sensors init
// sP320.0000010.00000.000001000.00 

//for valves init
//vV3602.2

int buffer = 7;
int bufferValve = 3;

void create_device(const string& input)
{
    if (input.empty()) {
        throw DeviceError("Empty input string");
    }

    lock_guard<mutex> lock(device_mutex);

    // Check total device limit
    if (valves.size() + sensors.size() >= MAX_DEVICES) {
        throw DeviceError("Maximum number of devices reached");
    }

    try {
        if (input[0] == 's') {
            if (input.length() < 1 + PORT_LENGTH + 4 * BUFFER_SIZE) {
                throw DeviceError("Invalid sensor input format");
            }

            string port = input.substr(1, PORT_LENGTH);
            double minVol = stod(input.substr(1 + PORT_LENGTH, BUFFER_SIZE));
            double maxVol = stod(input.substr(1 + PORT_LENGTH + BUFFER_SIZE, BUFFER_SIZE));
            double minReading = stod(input.substr(1 + PORT_LENGTH + 2 * BUFFER_SIZE, BUFFER_SIZE));
            double maxReading = stod(input.substr(1 + PORT_LENGTH + 3 * BUFFER_SIZE, BUFFER_SIZE));

            auto it = find_if(sensors.begin(), sensors.end(),
                            [&port](const Sensor& s) { return s.port == port; });

            if (it != sensors.end()) {
                it->minVol = minVol;
                it->maxVol = maxVol;
                it->minReading = minReading;
                it->maxReading = maxReading;
            } else {
                Sensor newSensor(port, minVol, maxVol, minReading, maxReading);
                if (!newSensor.isValid()) {
                    throw DeviceError("Invalid sensor configuration");
                }
                sensors.push_back(newSensor);
            }
        }
        else if (input[0] == 'v') {
            if (input.length() < 1 + PORT_LENGTH + 1 + VALVE_BUFFER_SIZE) {
                throw DeviceError("Invalid valve input format");
            }

            string port = input.substr(1, PORT_LENGTH);
            bool state = (input[1 + PORT_LENGTH] == '1');
            double inputVol = stod(input.substr(1 + PORT_LENGTH + 1, VALVE_BUFFER_SIZE));

            auto it = find_if(valves.begin(), valves.end(),
                            [&port](const Valve& v) { return v.port == port; });

            if (it != valves.end()) {
                it->state = state;
                it->inputVol = inputVol;
            } else {
                Valve newValve(port, inputVol, state);
                if (!newValve.isValid()) {
                    throw DeviceError("Invalid valve configuration");
                }
                valves.push_back(newValve);
            }
        }
        else {
            throw DeviceError("Invalid device type");
        }
    }
    catch (const std::exception& e) {
        throw DeviceError(string("Error creating device: ") + e.what());
    }
}

void updateSensorValue()
{
    lock_guard<mutex> lock(device_mutex);
    
    for (Sensor& s : sensors) {
        try {
            double rawValue = sensorFeedback(s.port);
            // Apply scaling based on voltage and reading ranges
            double scale = (s.maxReading - s.minReading) / (s.maxVol - s.minVol);
            double offset = -s.minVol * scale + s.minReading;
            s.value = rawValue * scale + offset;
        }
        catch (const std::exception& e) {
            cerr << "Error updating sensor " << s.port << ": " << e.what() << endl;
        }
    }
}

double getSensorValue(const string& port_)
{
    lock_guard<mutex> lock(device_mutex);
    
    auto it = find_if(sensors.begin(), sensors.end(),
                     [&port_](const Sensor& s) { return s.port == port_; });
    
    if (it != sensors.end()) {
        return it->value;
    }
    throw DeviceError("Sensor not found: " + port_);
}

void changeValveState(const string& port_, bool state_)
{
    lock_guard<mutex> lock(device_mutex);
    
    auto it = find_if(valves.begin(), valves.end(),
                     [&port_](const Valve& v) { return v.port == port_; });
    
    if (it != valves.end()) {
        it->state = state_;
        try {
            setValve(port_, state_ ? it->inputVol : 0.0);
        }
        catch (const std::exception& e) {
            cerr << "Error setting valve " << port_ << ": " << e.what() << endl;
            throw DeviceError(string("Error setting valve: ") + e.what());
        }
    }
    else {
        throw DeviceError("Valve not found: " + port_);
    }
}

string getValues()
{
    lock_guard<mutex> lock(device_mutex);
    stringstream ss;
    
    for (const Sensor& s : sensors) {
        ss << s.port << " " << s.value << ",";
    }
    
    for (const Valve& v : valves) {
        ss << v.port << (v.state ? " Open," : " Closed,");
    }
    
    return ss.str();
}

void cleanup_devices()
{
    lock_guard<mutex> lock(device_mutex);
    valves.clear();
    sensors.clear();
}
