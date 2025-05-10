#ifndef SERVERCOMMS_H
#define SERVERCOMMS_H

#include <string>
#include <stdexcept>

// Custom exception for memory operations
class MemoryError : public std::runtime_error {
public:
    explicit MemoryError(const std::string& message) : std::runtime_error(message) {}
};

// Constants
constexpr size_t MEMORY_SIZE = 2048;
constexpr const char* MEMORY_NAME = "Local\\MySharedMemory";
constexpr int MEMORY_WAIT_TIMEOUT = 10000;

// Memory operations
void WriteMemory(const char* input, bool wait_for_response);
char* ReadMemory();

#endif