from __future__ import annotations

import errno
import os

from google.protobuf.struct_pb2 import Value, Struct

import gymnasium as gym
import numpy as np

from ferry.gym_grpc import gym_pb2
from ferry.utils import decode, encode, wrap_dict, unwrap_dict

# FIFO = '/Users/redtachyon/projects/Ferry/mypipe'
FIFO = '/tmp/ferry_pipe'

try:
    os.mkfifo(FIFO)
except OSError as oe:
    if oe.errno != errno.EEXIST:
        raise

try:
    os.mkfifo(FIFO + "back")
except OSError as oe:
    if oe.errno != errno.EEXIST:
        raise

class PipeServer:
    def __init__(self, env_id: str, path: str):
        self.env = gym.make(env_id)
        self.path = path
        self.env.reset()

    def run(self):
        while True:
            # print("Opening FIFO...")
            with open(self.path, "rb") as fifo:
                # print("FIFO opened")
                data = fifo.read()
                if len(data) == 0:
                    print("Writer closed")
                    break
                # print("Received action")
                # action = np.frombuffer(data, dtype=int)[0]
                # print(f"{data=}")
                action = decode(gym_pb2.NumpyArray.FromString(data))
                # print(action)

            obs, reward, terminated, truncated, info = self.env.step(action)

            # print("Sending observation")
            # print(obs)
            # print(obs.tobytes())
            data = encode(obs).SerializeToString()
            with open(self.path + "back", "wb") as fifo:
                fifo.write(data)


class PipeEnv:
    def __init__(self, path: str):
        self.path = path

    def step(self):
        with open(self.path, "wb") as fifo:
            action = np.array(0, dtype=int)
            data = encode(action)
            data_b = data.SerializeToString()
            fifo.write(data_b)

        with open(self.path + "back", "rb") as fifo:
            data_b = fifo.read()
            data = gym_pb2.NumpyArray.FromString(data_b)

        return decode(data)

class EnvWorker:
    def __init__(self, env_id: str, path: str = FIFO):
        self.env = gym.make(env_id)
        self.path = path
        self.path_back = path + "back"

    def run(self):
        print("Starting env-logic server")
        while True:
            # print("Opening FIFO...")
            with open(self.path, "rb") as fifo:
                data = fifo.read()
                if len(data) == 0:
                    print("Writer closed")
                    break

            msg = gym_pb2.GymnasiumMessage.FromString(data)
            # print(f"Reset args: {msg.reset_args}")
            # print(f"Action: {msg.action}")

            response = self.process_message(msg)
            # print(response)

            with open(self.path_back, "wb") as fifo:
                fifo.write(response.SerializeToString())

    def process_message(self, msg: gym_pb2.GymnasiumMessage) -> gym_pb2.GymnasiumMessage:
        if msg.HasField("reset_args"):
            response = self.process_reset(msg.reset_args)
        elif msg.HasField("action"):
            response = self.process_action(msg.action)
        elif msg.HasField("close"):
            response = self.process_close()
        else:
            raise ValueError("Unknown message type")

        return response

    def process_reset(self, msg: gym_pb2.ResetArgs) -> gym_pb2.GymnasiumMessage:
        seed = msg.seed if msg.seed != -1 else None
        obs, info = self.env.reset(seed=seed, options=unwrap_dict(msg.options))
        reset_return = gym_pb2.ResetReturn(obs=encode(obs), info=wrap_dict(info))
        msg = gym_pb2.GymnasiumMessage(reset_return=reset_return)
        return msg

    def process_action(self, msg: gym_pb2.NumpyArray) -> gym_pb2.GymnasiumMessage:
        obs, reward, terminated, truncated, info = self.env.step(decode(msg))

        step_return = gym_pb2.StepReturn(obs=encode(obs), reward=reward, terminated=terminated, truncated=truncated, info=wrap_dict(info))
        msg = gym_pb2.GymnasiumMessage(step_return=step_return)
        return msg

    def process_close(self) -> gym_pb2.GymnasiumMessage:
        self.env.close()
        msg = gym_pb2.GymnasiumMessage(close=True)
        return msg


class FerryEnv(gym.Env):
    def __init__(self, path: str = FIFO):
        self.path = path
        self.path_back = path + "back"

    def reset(self, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        options_pb2 = wrap_dict(options) if options else {}
        seed_pb2 = seed if seed is not None else -1

        reset_args = gym_pb2.ResetArgs(seed=seed_pb2, options=options_pb2)
        msg = gym_pb2.GymnasiumMessage(reset_args=reset_args)
        with open(self.path, "wb") as fifo:
            fifo.write(msg.SerializeToString())

        with open(self.path_back, "rb") as fifo:
            data = fifo.read()

        msg = gym_pb2.GymnasiumMessage.FromString(data)
        obs = decode(msg.reset_return.obs)
        info = unwrap_dict(msg.reset_return.info)
        return obs, info

    def step(self, action: np.ndarray):
        action = np.asarray(action)
        msg = gym_pb2.GymnasiumMessage(action=encode(action))
        with open(self.path, "wb") as fifo:
            fifo.write(msg.SerializeToString())

        with open(self.path_back, "rb") as fifo:
            data = fifo.read()

        msg = gym_pb2.GymnasiumMessage.FromString(data)
        obs = decode(msg.step_return.obs)
        reward = msg.step_return.reward
        terminated = msg.step_return.terminated
        truncated = msg.step_return.truncated
        info = unwrap_dict(msg.step_return.info)
        return obs, reward, terminated, truncated, info

    def close(self):
        super().close()
        msg = gym_pb2.GymnasiumMessage(close=True)
        with open(self.path, "wb") as fifo:
            fifo.write(msg.SerializeToString())

        return

    def render(self):
        pass
