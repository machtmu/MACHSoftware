package comm_share

import (
	"fmt"
	"syscall"
	"unsafe"
)



func readMem() string {
	kernel32 := syscall.NewLazyDLL("kernel32.dll")
	openFileMapping := kernel32.NewProc("OpenFileMappingW")
	mapViewOfFile := kernel32.NewProc("MapViewOfFile")
	unmapViewOfFile := kernel32.NewProc("UnmapViewOfFile")
	closeHandle := kernel32.NewProc("CloseHandle")

	handle, _, _ := openFileMapping.Call(
		uintptr(0xF001F),
		0,
		uintptr(unsafe.Pointer(syscall.StringToUTF16Ptr(memName))),
	)

	if handle == 0 {
		fmt.Println("couldent open file mapping")
		return ""
	}
	defer closeHandle.Call(handle)

	pBuffer, _, _ := mapViewOfFile.Call(
		handle,
		0xF001F,
		0, 0, memSize,
	)

	if pBuffer == 0 {
		fmt.Println("could not map view")
		return ""
	}
	defer unmapViewOfFile.Call(pBuffer)

	data := (*[memSize]byte)(unsafe.Pointer(pBuffer))

	str := string(data[:])
	return str

}

func WriteMem(input string) {
	kernel32 := syscall.NewLazyDLL("kernel32.dll")
	openFileMapping := kernel32.NewProc("OpenFileMappingW")
	mapViewOfFile := kernel32.NewProc("MapViewOfFile")
	unmapViewOfFile := kernel32.NewProc("UnmapViewOfFile")
	closeHandle := kernel32.NewProc("CloseHandle")

	handle, _, _ := openFileMapping.Call(
		uintptr(0xF001F),
		0,
		uintptr(unsafe.Pointer(syscall.StringToUTF16Ptr(memName))),
	)

	if handle == 0 {
		fmt.Println("couldent open file mapping")
	}
	defer closeHandle.Call(handle)

	pBuffer, _, _ := mapViewOfFile.Call(
		handle,
		0xF001F,
		0, 0, memSize,
	)

	if pBuffer == 0 {
		fmt.Println("could not map view")
	}
	defer unmapViewOfFile.Call(pBuffer)

	data := []byte(input)

	if len(data) > memSize {
		data = data[:memSize]
	}

	copy((*[memSize]byte)(unsafe.Pointer(pBuffer))[:], data)
}

func main() {
}
