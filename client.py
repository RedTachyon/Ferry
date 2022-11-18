import logging

import grpc
from  ferry.gym_grpc import gym_pb2
from ferry.gym_grpc import gym_pb2_grpc

import numpy as np

logging.basicConfig()



def decode(data: gym_pb2.NumpyArray) -> np.ndarray:
    return np.frombuffer(data.data, dtype=data.dtype).reshape(np.frombuffer(data.shape, dtype=int))


def call_server():
    # seed = gym_pb2.Seed(seed=0)
    options = gym_pb2.Options(params={})
    reset_args = gym_pb2.ResetArgs(seed=0, options=options)
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = gym_pb2_grpc.EnvStub(channel)
        response = stub.Reset(reset_args)
    return decode(response.obs), response.info.params


out = call_server()