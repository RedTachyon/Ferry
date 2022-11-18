import numpy as np
from dataclasses import dataclass


from concurrent import futures
import logging

import grpc
from ferry.gym_grpc import gym_pb2_grpc, gym_pb2

import gymnasium as gym

@dataclass
class EncodedArray:
    data: bytes
    shape: bytes
    dtype: str


def encode(array: np.ndarray) -> gym_pb2.NumpyArray:
    return gym_pb2.NumpyArray(data=array.tobytes(), shape=np.array(array.shape).tobytes(), dtype=str(array.dtype))



class Cartpole(gym_pb2_grpc.EnvServicer):

    def __init__(self, env_id: str):
        super().__init__()

        self.env = gym.make(env_id)


    def Reset(self, request: gym_pb2.ResetArgs, context: grpc.RpcContext):
        obs, info = self.env.reset()
        obs = encode(obs)
        obs = encode(np.random.rand(4, 4))
        info = gym_pb2.Info(params={})

        return gym_pb2.ResetReturn(obs=obs, info=info)

    def Step(self, request: gym_pb2.Action, context: grpc.RpcContext):
        action = request.action
        obs = encode(np.random.rand(4, 4))
        reward = 1.0
        terminated = False
        truncated = False
        info = gym_pb2.Info(params={})

        return gym_pb2.StepReturn(obs=obs, reward=reward, terminated=terminated, truncated=truncated, info=info)


def serve():
    port = '50051'
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    gym_pb2_grpc.add_EnvServicer_to_server(Cartpole("CartPole-v1"), server)
    server.add_insecure_port('[::]:' + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()


# if __name__ == '__main__':
#     logging.basicConfig()
#     serve()

logging.basicConfig()

serve()