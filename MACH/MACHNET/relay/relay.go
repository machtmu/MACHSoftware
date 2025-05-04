package relay

import (
	"fmt"
	"log"
	"syscall"
	"time"
	"unsafe"

	"golang.org/x/net/context"
)

const memSize = 2048
const memName = "Local\\MySharedMemory"

type Server struct {
	UnimplementedRelayServiceServer
}

func (s *Server) RelayData(ctx context.Context, message *Message) (*Message, error) {
	if string(message.Body[0]) == "m" || string(message.Body[0]) == "w" {
		WriteMem(message.Body)
	} else if string(message.Body[0]) == "r" {
		WriteMem(message.Body)
		//time.Sleep(1 * time.Microsecond)
		//streamRead := readMem()
		/*
			for {
				if len(streamRead) != 0 {
					if streamRead[0] != "r"[0] {
						//log.Printf("BROOOO")
						break
					}
				}
				streamRead := readMem()
				if len(streamRead) != 0 {
					if streamRead[0] != "r"[0] {
						//log.Printf(string(streamRead))
						break
					}
				}
			}
		*/
		ellanor := "booya"
		for {
			streamRead := readMem()
			log.Println("yessir")
			if len(streamRead) != 0 {
				if streamRead[0] == "s"[0] {
					ellanor = string(streamRead)
					//log.Println(string(streamRead))
					//log.Println("yessir")
					break
				}
			}

			//log.Println(streamRead)
		}
		WriteMem("L")
		//time.Sleep(1 * time.Microsecond)
		//log.Println(string(streamRead))
		//log.Printf("heyya")
		return &Message{Body: ellanor}, nil
	} else if string(message.Body) == "Rec" || string(message.Body) == "End" {
		log.Printf("haha fuck you")
		WriteMem(message.Body)
	}
	log.Printf("you recived message from: %s", message.Body)
	return &Message{Body: ""}, nil
}

func readMem() string {
	//const INFINITE = 0xFFFFFFFF
	kernel32 := syscall.NewLazyDLL("kernel32.dll")
	openFileMapping := kernel32.NewProc("OpenFileMappingW")
	mapViewOfFile := kernel32.NewProc("MapViewOfFile")
	unmapViewOfFile := kernel32.NewProc("UnmapViewOfFile")
	closeHandle := kernel32.NewProc("CloseHandle")
	//procWaitForSingleObject := kernel32.NewProc("WaitForSingleObject")

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

	/*
		ret, _, _ := procWaitForSingleObject.Call(uintptr(handle), uintptr(INFINITE))

		if ret == 0 {
			fmt.Println("Event signaled!")
		} else {
			fmt.Println("Wait failed with return code:", ret)
		}
	*/

	data := (*[memSize]byte)(unsafe.Pointer(pBuffer))

	str := string(data[:])
	return str

}

func WriteMem(input string) {
	kernel32 := syscall.NewLazyDLL("kernel32.dll")
	createFileMapping := kernel32.NewProc("CreateFileMappingW")
	unmapViewOfFile := kernel32.NewProc("UnmapViewOfFile")
	mapViewOfFile := kernel32.NewProc("MapViewOfFile")
	closeHandle := kernel32.NewProc("CloseHandle")

	handle, _, _ := createFileMapping.Call(
		0xFFFFFFFFFFFFFFFF, // INVALID_HANDLE_VALUE (page file-backed mapping)
		0,
		0x04, // PAGE_READWRITE
		0,
		memSize,
		uintptr(unsafe.Pointer(syscall.StringToUTF16Ptr(memName))),
	)

	if handle == 0 {
		fmt.Println("couldent open file mapping")
	}

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

	time.Sleep(1 * time.Microsecond)
	closeHandle.Call(handle)
}
