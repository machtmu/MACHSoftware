//For compilation
//g++ main.cpp deviceManager.cpp labjack.cpp labjack.hpp deviceManager.hpp ServerComms.hpp ServerComms.cpp  -o labjack_test.exe -I"C:\Program Files (x86)\LabJack\Drivers" -L"C:\Program Files (x86)\LabJack\Drivers" -lLabJackM
#include <iostream>
#include <fstream>
#include <windows.h>
#include <unistd.h>
#include <ctime>
#include <chrono>
#include <thread>
#include <atomic>
#include <memory>
#include <string>
#include <vector>
#include <mutex>
#include "deviceManager.hpp"
#include "labjack.hpp"
#include "ServerComms.hpp"

using namespace std;

// Constants
constexpr int MAX_RECORDING_BUFFER = 1000;
constexpr int MEMORY_WAIT_TIMEOUT = 10000;
constexpr int UPDATE_INTERVAL_MS = 10;

// Global state
atomic<bool> g_running{true};
atomic<bool> g_recording{false};
string g_filename = "Dat_";
vector<string> g_recording_buffer;
mutex g_recording_mutex;
ofstream g_data_record;
HANDLE g_update_thread = nullptr;
HANDLE g_record_thread = nullptr;

// Thread functions
DWORD WINAPI UpdateThread(LPVOID lpParam) {
    while (g_running) {
        try {
            updateSensorValue();
            this_thread::sleep_for(chrono::milliseconds(UPDATE_INTERVAL_MS));
        }
        catch (const exception& e) {
            cerr << "Error in update thread: " << e.what() << endl;
        }
    }
    return 0;
}

DWORD WINAPI RecordThread(LPVOID lpParam) {
    while (g_recording) {
        try {
            lock_guard<mutex> lock(g_recording_mutex);
            
            if (g_recording_buffer.size() >= MAX_RECORDING_BUFFER) {
                for (const auto& data : g_recording_buffer) {
                    g_data_record << data;
                }
                g_recording_buffer.clear();
            }

            time_t now = time(nullptr);
            string time_str = ctime(&now);
            time_str.erase(time_str.find('\n'));

            string data = time_str + "," + getValues() + "\n";
            g_recording_buffer.push_back(data);
        }
        catch (const exception& e) {
            cerr << "Error in record thread: " << e.what() << endl;
        }
    }
    return 0;
}

// Helper functions
void StartRecording() {
    if (g_recording) return;

    g_recording = true;
    g_data_record.open(g_filename + ".csv");
    if (!g_data_record.is_open()) {
        throw runtime_error("Failed to open recording file");
    }

    g_record_thread = CreateThread(nullptr, 0, RecordThread, nullptr, 0, nullptr);
    if (!g_record_thread) {
        g_recording = false;
        g_data_record.close();
        throw runtime_error("Failed to create record thread");
    }
}

void StopRecording() {
    if (!g_recording) return;

    g_recording = false;
    
    {
        lock_guard<mutex> lock(g_recording_mutex);
        for (const auto& data : g_recording_buffer) {
            g_data_record << data;
        }
        g_recording_buffer.clear();
    }

    g_data_record.close();
    g_data_record.clear();

    if (g_record_thread) {
        WaitForSingleObject(g_record_thread, INFINITE);
        CloseHandle(g_record_thread);
        g_record_thread = nullptr;
    }

    g_filename += "0";
}

void ProcessCommand(const string& command) {
    if (command.empty()) return;

    try {
        switch (command[0]) {
            case 'm': // Create device
                create_device(command.substr(1));
                WriteMemory(const_cast<char*>("P"), false);
                break;

            case 'r': // Read sensor
                if (command.length() >= 6) {
                    double value = getSensorValue(command.substr(2, 4));
                    string response = command.substr(1, 5) + to_string(value);
                    WriteMemory(const_cast<char*>(response.c_str()), true);
                }
                break;

            case 'w': // Write valve state
                if (command.length() >= 6) {
                    bool state = (command.substr(5, 1) == "1");
                    changeValveState(command.substr(1, 4), state);
                    WriteMemory(const_cast<char*>("P"), false);
                }
                break;

            default:
                if (command == "Rec") {
                    StartRecording();
                    WriteMemory(const_cast<char*>("P"), false);
                }
                else if (command == "End") {
                    StopRecording();
                    WriteMemory(const_cast<char*>("P"), false);
                }
                break;
        }
    }
    catch (const exception& e) {
        cerr << "Error processing command: " << e.what() << endl;
        WriteMemory(const_cast<char*>("E"), false);
    }
}

int main() {
    try {
        startConnection();

        g_update_thread = CreateThread(nullptr, 0, UpdateThread, nullptr, 0, nullptr);
        if (!g_update_thread) {
            throw runtime_error("Failed to create update thread");
        }

        while (g_running) {
            char* stream_read = ReadMemory();
            if (stream_read && stream_read[0] != 'P') {
                ProcessCommand(string(stream_read));
            }
            delete[] stream_read;
        }

        // Cleanup
        if (g_recording) {
            StopRecording();
        }

        if (g_update_thread) {
            WaitForSingleObject(g_update_thread, INFINITE);
            CloseHandle(g_update_thread);
        }

        cleanup_devices();
        endConnection();
    }
    catch (const exception& e) {
        cerr << "Fatal error: " << e.what() << endl;
        return 1;
    }

    return 0;
}