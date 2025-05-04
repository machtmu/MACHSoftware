#include <windows.h>
#include <iostream>

bool fuck = false;

DWORD WINAPI MyThreadFunction(LPVOID lpParam) {
    while(fuck == true)
    {
        std::cout << "Thread running\n";
    }
    
    return 0;
}

int main() {
    HANDLE hThread = CreateThread(NULL, 0, MyThreadFunction, NULL, 0, NULL);
    fuck = true;
    

    for(int i = 0; i <= 1000000000; i++)
    {
        std::cout << "bro";
    }
    fuck = false;
    CloseHandle(hThread);
    if (hThread) {
        WaitForSingleObject(hThread, INFINITE);
        CloseHandle(hThread);
    }
    return 0;
}