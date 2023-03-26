from __future__ import annotations

import os
import time
from multiprocessing import Lock
from multiprocessing.shared_memory import SharedMemory
from google.protobuf.struct_pb2 import Value, Struct
import gymnasium as gym
import numpy as np
from ferry.gym_grpc import gym_pb2
from ferry.utils import decode, encode, wrap_dict, unwrap_dict

import posix_ipc

shm_name = "Ferry_SharedMemory"
shm_size = 1024  # Adjust the size depending on your requirements
lock_name = "Ferry_SharedMemory_Lock"

TIMEOUT = 1

lock_write_name = "Ferry_SharedMemory_Write_Lock"
lock_read_name = "Ferry_SharedMemory_Read_Lock"

# try:
#     lock = posix_ipc.Semaphore(lock_name, posix_ipc.O_CREAT, initial_value=1)
# except posix_ipc.ExistentialError:
#     lock = posix_ipc.Semaphore(lock_name)

try:
    lock_write = posix_ipc.Semaphore(lock_write_name, posix_ipc.O_CREAT, initial_value=1)
except posix_ipc.ExistentialError:
    lock_write = posix_ipc.Semaphore(lock_write_name)

try:
    lock_read = posix_ipc.Semaphore(lock_read_name, posix_ipc.O_CREAT, initial_value=0)
except posix_ipc.ExistentialError:
    lock_read = posix_ipc.Semaphore(lock_read_name)

# try:
#     shm = SharedMemory(name=shm_name, create=True, size=shm_size)
# except FileExistsError:
#     shm = SharedMemory(name=shm_name)

shm_name_cs = "Ferry_SharedMemory_ClientServer"
shm_name_sc = "Ferry_SharedMemory_ServerClient"

try:
    shm_cs = SharedMemory(name=shm_name_cs, create=True, size=shm_size)
except FileExistsError:
    shm_cs = SharedMemory(name=shm_name_cs)

try:
    shm_sc = SharedMemory(name=shm_name_sc, create=True, size=shm_size)
except FileExistsError:
    shm_sc = SharedMemory(name=shm_name_sc)


msg_size_shm_name = "Ferry_SharedMemory_MsgSize"
msg_size_shm_size = 4  # 4 bytes for a 32-bit integer

try:
    msg_size_shm = SharedMemory(name=msg_size_shm_name, create=True, size=msg_size_shm_size)
except FileExistsError:
    msg_size_shm = SharedMemory(name=msg_size_shm_name)

class MemServer:
    def __init__(self, env_id: str):
        self.env = gym.make(env_id)
        self.env.reset()

    def process_reset(self, msg):
        seed = msg.seed if msg.seed != -1 else None
        options = unwrap_dict(msg.options)
        obs, info = self.env.reset(seed=seed, options=options)
        reset_return = gym_pb2.ResetReturn(obs=encode(obs), info=wrap_dict(info))
        response = gym_pb2.GymnasiumMessage(reset_return=reset_return)
        self.send_message(response)

    def process_close(self, msg):
        self.env.close()
        response = gym_pb2.GymnasiumMessage(close=True)
        self.send_message(response)

    def run(self):
        while True:
            msg = self.receive_message()
            if msg.HasField("action"):
                print("SERVER: stepping")
                action = decode(msg.action)
                obs, reward, terminated, truncated, info = self.env.step(action[0])
                step_return = gym_pb2.StepReturn(obs=encode(obs), reward=reward, terminated=terminated,
                                                 truncated=truncated, info=wrap_dict(info))
                response = gym_pb2.GymnasiumMessage(step_return=step_return)
                self.send_message(response)
            elif msg.HasField("reset_args"):
                self.process_reset(msg.reset_args)
            elif msg.HasField("close"):
                self.process_close(msg.close)
                break

    def send_message(self, msg: gym_pb2.GymnasiumMessage):
        # print("SERVER: sending message")
        serialized_msg = msg.SerializeToString()
        with lock_write:
            print("SERVER: sending message, claimed lock")
            shm.buf[:len(serialized_msg)] = serialized_msg
            msg_size_shm.buf[:4] = len(serialized_msg).to_bytes(4, 'little')
            print("SERVER: sent message, releasing lock")
            print(f"SERVER: Message sent: {msg}")
        lock_read.release()

    def receive_message(self) -> gym_pb2.GymnasiumMessage:
        # print("SERVER: receiving message")
        lock_read.acquire()
        msg = gym_pb2.GymnasiumMessage()
        with lock_write:
            print("SERVER: receiving message, claimed lock")
            msg_size = int.from_bytes(msg_size_shm.buf[:4], 'little')
            while msg_size == 0:
                print("SERVER: no message in buffer, releasing lock")
                lock_write.release()
                time.sleep(TIMEOUT)
                lock_write.acquire()
                msg_size = int.from_bytes(msg_size_shm.buf[:4], 'little')

            # if msg_size == 0:
            #     print("SERVER: no message in buffer, releasing lock")
            #     return msg  # Return an empty message if there is no message in the buffer
            serialized_msg = shm.buf.tobytes()[:msg_size]
            msg.ParseFromString(serialized_msg)
            msg_size_shm.buf[:4] = (0).to_bytes(4, 'little')
            print("SERVER: received message, releasing lock")
            print(f"SERVER: Message received: {msg}")
        return msg

