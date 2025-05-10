#include <windows.h>
#include <iostream>
#include <string>
#include <memory>
#include "ServerComms.hpp"

using namespace std;

#define memSize 2048
const char* memName = "Local\\MySharedMemory";

// RAII wrapper for Windows handles
class HandleGuard {
public:
    explicit HandleGuard(HANDLE h) : handle(h) {}
    ~HandleGuard() { if (handle) CloseHandle(handle); }
    HANDLE get() const { return handle; }
private:
    HANDLE handle;
};

// RAII wrapper for memory mapping
class MemoryGuard {
public:
    explicit MemoryGuard(HANDLE h) : handle(h), buffer(nullptr) {
        buffer = MapViewOfFile(handle, FILE_MAP_ALL_ACCESS, 0, 0, memSize);
        if (!buffer) {
            throw MemoryError("Failed to map view of file: " + to_string(GetLastError()));
        }
    }
    ~MemoryGuard() { if (buffer) UnmapViewOfFile(buffer); }
    char* get() const { return buffer; }
private:
    HANDLE handle;
    char* buffer;
};

char* ReadMemory()
{
    try {
        HandleGuard handle(OpenFileMapping(
            FILE_MAP_ALL_ACCESS,
            FALSE,
            memName
        ));
        if (!handle.get()) {
            return new char[1]{'P'};
        }    

        MemoryGuard memory(handle.get());
        char* result = new char[memSize];
        memcpy(result, memory.get(), memSize);    

        return result;
    }
    catch (const exception& e) {
        cerr << "Error reading memory: " << e.what() << endl;
        return new char[1]{'P'};
    }
}

void WriteMemory(const char* input, bool wait_for_response)
{
    if (!input) {
        throw MemoryError("Null input pointer");
    }

    try {
        HandleGuard handle(CreateFileMapping(
            INVALID_HANDLE_VALUE,
            NULL,
            PAGE_READWRITE,
            0, memSize,
            memName
        ));
        
        if (!handle.get()) {
            throw MemoryError("Failed to create file mapping: " + to_string(GetLastError()));
        }    

        MemoryGuard memory(handle.get());
        memset(memory.get(), 0, memSize);
        strncpy(memory.get(), input, memSize - 1);
        memory.get()[memSize - 1] = '\0';

        if (wait_for_response) {
            int counter = 0;
            while (counter < 10000) {
                char* response = ReadMemory();
                if (response[0] == 'L') {
                    delete[] response;
                    break;
                }
                delete[] response;
                counter++;
            }
        }
    }
    catch (const exception& e) {
        cerr << "Error writing memory: " << e.what() << endl;
        throw;
    }
}


