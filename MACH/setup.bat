@echo off
echo Downloading and installing Go protobuf and gRPC...

:: Install Go protobuf and gRPC
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest

:: Ensure Go binaries are in PATH
set PATH=%PATH%;%USERPROFILE%\go\bin

echo Installing Python dependencies...
:: Upgrade pip
python -m pip install --upgrade pip

:: Install grpc dependencies
python -m pip install grpcio grpcio-tools

:: Install Tkinter (for Windows, tkinter comes with Python)
python -c "import tkinter" 2>nul && echo Tkinter is already installed || echo Tkinter is included with Python but may require manual installation on some systems.

echo Installation complete.
pause
