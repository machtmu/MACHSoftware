#ifndef DEVICEMANAGER_H
#define DEVICEMANAGER_H

#include <string>
#include <cstring>
#include <sstream>
#include <vector>

class Valve
{
    public:
        bool state = 0;
        std::string port;
        double inputVol;
};

class Sensor
{
    public:
        double value = 6.6;
        double minVol = 0;
        double maxVol;
        double minReading = 1;
        double maxReading;
        std::string port;
};

void create_device(std::string input);
void updateSensorValue();
std::string getValues();
void changeValveState(std::string port_, bool state_);
double getSensorValue(std::string port_);

#endif