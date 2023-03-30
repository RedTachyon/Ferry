from __future__ import annotations

import mmap
import os
import time
from typing import Optional, Any

import numpy as np
import posix_ipc

from ferry.gym_grpc import gym_ferry_pb2
from ferry.gym_grpc.gym_ferry_pb2 import GymnasiumMessage, StepReturn, ResetArgs
from ferry.utils import encode, wrap_dict


def create_memory_map(file_path: str, size: int = 1024) -> mmap.mmap:
    # Create a new file and set its size to the given size

    if os.path.exists(file_path):
        os.remove(file_path)

    with open(file_path, "wb") as f:
        f.write(b"\x00" * size)

    # Memory map the file
    with open(file_path, "r+b") as f:
        mmapped_file = mmap.mmap(f.fileno(), size, access=mmap.ACCESS_WRITE)

    return mmapped_file


def get_memory_map(file_path: str, size: int = 1024) -> mmap.mmap:
    # Memory map the file
    with open(file_path, "r+b") as f:
        mmapped_file = mmap.mmap(f.fileno(), size, access=mmap.ACCESS_WRITE)

    return mmapped_file


def create_lock(name: str, initial_value: int) -> posix_ipc.Semaphore:
    try:
        lock = posix_ipc.Semaphore(name, posix_ipc.O_CREAT, initial_value=initial_value)
    except posix_ipc.ExistentialError:
        lock = posix_ipc.Semaphore(name)

    return lock


def get_lock(name: str, initial_value: int) -> posix_ipc.Semaphore:
    lock = posix_ipc.Semaphore(name)

    return lock


TIMEOUT = 0


class Communicator:
    def __init__(self, name_send: str, name_recv: str, lock_name: str, port: int = 0, size: int = 1024, create: bool = True):

        self.name_send = name_send
        self.name_recv = name_recv
        self.port = port
        self.size = size

        mmap_func = create_memory_map if create else get_memory_map
        lock_func = create_lock if create else get_lock

        self.send_file = mmap_func(f"/tmp/{name_send}:{port}", size)
        self.recv_file = mmap_func(f"/tmp/{name_recv}:{port}", size)

        self.send_size = mmap_func(f"/tmp/{name_send}_size:{port}", 4)
        self.recv_size = mmap_func(f"/tmp/{name_recv}_size:{port}", 4)

        self.lock_write = lock_func(f"{lock_name}_write:{port}", 1)
        self.lock_read = lock_func(f"{lock_name}_read:{port}", 0)
        self.lock_sync2 = lock_func(f"{lock_name}_sync:{port}", 1)

    def send_message(self, msg: gym_ferry_pb2.GymnasiumMessage):
        print(f"Trying to send message {msg}")
        serialized_msg = msg.SerializeToString()
        with self.lock_write:
            self.send_file[:len(serialized_msg)] = serialized_msg
            self.send_size[:4] = len(serialized_msg).to_bytes(4, 'little')
        self.lock_read.release()

    def receive_message(self) -> gym_ferry_pb2.GymnasiumMessage:
        print(f"Trying to receive message")
        self.lock_read.acquire()
        msg = gym_ferry_pb2.GymnasiumMessage()
        with self.lock_write:
            msg_size = int.from_bytes(self.recv_size[:4], 'little')
            while msg_size == 0:
                self.lock_write.release()
                time.sleep(TIMEOUT)
                self.lock_write.acquire()
                msg_size = int.from_bytes(self.recv_size[:4], 'little')

            serialized_msg = bytes(self.recv_file[:msg_size])
            msg.ParseFromString(serialized_msg)
            self.recv_size[:4] = (0).to_bytes(4, 'little')

        print(f"Received message {msg}")
        return msg

    def send_dummy(self):
        print("Sending sync dummy message")
        self.send_message(gym_ferry_pb2.GymnasiumMessage(dummy=True))


    def get_lock(self):
        # breakpoint()
        print(f"GETTING LOCK -1 {self.lock_sync2.name}")
        self.lock_sync2.acquire()
        print(f"GOT LOCK -1 {self.lock_sync2.name}")


    def release_lock(self):
        # breakpoint()
        print(f"RELEASING LOCK +1 {self.lock_sync2.name}")
        self.lock_sync2.release()
        print(f"RELEASED LOCK +1 {self.lock_sync2.name}")



    def close(self):
        for f in [self.send_file, self.recv_file, self.send_size, self.recv_size]:
            f.close()
        self.send_file.close()
        self.recv_file.close()
        self.send_size.close()
        self.recv_size.close()
        self.lock_write.close()
        self.lock_read.close()
        self.lock_sync2.close()

        os.remove(f"/tmp/{self.name_send}:{self.port}")
        os.remove(f"/tmp/{self.name_recv}:{self.port}")
        os.remove(f"/tmp/{self.name_send}_size:{self.port}")
        os.remove(f"/tmp/{self.name_recv}_size:{self.port}")


def create_gymnasium_message(step_return: Optional[tuple[np.ndarray, float, bool, bool, dict[str, Any]]] = None,
                             reset_return: Optional[tuple[np.ndarray, dict[str, Any]]] = None,
                             reset_args: Optional[tuple[int, dict[str, Any]]]= None,
                             action: Optional[np.ndarray] = None,
                             close: Optional[bool] = None) -> GymnasiumMessage:

    message = GymnasiumMessage()

    if step_return is not None:
        obs, reward, terminated, truncated, info = step_return
        obs_data = encode(obs)
        info = wrap_dict(info)

        step_return = StepReturn(obs=obs_data,
                                 reward=reward,
                                 terminated=terminated,
                                 truncated=truncated,
                                 info=info)
        message.step_return.CopyFrom(step_return)

    elif reset_return is not None:
        obs, info = reset_return

        reset_return_ = gym_ferry_pb2.ResetReturn(obs=encode(obs), info=wrap_dict(info))

        message.reset_return.CopyFrom(reset_return_)

    elif reset_args is not None:
        seed, options = reset_args
        reset_args = ResetArgs(seed=seed,
                               options=wrap_dict(options))

        message.reset_args.CopyFrom(reset_args)

    elif action is not None:
        action_data = encode(action)

        message.action.CopyFrom(action_data)

    elif close is not None:
        message.close = close

    else:
        raise ValueError("No valid keyword arguments provided.")

    return message
