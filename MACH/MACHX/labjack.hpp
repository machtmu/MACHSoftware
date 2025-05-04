#ifndef LABJACK_H
#define LABJACK_H

#include <string>

void startConnection();

void endConnection();

double sensorFeedback(std::string port);

void setValve(std::string port, double value);

#endif