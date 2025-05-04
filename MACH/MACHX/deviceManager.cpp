#include <iostream>
#include "deviceManager.hpp"
#include "labjack.hpp"

using namespace std;

//for sensors init
// sP320.0000010.00000.000001000.00 

//for valves init
//vV3602.2

int buffer = 7;
int bufferValve = 3;

vector<Valve> valves;
vector<Sensor> sensors;

void create_device(string input)
{
    if(input.substr(0,1) == "s")
    {
        bool create = true;
        for(Sensor& s : sensors)
        {
            if(s.port == input.substr(1,4))
            {
                create = false;
                s.port = input.substr(1,4);            
                s.minVol = stod(input.substr(4,buffer));
                s.maxVol = stod(input.substr(4+buffer,buffer));
                s.minReading = stod(input.substr(4+buffer+buffer, buffer));
                s.maxReading = stod(input.substr(4+buffer+buffer+buffer, buffer));
            }
        }

        if (create == true)
        {
            Sensor newSensor = Sensor();
            newSensor.port = input.substr(1,4);            
            newSensor.minVol = stod(input.substr(4,buffer));
            newSensor.maxVol = stod(input.substr(4+buffer,buffer));
            newSensor.minReading = stod(input.substr(4+buffer+buffer, buffer));
            newSensor.maxReading = stod(input.substr(4+buffer+buffer+buffer, buffer));
            sensors.push_back(newSensor);
        }
        
        //cout << input.substr(1,4);
    }
    else if(input.substr(0,1) == "v")
    {
        //cout << input.substr(1,4);

        bool create = true;
        for(Valve& v : valves)
        {
            if(v.port == input.substr(1,4))
            {
                create = false;
                v.port = input.substr(1,4);
                if(stoi(input.substr(5,1)) == 1)
                {
                    v.state = 1;
                }
                else
                {
                    v.state = 0;
                }

                v.inputVol = stod(input.substr(6,bufferValve));
            }
        }
        if (create == true)
        {
            Valve newValve = Valve();
            newValve.port = input.substr(1,4);

            //cout << input.substr(4,1);

            if(stoi(input.substr(5,1)) == 1)
            {
                newValve.state = 1;
            }
            else
            {
                newValve.state = 0;
            }

            newValve.inputVol = stod(input.substr(6,bufferValve));

            valves.push_back(newValve);
        }
        
    }
}

void updateSensorValue()
{
    for(Sensor& s : sensors)
    {

        s.value = sensorFeedback(s.port) * s.maxReading;

    }
}

double getSensorValue(string port_)
{
    //double val = sensorFeedback(port_);

    for(Sensor& s : sensors)
    {
        if(s.port == port_)
        {
            return s.value;
            //val = val * s.maxReading;
        }
    }
}

void changeValveState(string port_, bool state_)
{  
    for(Valve& v : valves)
    {
        if(v.port == port_)
        {
            //cout << "heyop";
            v.state = state_;
            if(v.state == true)
            {
                //cout << "heyo";
                setValve(port_, v.inputVol);
            }
            else
            {
                //cout << "heyo";
                setValve(port_, 0);
            }
        }
        
    }
}

string getValues()
{
    string full = "";
    for(Sensor s : sensors)
    {
        full += string(s.port);
        double val;

        
        //double scale = (s.maxReading-s.minReading)/(s.maxVol-s.minVol);
        //double offset = -s.minVol*(s.maxReading-s.minReading)/(s.maxVol-s.minVol) + s.minReading;
        //val = s.value*scale + offset;
        val = s.value;
        full += " " + to_string(val)+ ","; 
    }
    for(Valve v : valves)
    {
        full += string(v.port);
        if(v.state == true)
        {
            full += " Open,";
        }
        else
        {
            full += " Closed,";
        }
    }
    return full;
}
