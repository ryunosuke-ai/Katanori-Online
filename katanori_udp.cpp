//compile: "g++ katanori_udp.cpp -lws2_32" (to use socket communication)

#include <iostream>
#include <WinSock2.h>
#include <sstream>
#include <signal.h>
#include <stdlib.h>

/*
#include "include/gs2d_robotis.h"
#include "include/gs2d_krs.h"
#include "include/gs2d_b3m.h"
*/
#include "gs2d-cpp/gs2d/gs2d_futaba.h"
#include "gs2d-cpp/samples/windows/WindowsSerial.h"

#pragma comment(lib, "ws2_32.lib")

#define NUM_SERVO 6
#define BUFFER_MAX 256

using namespace gs2d;

void burstReadCallback(CallbackEventArgs arg);
void enableServo(Driver* servo, uint8_t id);
void enableAllServo(Driver* servo);
void disableAllServo(Driver* servo);
void myQuit(int signum);

Driver* servo;

int main()
{
    WSAData wsaData;

    uint8_t id = 1;
    uint8_t idList[NUM_SERVO] = {1, 2, 3, 4, 5, 6};
    gFloat positionList[NUM_SERVO];
    SOCKET sock;
    struct sockaddr_in addr;

    char buf[BUFFER_MAX];
    std::string str;
    std::stringstream ss;

    servo = new Futaba<gs2d::WindowsSerial>();

    WSAStartup(MAKEWORD(2, 0), &wsaData);
    
    int port;
    std::cout << "PORT: ";
    std::cin >> port;

    sock = socket(AF_INET, SOCK_DGRAM, 0);
    addr.sin_family = AF_INET;
    // addr.sin_addr.s_addr = inet_addr(ADDRESS);
    addr.sin_addr.S_un.S_addr = INADDR_ANY;
    addr.sin_port = htons(port);

    bind(sock, (const struct sockaddr *)&addr, sizeof(addr));

    enableAllServo(servo);
    // servo->changeOperatingMode(true);  //これするとreadCurrentPositionができなくなる（isTrafficFreeがfalseになってるまま？boolでの制御（これだと「終わったらfalse」にできない）じゃなくてtrafficが何台か記録、都度増減（終わったら-1）がよい？）

    // Ctrl+cでサーボをオフにしてから終了するようにする（myQuit関数を呼び出す）
    signal(SIGINT, myQuit);

    while (true) {
        // "0,0,-50,0,0,0"のような形の文字列（各サーボ値）を受け取る
        memset(buf, 0, sizeof(buf));
        recv(sock, buf, sizeof(buf), 0);
        str = buf;
        std::cout << "received: " << str << std::endl; 

        if (str == "quit") {
            break;
        }

        // stringstreamにstrを追加する
        ss << str;

        // positionListに各サーボ値を格納
        std::cout << "{";
        for (int i = 0; i < NUM_SERVO; i++) {
            std::getline(ss, str, ',');
            positionList[i] = std::stof(str);
            std::cout << std::stof(str) << ",";
        }
        std::cout << "}" << std::endl;

        // stringstreamを空にする 
        ss.str(""); // バッファをクリアする。
        ss.clear(std::stringstream::goodbit); // ストリームの状態をクリアする。この行がないと意図通りに動作しない

        // すべてのサーボを同時に動かす
        std::cout << "Burst Position Write : " << std::endl << std::endl; servo->burstWriteTargetPositions(idList, positionList, NUM_SERVO);
        Sleep(10);

    }

    disableAllServo(servo);
}


void burstReadCallback(CallbackEventArgs arg)
{
    std::cout << "Burst Read Result -> id:" << (int)arg.id << ", position:" << (gFloat)arg.data << std::endl;
}

