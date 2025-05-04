#include <iostream>
#include "LabJackM.h"
//g++ main.cpp deviceManager.cpp labjack.cpp labjack.hpp deviceManager.hpp  -o labjack_test.exe -I"C:\Program Files (x86)\LabJack\Drivers" -L"C:\Program Files (x86)\LabJack\Drivers" -lLabJackM

using namespace std;

int main()
{
    cout << "test";
    int err, handle;
	double value = 0;

	const char * NAME = "SERIAL_NUMBER";

    err = LJM_Open(LJM_dtANY, LJM_ctANY, "LJM_idANY", &handle);

    err = LJM_Close(handle);
}