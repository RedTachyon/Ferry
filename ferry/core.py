from __future__ import annotations

import grpc
import numpy as np
import gymnasium as gym

from ferry.gym_grpc import gym_pb2_grpc, gym_pb2


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

"""
GENERAL MODEL: (ML-Agents-like)
Environment logic has a client. When it wants a decision, it sends a request to the server. 
"""