void enableServo(Driver* servo, uint8_t id)
{
    std::cout << "ID: " << (int)id << std::endl;

    // Ping
    std::cout << "Ping : " << (int)servo->ping(id) << std::endl;

    // Offset
    //電圧？
    std::cout << "Offset Write : " << std::endl; servo->writeOffset(id, 3.0);
    //std::cout << "Offset Read : " << servo->readOffset(id) << std::endl;

    // Deadband
    // 不感帯？
    std::cout << "Deadband Write : " << std::endl; servo->writeDeadband(id, 3.0);
    //std::cout << "Deadband Read : " << servo->readDeadband(id) << std::endl;

    // P Gain
    std::cout << "PGain Write : " << std::endl; servo->writePGain(id, 800);
    //std::cout << "PGain Read : " << servo->readPGain(id) << std::endl;

    // I Gain 
    std::cout << "IGain Write : " << std::endl; servo->writeIGain(id, 400);
    //std::cout << "IGain Read : " << servo->readIGain(id) << std::endl;

    // D Gain 
    std::cout << "DGain Write : " << std::endl; servo->writeDGain(id, 300);
    //std::cout << "DGain Read : " << servo->readDGain(id) << std::endl;

    // Max Torque
    std::cout << "MaxTorque Write : " << std::endl; servo->writeMaxTorque(id, 80);
    //std::cout << "MaxTorque Read : " << servo->readMaxTorque(id) << std::endl;

    // ROM
    //std::cout << "Save ROM : " << std::endl; servo->saveRom(id);
    //std::cout << "Load ROM : " << std::endl; servo->loadRom(id);
    //std::cout << "ResetMemory : " << std::endl; servo->resetMemory(id);

    //Sleep(1000);

    // Baudrate
    std::cout << "Baudrate Write : " << std::endl; servo->writeBaudrate(id, 115200);
    //std::cout << "Baudrate Read : " << servo->readBaudrate(id) << std::endl;

    // CW Limit
    std::cout << "CW Limit Write : " << std::endl; servo->writeLimitCWPosition(id, -135);
    //std::cout << "CW Limit Read : " << servo->readLimitCWPosition(id) << std::endl;

    // CCW Limit
    std::cout << "CCW Limit Write : " << std::endl; servo->writeLimitCCWPosition(id, 135);
    //std::cout << "CCW Limit Read : " << servo->readLimitCCWPosition(id) << std::endl;

    // Temperature Limit
    std::cout << "Temperature Limit Write : " << std::endl; servo->writeLimitTemperature(id, 70);
    //std::cout << "Temperature Limit Read : " << servo->readLimitTemperature(id) << std::endl;

    // Current Limit
    std::cout << "Current Limit Write : " << std::endl; servo->writeLimitCurrent(id, 5000);
    //std::cout << "Current Limit Read : " << servo->readLimitCurrent(id) << std::endl;

    // Drive Mode
    std::cout << "Drive Mode Write : " << std::endl; servo->writeDriveMode(id, 4);
    //std::cout << "Drive Mode Read : " << servo->readDriveMode(id) << std::endl;

    // Torque Enable
    std::cout << "Torque Enable Write : " << std::endl; servo->writeTorqueEnable(id, 1);
    std::cout << "Torque Enable Read : " << (int)servo->readTorqueEnable(id) << std::endl;

    // Temperature
    //std::cout << "Temperature Read : " << servo->readTemperature(id) << std::endl;

    // Current
    //std::cout << "Current Read : " << servo->readCurrent(id) << std::endl;

    // Voltage
    //std::cout << "Voltage Read : " << servo->readVoltage(id) << std::endl;

    // Speed
    std::cout << "Speed Write : " << std::endl; servo->writeSpeed(id, 100);
    //std::cout << "Speed Read : " << servo->readSpeed(id) << std::endl;

    // Accel Time
    std::cout << "Accel Time Write : " << std::endl; servo->writeAccelTime(id, 0.2);
    //std::cout << "Accel Time Read : " << servo->readAccelTime(id) << std::endl;

    // Target Time
    std::cout << "Target Time Write : " << std::endl; servo->writeTargetTime(id, 0);
    //std::cout << "Target Time Read : " << servo->readTargetTime(id) << std::endl; 
}

void enableAllServo(Driver* servo)
{
    for (uint8_t id=1; id<=NUM_SERVO; id++) {
        enableServo(servo, id);
    }
}

void disableAllServo(Driver* servo)
{
    for (uint8_t id=1; id<=NUM_SERVO; id++) {
        // Torque Disable
        std::cout << "ID : " << (int)id << std::endl;
        std::cout << "Torque Enable Write : " << std::endl; servo->writeTorqueEnable(id, 0);
        std::cout << "Torque Enable Read : " << (int)servo->readTorqueEnable(id) << std::endl;
    }
}

void myQuit(int signum)
{
    disableAllServo(servo);
    exit(0);
}