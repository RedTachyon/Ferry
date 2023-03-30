#python -m grpc_tools.protoc -I./ferry/protos/ --python_out=./ferry/ --pyi_out=./ferry/ --csharp_out=./ferry/ ./ferry/protos/gym_grpc/gym.proto
#protoc -I./ferry/protos/ --python_out=./ferry/ --pyi_out=./ferry/ --csharp_out=./FerryEnv/Assets/ ./ferry/protos/gym_grpc/gym.proto

protoc -I./protos/ --python_out=./ferry/ --pyi_out=./ferry/ --rust_out ./ferry-rs/src/ ./protos/gym_grpc/gym_ferry.proto

#python -m grpc_tools.protoc -I./ferry/protos/ --python_out=./ferry/ --pyi_out=./ferry/ --grpc_python_out=./ferry/ ./ferry/protos/gym_grpc/gym.proto
#protoc -I./ferry/protos/ --python_out=./ferry/ ./ferry/protos/gym_grpc/gym.proto

