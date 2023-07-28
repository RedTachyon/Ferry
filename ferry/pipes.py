from __future__ import annotations

import errno
import os

from google.protobuf.struct_pb2 import Value, Struct

import gymnasium as gym
import numpy as np

from ferry.gym_grpc import gym_ferry_pb2
from ferry.utils import decode, encode, wrap_dict, unwrap_dict

# # FIFO = '/Users/redtachyon/projects/Ferry/mypipe'
# FIFO = '/tmp/ferry_pipe'
#
# try:
#     os.mkfifo(FIFO)
# except OSError as oe:
#     if oe.errno != errno.EEXIST:
#         raise
#
# try:
#     os.mkfifo(FIFO + "back")
# except OSError as oe:
#     if oe.errno != errno.EEXIST:
#         raise
#
FIFO_REQUEST = '/tmp/ferry_pipe_request'
FIFO_RESPONSE = '/tmp/ferry_pipe_response'
FIFO_REQUEST_BACK = '/tmp/ferry_pipe_request_back'
FIFO_RESPONSE_BACK = '/tmp/ferry_pipe_response_back'

for fifo in [FIFO_REQUEST, FIFO_RESPONSE, FIFO_REQUEST_BACK, FIFO_RESPONSE_BACK]:
    try:
        os.mkfifo(fifo)
    except OSError as oe:
        if oe.errno != errno.EEXIST:
            raise

class PipeServer:
    def __init__(self, env_id: str, request_path: str = FIFO_REQUEST, response_path: str = FIFO_RESPONSE):
        self.env = gym.make(env_id)
        self.request_path = request_path
        self.response_path = response_path
        self.env.reset()

    def run(self):
        while True:
            # print("Opening FIFO...")
            with open(self.request_path, "rb") as fifo:
                # print("FIFO opened")
                data = fifo.read()
                if len(data) == 0:
                    print("Writer closed")
                    break
                # print("Received action")
                # action = np.frombuffer(data, dtype=int)[0]
                # print(f"{data=}")
                action = decode(gym_ferry_pb2.NumpyArray.FromString(data))
                # print(action)

            obs, reward, terminated, truncated, info = self.env.step(action)

            # print("Sending observation")
            # print(obs)
            # print(obs.tobytes())
            data = encode(obs).SerializeToString()
            with open(self.response_path, "wb") as fifo:
                fifo.write(data)


class PipeEnv:
    def __init__(self, request_path: str = FIFO_REQUEST, response_path: str = FIFO_RESPONSE):
        self.request_path = request_path
        self.response_path = response_path

    def step(self):
        with open(self.request_path, "wb") as fifo:
            action = np.array(0, dtype=int)
            data = encode(action)
            data_b = data.SerializeToString()
            fifo.write(data_b)

        with open(self.response_path, "rb") as fifo:
            data_b = fifo.read()
            data = gym_ferry_pb2.NumpyArray.FromString(data_b)

        return decode(data)
