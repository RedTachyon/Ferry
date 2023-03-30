from __future__ import annotations

import gymnasium as gym

import numpy as np
from ferry.core import Communicator, create_gymnasium_message
from ferry.gym_grpc import gym_ferry_pb2
from ferry.gym_grpc.gym_ferry_pb2 import GymnasiumMessage
from ferry.utils import unwrap_dict, decode, encode, wrap_dict


class ServerEnv(gym.Env):
    def __init__(self, port: int = 5005):
        self.port = port
        self.communicator = Communicator("ferry_server", "ferry_client", "ferry_lock", port=port, create=True)
        self.communicator.get_lock()

    def reset(self, seed=None, options=None):
        print("Resetting environment")
        seed = seed if seed is not None else -1
        options = wrap_dict(options) if options else {}

        reset_args = create_gymnasium_message(reset_args=(seed, options))

        self.wait_for_request()
        # breakpoint()
        self.communicator.release_lock()
        print("Got request, sending reset args")
        self.communicator.send_message(reset_args)
        print("Sent reset args, waiting for response")

        while True:
            print("Receiving a message")
            response = self.communicator.receive_message()
            if response.HasField("reset_return"):
                print("Got response")
                obs = decode(response.reset_return.obs)
                info = unwrap_dict(response.reset_return.info)
                print("Sending a dummy")
                # breakpoint()
                self.communicator.get_lock()
                self.communicator.send_dummy()  # For synchronization

                print("Sent dummy")
                return obs, info

    def step(self, action: np.ndarray | int):
        action_msg = create_gymnasium_message(action=action)

        self.wait_for_request()
        self.communicator.release_lock()
        self.communicator.send_message(action_msg)

        while True:
            response = self.communicator.receive_message()
            if response.HasField("step_return"):
                obs = decode(response.step_return.obs)
                reward = response.step_return.reward
                terminated = response.step_return.terminated
                truncated = response.step_return.truncated
                info = unwrap_dict(response.step_return.info)
                # breakpoint()
                self.communicator.get_lock()
                self.communicator.send_dummy()  # For synchronization

                return obs, reward, terminated, truncated, info

    def close(self):
        self.communicator.close()

    def wait_for_request(self):
        while True:
            # self.communicator.release_lock()
            response = self.communicator.receive_message()
            if response.HasField("dummy"):
                return

class ServerBackend:
    def __init__(self, env_id: str, port: int = 50051):
        self.env = gym.make(env_id)
        self.env.reset()

        self.communicator = Communicator("ferry_server", "ferry_client", "ferry_lock", port=port, create=True)

        print(f"Backend server listening on port {port}")

    def process_reset(self, msg: GymnasiumMessage):
        msg = msg.reset_args
        seed = msg.seed if msg.seed != -1 else None
        options = unwrap_dict(msg.options)
        obs, info = self.env.reset(seed=seed, options=options)
        response = create_gymnasium_message(reset_return=(obs, info))
        self.communicator.send_message(response)

    def process_close(self, msg: GymnasiumMessage):
        self.env.close()
        self.communicator.close()

    def process_step(self, msg: GymnasiumMessage):
        action = decode(msg.action)
        obs, reward, terminated, truncated, info = self.env.step(action[0])
        step_return = gym_ferry_pb2.StepReturn(obs=encode(obs), reward=reward, terminated=terminated,
                                         truncated=truncated, info=wrap_dict(info))
        response = gym_ferry_pb2.GymnasiumMessage(step_return=step_return)
        self.communicator.send_message(response)

    def run(self):
        while True:
            msg = self.communicator.receive_message()
            if msg.HasField("action"):
                # print("SERVER: stepping")
                action = decode(msg.action)
                if action.size == 1:
                    action = action[0]
                obs, reward, terminated, truncated, info = self.env.step(action)
                response = create_gymnasium_message(step_return=(obs, reward, terminated, truncated, info))
                self.communicator.send_message(response)
            elif msg.HasField("reset_args"):
                self.process_reset(msg)
            elif msg.HasField("close"):
                self.process_close(msg)
                break
