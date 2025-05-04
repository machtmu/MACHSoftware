import grpc
import relay_pb2, relay_pb2_grpc

def main():
    channel = grpc.insecure_channel('localhost:9000')
    client = relay_pb2_grpc.RelayServiceStub(channel)

    message = relay_pb2.Message(
        body="mvFIO103.3"
    )
    
    try:
        response = client.RelayData(message)
        print(f"Response from server: {response.body}")
    except grpc.RpcError as e:
        print(f"Error when calling RelayData: {e}")

if __name__ == "__main__":
    main()
