from __future__ import annotations

import gymnasium as gym
import numpy as np

from ferry.core import Communicator, create_gymnasium_message
from ferry.gym_grpc import gym_ferry_pb2
from ferry.utils import wrap_dict, decode, unwrap_dict


class ServerEnv(gym.Env):
    def __init__(self, port: int = 5005):
        self.port = port
        self.communicator = Communicator("ferry", create=True)


    def reset(self, seed=None, options=None):
        # print("Resetting environment")
        seed = seed if seed is not None else -1
        options = wrap_dict(options) if options else {}

        reset_args = create_gymnasium_message(reset_args=(seed, options))

        _request = self.communicator.receive_message()

        self.communicator.send_message(reset_args)

        response = self.communicator.receive_message()

        if response.HasField("reset_return"):
            obs = decode(response.reset_return.obs)
            info = unwrap_dict(response.reset_return.info)

            self.communicator.send_message(gym_ferry_pb2.GymnasiumMessage(status=True))

            return obs, info

    def step(self, action: np.ndarray | int):
        action_msg = create_gymnasium_message(action=action)

        _request = self.communicator.receive_message()

        self.communicator.send_message(action_msg)

        response = self.communicator.receive_message()

        if response.HasField("step_return"):
            obs = decode(response.step_return.obs)
            reward = response.step_return.reward
            terminated = response.step_return.terminated
            truncated = response.step_return.truncated
            info = unwrap_dict(response.step_return.info)
            self.communicator.send_message(gym_ferry_pb2.GymnasiumMessage(status=True))

            return obs, reward, terminated, truncated, info

    def close(self):
        self.communicator.close()


class ClientEnv:  # (gym.Env)
    def __init__(self, port: int = 50051):
        self.port = port
        self.communicator = Communicator("ferry", create=False)


        self.communicator.receive_message()
        self.communicator.send_message(gym_ferry_pb2.GymnasiumMessage(status=True))
        self.communicator.receive_message()
        print(f"Environment starting on port {port}")



    def reset(self, seed=None, options=None):
        seed = seed if seed is not None else -1
        options = wrap_dict(options) if options else {}

        reset_msg = create_gymnasium_message(reset_args=(seed, options))
        self.communicator.send_message(reset_msg)


        response = self.communicator.receive_message()
        # self.communicator.release_lock(2)

        if response.HasField("reset_return"):
            obs = decode(response.reset_return.obs)
            info = unwrap_dict(response.reset_return.info)
            return obs, info

    def step(self, action: np.ndarray | int):
        """Send an action to the server and receive a response."""
        action_msg = create_gymnasium_message(action=action)

        self.communicator.send_message(action_msg)
        response = self.communicator.receive_message()

        if response.HasField("step_return"):
            obs = decode(response.step_return.obs)
            reward = response.step_return.reward
            terminated = response.step_return.terminated
            truncated = response.step_return.truncated
            info = unwrap_dict(response.step_return.info)
            return obs, reward, terminated, truncated, info

    def close(self):
        close_msg = gym_ferry_pb2.GymnasiumMessage(close=True)
        self.communicator.send_message(close_msg)
