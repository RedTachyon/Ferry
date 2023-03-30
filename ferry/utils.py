from __future__ import annotations

from typing import Any

import google.protobuf.internal.containers
import numpy as np

from ferry.gym_grpc import gym_ferry_pb2

from google.protobuf.struct_pb2 import Value
from google.protobuf.struct_pb2 import Struct


def encode(array: np.ndarray | int) -> gym_ferry_pb2.NumpyArray:
    return gym_ferry_pb2.NumpyArray(data=np.array(array).tobytes(), shape=np.array(array.shape).tobytes(), dtype=str(array.dtype))


def decode(data: gym_ferry_pb2.NumpyArray) -> np.ndarray:
    return np.frombuffer(data.data, dtype=data.dtype).reshape(np.frombuffer(data.shape, dtype=int))


def wrap_dict(d: dict[str, Any]) -> dict[str, Value]:
    """Convert an arbitrarily nested dictionary to a dictionary of protobuf Values."""
    new_dict = {}
    for k, v in d.items():
        if isinstance(v, dict):
            new_dict[k] = wrap_dict(v)
        elif isinstance(v, int):
            new_dict[k] = Value(number_value=v)
        elif isinstance(v, float):
            new_dict[k] = Value(number_value=v)
        elif isinstance(v, str):
            new_dict[k] = Value(string_value=v)
        elif isinstance(v, bool):
            new_dict[k] = Value(bool_value=v)

    return new_dict


def unwrap_dict(d: google.protobuf.internal.containers.MessageMap) -> dict[str, Any]:
    """Convert an arbitrarily nested dictionary of protobuf Values to a dictionary."""
    new_dict = {}
    for k, v in d.items():
        if isinstance(v, Struct):
            new_dict[k] = unwrap_dict(v)
        elif v.HasField("number_value"):
            new_dict[k] = v.number_value
        elif v.HasField("string_value"):
            new_dict[k] = v.string_value
        elif v.HasField("bool_value"):
            new_dict[k] = v.bool_value

    return new_dict
