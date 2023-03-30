from __future__ import annotations

import time

import gymnasium as gym
import numpy as np

from ferry.core import Communicator, create_gymnasium_message
from ferry.gym_grpc import gym_ferry_pb2
from ferry.utils import wrap_dict, decode, unwrap_dict


class ClientBackend:
    def __init__(self, env_id: str, port: int = 5005):
        self.env = gym.make(env_id)
        self.env.reset()

        self.communicator = Communicator("ferry_client", "ferry_server", "ferry_lock", port=port, create=False)

        print(f"Backend client listening on port {port}")

    def run(self):
        while True:
            # Wait for a decision request
            # response = self.communicator.receive_message()
            print("Requesting a decision")

            response = self.request_decision()
            print(f"Received a decision: {response}")

            if response.HasField("action"):
                action = decode(response.action)
                if action.size == 1:
                    action = action[0]
                obs, reward, terminated, truncated, info = self.env.step(action)
                step_return = create_gymnasium_message(step_return=(obs, reward, terminated, truncated, info))
                print(f"Sending step return: {step_return}")
                self.communicator.send_message(step_return)
                print("Sent step return")

            elif response.HasField("reset_args"):
                seed = response.reset_args.seed if response.reset_args.seed != -1 else None
                options = unwrap_dict(response.reset_args.options)
                obs, info = self.env.reset(seed=seed, options=options)
                reset_return = create_gymnasium_message(reset_return=(obs, info))
                print(f"Sending reset return: {reset_return}")
                self.communicator.send_message(reset_return)
                print("Sent reset return")

            elif response.HasField("close"):
                self.env.close()
                break

            else:
                # Send a dummy message to request a decision
                raise ValueError("Received an invalid message")

            print("Receiving dummy")

            self.communicator.receive_message()  # dummy
            print("Received dummy")


    def request_decision(self):
        decision_request = gym_ferry_pb2.GymnasiumMessage(dummy=True)
        self.communicator.send_message(decision_request)
        self.communicator.get_lock()

        response = self.communicator.receive_message()
        self.communicator.release_lock()
        return response

class ClientEnv:  # (gym.Env)
    def __init__(self, port: int = 50051):
        self.port = port
        self.communicator = Communicator("ferry_client", "ferry_server", "ferry_lock", port=port, create=False)
        print(f"Environment starting on port {port}")


    def reset(self, seed=None, options=None):
        seed = seed if seed is not None else -1
        options = wrap_dict(options) if options else {}

        reset_msg = create_gymnasium_message(reset_args=(seed, options))
        self.communicator.send_message(reset_msg)

        while True:
            response = self.communicator.receive_message()
            if response.HasField("reset_return"):
                obs = decode(response.reset_return.obs)
                info = unwrap_dict(response.reset_return.info)
                return obs, info

    def step(self, action: np.ndarray | int):
        """Send an action to the server and receive a response."""
        action_msg = create_gymnasium_message(action=action)

        self.communicator.send_message(action_msg)

        while True:
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
