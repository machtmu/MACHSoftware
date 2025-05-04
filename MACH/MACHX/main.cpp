//For compilation
//g++ main.cpp deviceManager.cpp labjack.cpp labjack.hpp deviceManager.hpp ServerComms.hpp ServerComms.cpp  -o labjack_test.exe -I"C:\Program Files (x86)\LabJack\Drivers" -L"C:\Program Files (x86)\LabJack\Drivers" -lLabJackM
#include <iostream>
#include <fstream>
#include <windows.h>
#include <unistd.h>
#include <ctime>
#include "deviceManager.hpp"
#include "labjack.hpp"
#include "ServerComms.hpp"
#include <chrono>
#include <thread>

using namespace std;


string input = "";

char* em = (char*)"P";

vector<string> recordingData;

int instructionLimit = 1;

bool recstate = false;

bool fuck = true;

double duration = 0;

int counter_rec = 0;

string fileName = "Dat_"; 

ofstream DataRecord;

HANDLE hThread;

HANDLE hThread2;

DWORD WINAPI update(LPVOID lpParam) {
    while(fuck == true)
    {
        updateSensorValue();
    }
    return 0;
}

DWORD WINAPI record(LPVOID lpParam) {
    //cout << "hey BOI";
    while(recstate == true)
    {
        
        if (recordingData.size() >= instructionLimit)
        {
            
            for (string ins : recordingData) {
                
                DataRecord << ins;
                //cout << ins;
            } 
            recordingData.clear();

            
        }
        time_t timestamp;
        time(&timestamp);

        time_t now = time(nullptr);  
        std::string timeStr = ctime(&now);  

        timeStr.erase(timeStr.find('\n'));

        getValues();
        
        string dat = string(timeStr) + "," + getValues() + "\n";
        //string dat = "ff";
        recordingData.push_back(dat);
        //cout << "Hey";
    }
    return 0;
}

int main()
{
    startConnection();

    hThread = CreateThread(NULL, 0, update, NULL, 0, NULL);
    
    

    while(fuck == true)
    {
        //clock_t start = clock();
        // Calculate the duration in microseconds
        
        //updateSensorValue();
        char* stream_read = ReadMemory();
        string s(stream_read);

        if(s != "P")
        {
            //cout << s;
        }

        
        
        if(stream_read[0] == "m"[0])
        {
            //cout << "made";
            create_device(s.substr(1,s.length()));
            WriteMemory(em, false);
        }
        else if(stream_read[0] == "r"[0])
        {
            //cout << "read";
            double val = getSensorValue(s.substr(2,4));
            double val_2 = 4.786;
            string val_ = to_string(val);
            string send_back = s.substr(1,5) + val_;
            WriteMemory((char*)send_back.c_str(), true);
            //fuck = false;
        }
        else if(stream_read[0] == "w"[0])
        {
            //cout << s;
            if(s.substr(5,1) == "0")
            {
                changeValveState(s.substr(1,4),false);
                WriteMemory(em, false);
            }
            else
            {
                changeValveState(s.substr(1,4),true);
                WriteMemory(em,false);
            }
        }
        
        if(s == "Rec")
        {
            cout << "holy_one";

            recstate = true;

            DataRecord.open(fileName + ".csv");

            hThread = CreateThread(nullptr, 0, record, nullptr, 0, nullptr);
            
            WriteMemory(em,false);;
        }
        else if(s == "End")
        {
            //cout << "holy";
            recstate = false;
            for (string ins : recordingData) {
                DataRecord << ins;
            }
            recordingData.clear();
            DataRecord.close();
            DataRecord.clear();
            WriteMemory(em,false);
            if (hThread) {
                WaitForSingleObject(hThread, INFINITE);
                CloseHandle(hThread);
            }

            fileName += "0";
            //ofstream DataRecord(fileName + ".csv");
        }

        //clock_t end = clock();

        //double duration = static_cast<double>(end - start) / CLOCKS_PER_SEC * 1000000;

        
        
        
        //sleep(0.000001f);
    }

    //std::cout << "Time passed: " << duration << " microseconds" << std::endl;

    void endConnection();
    return 0;
}