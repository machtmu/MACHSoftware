// Code generated by protoc-gen-go-grpc. DO NOT EDIT.
// versions:
// - protoc-gen-go-grpc v1.5.1
// - protoc             v5.29.1
// source: relay.proto

package relay

import (
	context "context"
	grpc "google.golang.org/grpc"
	codes "google.golang.org/grpc/codes"
	status "google.golang.org/grpc/status"
)

// This is a compile-time assertion to ensure that this generated file
// is compatible with the grpc package it is being compiled against.
// Requires gRPC-Go v1.64.0 or later.
const _ = grpc.SupportPackageIsVersion9

const (
	RelayService_RelayData_FullMethodName = "/relay.RelayService/RelayData"
)

// RelayServiceClient is the client API for RelayService service.
//
// For semantics around ctx use and closing/ending streaming RPCs, please refer to https://pkg.go.dev/google.golang.org/grpc/?tab=doc#ClientConn.NewStream.
type RelayServiceClient interface {
	RelayData(ctx context.Context, in *Message, opts ...grpc.CallOption) (*Message, error)
}

type relayServiceClient struct {
	cc grpc.ClientConnInterface
}

func NewRelayServiceClient(cc grpc.ClientConnInterface) RelayServiceClient {
	return &relayServiceClient{cc}
}

func (c *relayServiceClient) RelayData(ctx context.Context, in *Message, opts ...grpc.CallOption) (*Message, error) {
	cOpts := append([]grpc.CallOption{grpc.StaticMethod()}, opts...)
	out := new(Message)
	err := c.cc.Invoke(ctx, RelayService_RelayData_FullMethodName, in, out, cOpts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

// RelayServiceServer is the server API for RelayService service.
// All implementations must embed UnimplementedRelayServiceServer
// for forward compatibility.
type RelayServiceServer interface {
	RelayData(context.Context, *Message) (*Message, error)
	mustEmbedUnimplementedRelayServiceServer()
}

// UnimplementedRelayServiceServer must be embedded to have
// forward compatible implementations.
//
// NOTE: this should be embedded by value instead of pointer to avoid a nil
// pointer dereference when methods are called.
type UnimplementedRelayServiceServer struct{}

func (UnimplementedRelayServiceServer) RelayData(context.Context, *Message) (*Message, error) {
	return nil, status.Errorf(codes.Unimplemented, "method RelayData not implemented")
}
func (UnimplementedRelayServiceServer) mustEmbedUnimplementedRelayServiceServer() {}
func (UnimplementedRelayServiceServer) testEmbeddedByValue()                      {}

// UnsafeRelayServiceServer may be embedded to opt out of forward compatibility for this service.
// Use of this interface is not recommended, as added methods to RelayServiceServer will
// result in compilation errors.
type UnsafeRelayServiceServer interface {
	mustEmbedUnimplementedRelayServiceServer()
}

func RegisterRelayServiceServer(s grpc.ServiceRegistrar, srv RelayServiceServer) {
	// If the following call pancis, it indicates UnimplementedRelayServiceServer was
	// embedded by pointer and is nil.  This will cause panics if an
	// unimplemented method is ever invoked, so we test this at initialization
	// time to prevent it from happening at runtime later due to I/O.
	if t, ok := srv.(interface{ testEmbeddedByValue() }); ok {
		t.testEmbeddedByValue()
	}
	s.RegisterService(&RelayService_ServiceDesc, srv)
}

func _RelayService_RelayData_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(Message)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(RelayServiceServer).RelayData(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: RelayService_RelayData_FullMethodName,
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(RelayServiceServer).RelayData(ctx, req.(*Message))
	}
	return interceptor(ctx, in, info, handler)
}

// RelayService_ServiceDesc is the grpc.ServiceDesc for RelayService service.
// It's only intended for direct use with grpc.RegisterService,
// and not to be introspected or modified (even as a copy)
var RelayService_ServiceDesc = grpc.ServiceDesc{
	ServiceName: "relay.RelayService",
	HandlerType: (*RelayServiceServer)(nil),
	Methods: []grpc.MethodDesc{
		{
			MethodName: "RelayData",
			Handler:    _RelayService_RelayData_Handler,
		},
	},
	Streams:  []grpc.StreamDesc{},
	Metadata: "relay.proto",
}
