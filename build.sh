#python -m grpc_tools.protoc -I./ferry/protos/ --python_out=./ferry/ --pyi_out=./ferry/ --csharp_out=./ferry/ ./ferry/protos/gym_grpc/gym.proto
protoc -I./ferry/protos/ --python_out=./ferry/ --pyi_out=./ferry/ --csharp_out=./FerryEnv/Assets/ ./ferry/protos/gym_grpc/gym.proto


#python -m grpc_tools.protoc -I./ferry/protos/ --python_out=./ferry/ --pyi_out=./ferry/ --grpc_python_out=./ferry/ ./ferry/protos/gym_grpc/gym.proto
#protoc -I./ferry/protos/ --python_out=./ferry/ ./ferry/protos/gym_grpc/gym.proto

