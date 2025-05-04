#include <windows.h>
#include <iostream>
#include <unistd.h>

#define memSize 2048
const char* memName = "Local\\MySharedMemory";

char* ReadMemory()
{
    HANDLE handle = OpenFileMapping(
        FILE_MAP_ALL_ACCESS,
        FALSE,
        memName
    );

    if(handle == NULL)
    {
        //std::cerr << "couldent make a map" << GetLastError() << std::endl;
        char* result = (char*)"P";
        return result;
    }    

    char* pBuffer = (char*)MapViewOfFile(
        handle,
        FILE_MAP_ALL_ACCESS,
        0, 0, memSize
    );

    if(pBuffer == NULL)
    {
        //std::cerr << "could not map view of file " << GetLastError() << std::endl;
        CloseHandle(handle);
        char* result = (char*)"P";
        return result;
    }

    WaitForSingleObject(handle, INFINITE);

    char* result = new char[memSize];
    memcpy(result, pBuffer, memSize);    

    UnmapViewOfFile(pBuffer);
    CloseHandle(handle);

    return result;
}

void WriteMemory(char* input, bool re)
{
    //std::cout << "legendary";
    HANDLE handle = CreateFileMapping(
                        INVALID_HANDLE_VALUE,
                        NULL,
                        PAGE_READWRITE,
                        0, memSize,
                        memName
    );
    

    if(handle == NULL)
    {
        //std::cerr << "couldent make a map" << GetLastError() << std::endl;
    }    

    char* pBuffer = (char*)MapViewOfFile(
        handle,
        FILE_MAP_ALL_ACCESS,
        0, 0, memSize
    );

    

    if(pBuffer == NULL)
    {
        //std::cerr << "could not map view of file " << GetLastError() << std::endl;
        CloseHandle(handle);
    }

    memset(pBuffer, 0, memSize);

    strncpy(pBuffer, input, memSize - 1);
    pBuffer[memSize - 1] = '\0';

    

    UnmapViewOfFile(pBuffer);

    int counter = 0;
    while(ReadMemory()[0] != "L"[0] && re == true && counter <= 10000){
        //std::cout << "im real";
        counter += 1;
    }

    //std::cout << "legend";

    //sleep(0.0001f);

    CloseHandle(handle);

}


