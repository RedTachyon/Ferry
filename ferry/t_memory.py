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

shm_name_cs = "Ferry_SharedMemory_CS"
shm_name_sc = "Ferry_SharedMemory_SC"
shm_size = 1024  # Adjust the size depending on your requirements

try:
    shm_cs = SharedMemory(name=shm_name_cs, create=True, size=shm_size)
except FileExistsError:
    shm_cs = SharedMemory(name=shm_name_cs)

try:
    shm_sc = SharedMemory(name=shm_name_sc, create=True, size=shm_size)
except FileExistsError:
    shm_sc = SharedMemory(name=shm_name_sc)

lock_write_name = "Ferry_SharedMemory_Write_Lock"
lock_read_name = "Ferry_SharedMemory_Read_Lock"

try:
    lock_write = posix_ipc.Semaphore(lock_write_name, posix_ipc.O_CREAT, initial_value=1)
except posix_ipc.ExistentialError:
    lock_write = posix_ipc.Semaphore(lock_write_name)

try:
    lock_read = posix_ipc.Semaphore(lock_read_name, posix_ipc.O_CREAT, initial_value=0)
except posix_ipc.ExistentialError:
    lock_read = posix_ipc.Semaphore(lock_read_name)

msg_size_shm_name_cs = "Ferry_SharedMemory_MsgSize_CS"
msg_size_shm_name_sc = "Ferry_SharedMemory_MsgSize_SC"
msg_size_shm_size = 4  # 4 bytes for a 32-bit integer

try:
    msg_size_shm_cs = SharedMemory(name=msg_size_shm_name_cs, create=True, size=msg_size_shm_size)
except FileExistsError:
    msg_size_shm_cs = SharedMemory(name=msg_size_shm_name_cs)

try:
    msg_size_shm_sc = SharedMemory(name=msg_size_shm_name_sc, create=True, size=msg_size_shm_size)
except FileExistsError:
    msg_size_shm_sc = SharedMemory(name=msg_size_shm_name_sc)

TIMEOUT = 0.0


def cleanup():
    shm_sc.close()
    shm_cs.close()
    msg_size_shm_sc.close()
    msg_size_shm_cs.close()
    lock_write.unlink()
    lock_read.unlink()


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
                # print("SERVER: stepping")
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

        cleanup()

    def send_message(self, msg: gym_pb2.GymnasiumMessage):
        serialized_msg = msg.SerializeToString()
        with lock_write:
            # print("SERVER: sending message, claimed lock")
            shm_sc.buf[:len(serialized_msg)] = serialized_msg
            msg_size_shm_sc.buf[:4] = len(serialized_msg).to_bytes(4, 'little')
            # print("SERVER: sent message, releasing lock")
            # print(f"SERVER: Message sent: {msg}")
        lock_read.release()

    def receive_message(self) -> gym_pb2.GymnasiumMessage:
        lock_read.acquire()
        msg = gym_pb2.GymnasiumMessage()
        with lock_write:
            # print("SERVER: receiving message, claimed lock")
            msg_size = int.from_bytes(msg_size_shm_cs.buf[:4], 'little')
            while msg_size == 0:
                # print("SERVER: no message in buffer, releasing lock")
                lock_write.release()
                time.sleep(TIMEOUT)
                lock_write.acquire()
                msg_size = int.from_bytes(msg_size_shm_cs.buf[:4], 'little')

            serialized_msg = shm_cs.buf.tobytes()[:msg_size]
            msg.ParseFromString(serialized_msg)
            msg_size_shm_cs.buf[:4] = (0).to_bytes(4, 'little')
            # print("SERVER: received message, releasing lock")
            # print(f"SERVER: Message received: {msg}")
        return msg


class MemEnv:
    def __init__(self):
        pass

    def reset(self, seed=None, options=None):
        seed = seed if seed is not None else -1
        options = wrap_dict(options) if options else {}
        reset_args = gym_pb2.ResetArgs(seed=seed, options=options)
        reset_msg = gym_pb2.GymnasiumMessage(reset_args=reset_args)
        # print("CLIENT: resetting")
        self.send_message(reset_msg)

        while True:
            response = self.receive_message()
            if response.HasField("reset_return"):
                obs = decode(response.reset_return.obs)
                return obs

    def step(self, action: np.ndarray | int):
        action_msg = gym_pb2.GymnasiumMessage(action=encode(action))
        # print("CLIENT: sending step message")
        self.send_message(action_msg)

        while True:
            response = self.receive_message()
            if response.HasField("step_return"):
                # print("CLIENT: received step return")
                obs = decode(response.step_return.obs)
                reward = response.step_return.reward
                terminated = response.step_return.terminated
                truncated = response.step_return.truncated
                info = unwrap_dict(response.step_return.info)
                return obs, reward, terminated, truncated, info

    def close(self):
        # print("CLIENT: closing")
        close_msg = gym_pb2.GymnasiumMessage(close=True)
        self.send_message(close_msg)
        # cleanup()


    def send_message(self, msg: gym_pb2.GymnasiumMessage):
        serialized_msg = msg.SerializeToString()
        with lock_write:
            # print("CLIENT: sending message, claimed lock")
            shm_cs.buf[:len(serialized_msg)] = serialized_msg
            msg_size_shm_cs.buf[:4] = len(serialized_msg).to_bytes(4, 'little')
            # print("CLIENT: sent message, releasing lock")
            # print(f"CLIENT: Message sent: {msg}")
        lock_read.release()

    def receive_message(self) -> gym_pb2.GymnasiumMessage:
        lock_read.acquire()
        msg = gym_pb2.GymnasiumMessage()
        with lock_write:
            # print("CLIENT: receiving message, claimed lock")
            msg_size = int.from_bytes(msg_size_shm_sc.buf[:4], 'little')
            while msg_size == 0:
                # print("CLIENT: no message in buffer, releasing lock")
                lock_write.release()
                time.sleep(TIMEOUT)
                lock_write.acquire()
                msg_size = int.from_bytes(msg_size_shm_sc.buf[:4], 'little')

            serialized_msg = shm_sc.buf.tobytes()[:msg_size]
            msg.ParseFromString(serialized_msg)
            msg_size_shm_sc.buf[:4] = (0).to_bytes(4, 'little')
            # print("CLIENT: received message, releasing lock")
            # print(f"CLIENT: Message received: {msg}")
        return msg
