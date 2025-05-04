package main

import (
	"log"
	"net"

	"machnet/relay"

	"google.golang.org/grpc"
)

func main() {
	lis, err := net.Listen("tcp", "DESKTOP-K4SS8OO:9000")
	if err != nil {
		log.Fatalf("failed to connect", err)
	}

	s := relay.Server{}

	grpcServer := grpc.NewServer()

	relay.RegisterRelayServiceServer(grpcServer, &s)

	if err := grpcServer.Serve(lis); err != nil {
		log.Fatalf("failed to: ", err)
	}
}
