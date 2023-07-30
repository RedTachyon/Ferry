from __future__ import annotations

import gymnasium as gym

from ferry.core import Communicator, create_gymnasium_message
from ferry.gym_grpc import gym_ferry_pb2
from ferry.gym_grpc.gym_ferry_pb2 import GymnasiumMessage
from ferry.utils import decode, unwrap_dict, encode, wrap_dict


class ClientBackend:
    def __init__(self, env_id: str, port: int = 5005):
        self.env = gym.make(env_id)
        self.env.reset()

        # self.communicator = Communicator("ferry_client", "ferry_server", "ferry_lock", port=port, create=False)
        self.communicator = Communicator("ferry", create=False)


        print(f"Backend client listening on port {port}")

    def run(self):
        while True:

            self.communicator.send_message(gym_ferry_pb2.GymnasiumMessage(request=True))

            response = self.communicator.receive_message()

            if response.HasField("action"):
                action = decode(response.action)
                if action.size == 1:
                    action = action[0]
                obs, reward, terminated, truncated, info = self.env.step(action)
                msg = create_gymnasium_message(step_return=(obs, reward, terminated, truncated, info))

            elif response.HasField("reset_args"):
                seed = response.reset_args.seed if response.reset_args.seed != -1 else None
                options = unwrap_dict(response.reset_args.options)
                obs, info = self.env.reset(seed=seed, options=options)
                msg = create_gymnasium_message(reset_return=(obs, info))

            elif response.HasField("close"):
                self.env.close()
                return

            else:
                # Send a dummy message to request a decision
                raise ValueError("Received an invalid message")

            self.communicator.send_message(msg)


            self.communicator.receive_message()  # dummy


class ServerBackend:
    def __init__(self, env_id: str, port: int = 50051):
        self.env = gym.make(env_id)
        self.env.reset()

        self.communicator = Communicator("ferry", create=True)

        print("Waiting for handshake")
        self.communicator.send_message(gym_ferry_pb2.GymnasiumMessage(request=True))
        self.communicator.receive_message() # handshake
        self.communicator.send_message(gym_ferry_pb2.GymnasiumMessage(request=True))

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
        if action.size == 1:
            action = action[0]
        obs, reward, terminated, truncated, info = self.env.step(action)
        step_return = gym_ferry_pb2.StepReturn(obs=encode(obs), reward=reward, terminated=terminated,
                                         truncated=truncated, info=wrap_dict(info))
        response = gym_ferry_pb2.GymnasiumMessage(step_return=step_return)
        self.communicator.send_message(response)

    def run(self):
        while True:
            msg = self.communicator.receive_message()

            if msg.HasField("action"):
                self.process_step(msg)
            elif msg.HasField("reset_args"):
                self.process_reset(msg)
            elif msg.HasField("close"):
                self.process_close(msg)
                break