class MemEnv:
    def __init__(self):
        pass

    def reset(self, seed=None, options=None):
        seed = seed if seed is not None else -1
        options = wrap_dict(options) if options else {}
        reset_args = gym_pb2.ResetArgs(seed=seed, options=options)
        reset_msg = gym_pb2.GymnasiumMessage(reset_args=reset_args)
        print("CLIENT: resetting")
        self.send_message(reset_msg)

        while True:
            response = self.receive_message()
            if response.HasField("reset_return"):
                obs = decode(response.reset_return.obs)
                return obs

    def step(self, action: np.ndarray | int):
        # if isinstance(action, int):
        #     action = np.array([action], dtype=int)
        action_msg = gym_pb2.GymnasiumMessage(action=encode(action))
        print("CLIENT: sending step message")
        self.send_message(action_msg)

        while True:
            response = self.receive_message()
            if response.HasField("step_return"):
                print("CLIENT: received step return")
                obs = decode(response.step_return.obs)
                reward = response.step_return.reward
                terminated = response.step_return.terminated
                truncated = response.step_return.truncated
                info = unwrap_dict(response.step_return.info)
                return obs, reward, terminated, truncated, info

        # response = self.receive_message()
        # while not response.HasField("step_return"):
        #     response = self.receive_message()
        # # print("Received response:", response)
        # if response.HasField("step_return"):
        #     obs = decode(response.step_return.obs)
        #     reward = response.step_return.reward
        #     terminated = response.step_return.terminated
        #     truncated = response.step_return.truncated
        #     info = unwrap_dict(response.step_return.info)
        #     return obs, reward, terminated, truncated, info

    def close(self):
        print("CLIENT: closing")
        close_msg = gym_pb2.GymnasiumMessage(close=True)
        self.send_message(close_msg)

    def send_message(self, msg: gym_pb2.GymnasiumMessage):
        # print("CLIENT: sending message")
        serialized_msg = msg.SerializeToString()
        with lock_write:
            print("CLIENT: sending message, claimed lock")
            shm.buf[:len(serialized_msg)] = serialized_msg
            msg_size_shm.buf[:4] = len(serialized_msg).to_bytes(4, 'little')
            print("CLIENT: sent message, releasing lock")
            print(f"CLIENT: Message sent: {msg}")
        lock_read.release()

    def receive_message(self) -> gym_pb2.GymnasiumMessage:
        # print("CLIENT: receiving message")
        lock_read.acquire()
        msg = gym_pb2.GymnasiumMessage()
        with lock_write:
            print("CLIENT: waiting for message, claimed lock")
            msg_size = int.from_bytes(msg_size_shm.buf[:4], 'little')
            while msg_size == 0:
                print("CLIENT: trying to receive")
                lock_write.release()
                time.sleep(TIMEOUT)
                lock_write.acquire()
                msg_size = int.from_bytes(msg_size_shm.buf[:4], 'little')
            # if msg_size == 0:
            #     print("CLIENT: no message in buffer, releasing lock")
            #     return msg  # Return an empty message if there is no message in the buffer
            serialized_msg = shm.buf.tobytes()[:msg_size]
            msg.ParseFromString(serialized_msg)
            msg_size_shm.buf[:4] = (0).to_bytes(4, 'little')
            print("CLIENT: received message, releasing lock")
            print(f"CLIENT: Message received: {msg}")
        return msg





if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "server":
        server = MemServer("CartPole-v0")
        server.run()
    else:
        env = MemEnv()
        action = np.array([0], dtype=int)
        print("Stepping with action:", action)
        obs, reward, terminated, truncated, info = env.step(action)
        print("Received observation:", obs)
        print("Received reward:", reward)
        print("Received terminated:", terminated)
        print("Received truncated:", truncated)
        print("Received info:", info)