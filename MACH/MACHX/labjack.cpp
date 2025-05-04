#include <iostream>
#include "LabJackM.h"

int err, handle;

void startConnection()
{
    double value = 0;

    const char * NAME = "SERIAL_NUMBER";

    err = LJM_Open(LJM_dtANY, LJM_ctANY, "LJM_idANY", &handle);

    std::cout << err;

    err = LJM_eWriteName(handle, "AIN0_NEGATIVE_CH", 1);

    //std::cout << err;

    err = LJM_eWriteName(handle, "AIN0_RANGE", 0.01);

    //std::cout << err;






    err = LJM_eWriteName(handle, "AIN2_NEGATIVE_CH", 3);

    //std::cout << err;

    err = LJM_eWriteName(handle, "AIN2_RANGE", 0.01);

    //std::cout << err;





    err = LJM_eWriteName(handle, "AIN4_NEGATIVE_CH", 5);

    //std::cout << err;

    err = LJM_eWriteName(handle, "AIN4_RANGE", 0.01);

    //std::cout << err;
}


double sensorFeedback(std::string port)
{
    //THIS PART MAKES IT SO THAT AIN2 AND AIN0 VALUES GET 
    /*
    if(port == "AIN2")
    {
        double voltage;
        double voltage2;
        const char* cstr = port.c_str(); 
       return err = LJM_eReadName(handle, cstr, &voltage);
        std::string port2 = "AIN0";
        cstr = port2.c_str();
        err = LJM_eReadName(handle, cstr, &voltage2);
         (150000/voltage)*voltage2;    
    }
        */
    //THIS PART DOES OTHER PORTS PART

    double voltage;
    const char* cstr = port.c_str(); 
    err = LJM_eReadName(handle, cstr, &voltage);
    return voltage;
    //return 12.09;
}

void setValve(std::string port, double value)
{
    const char* cstr = port.c_str(); 
    err = LJM_eWriteName(handle, cstr, value);

}


void endConnection()
{
    err = LJM_Close(handle);
} 
