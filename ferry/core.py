from __future__ import annotations

import grpc
import numpy as np
import gymnasium as gym

from ferry.gym_grpc import gym_pb2_grpc, gym_pb2


def encode(array: np.ndarray) -> gym_pb2.NumpyArray:
    return gym_pb2.NumpyArray(data=array.tobytes(), shape=np.array(array.shape).tobytes(), dtype=str(array.dtype))


def decode(data: gym_pb2.NumpyArray) -> np.ndarray:
    return np.frombuffer(data.data, dtype=data.dtype).reshape(np.frombuffer(data.shape, dtype=int))


class ClientEnv(gym.Env):
    def __init__(self, env_id: str, port: int = 50051):
        self.channel = grpc.insecure_channel(f"localhost:{port}")
        self.stub = gym_pb2_grpc.EnvStub(self.channel)

        self.stub.Initialize(env_id)

    def reset(self, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        obs, info = self.stub.Reset()
        return decode(obs)

    def close(self):
        self.channel.close()