from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Action(_message.Message):
    __slots__ = ["action"]
    ACTION_FIELD_NUMBER: _ClassVar[int]
    action: int
    def __init__(self, action: _Optional[int] = ...) -> None: ...

class EnvID(_message.Message):
    __slots__ = ["env_id"]
    ENV_ID_FIELD_NUMBER: _ClassVar[int]
    env_id: str
    def __init__(self, env_id: _Optional[str] = ...) -> None: ...

class Info(_message.Message):
    __slots__ = ["params"]
    class ParamsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _struct_pb2.Value
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_struct_pb2.Value, _Mapping]] = ...) -> None: ...
    PARAMS_FIELD_NUMBER: _ClassVar[int]
    params: _containers.MessageMap[str, _struct_pb2.Value]
    def __init__(self, params: _Optional[_Mapping[str, _struct_pb2.Value]] = ...) -> None: ...

class NumpyArray(_message.Message):
    __slots__ = ["data", "dtype", "shape"]
    DATA_FIELD_NUMBER: _ClassVar[int]
    DTYPE_FIELD_NUMBER: _ClassVar[int]
    SHAPE_FIELD_NUMBER: _ClassVar[int]
    data: bytes
    dtype: str
    shape: bytes
    def __init__(self, data: _Optional[bytes] = ..., shape: _Optional[bytes] = ..., dtype: _Optional[str] = ...) -> None: ...

class Options(_message.Message):
    __slots__ = ["params"]
    class ParamsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: _struct_pb2.Value
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[_struct_pb2.Value, _Mapping]] = ...) -> None: ...
    PARAMS_FIELD_NUMBER: _ClassVar[int]
    params: _containers.MessageMap[str, _struct_pb2.Value]
    def __init__(self, params: _Optional[_Mapping[str, _struct_pb2.Value]] = ...) -> None: ...

class ResetArgs(_message.Message):
    __slots__ = ["options", "seed"]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    SEED_FIELD_NUMBER: _ClassVar[int]
    options: Options
    seed: int
    def __init__(self, seed: _Optional[int] = ..., options: _Optional[_Union[Options, _Mapping]] = ...) -> None: ...

class ResetReturn(_message.Message):
    __slots__ = ["info", "obs"]
    INFO_FIELD_NUMBER: _ClassVar[int]
    OBS_FIELD_NUMBER: _ClassVar[int]
    info: Info
    obs: NumpyArray
    def __init__(self, obs: _Optional[_Union[NumpyArray, _Mapping]] = ..., info: _Optional[_Union[Info, _Mapping]] = ...) -> None: ...

class Seed(_message.Message):
    __slots__ = ["seed"]
    SEED_FIELD_NUMBER: _ClassVar[int]
    seed: int
    def __init__(self, seed: _Optional[int] = ...) -> None: ...

class Status(_message.Message):
    __slots__ = ["status"]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: bool
    def __init__(self, status: bool = ...) -> None: ...

class StepReturn(_message.Message):
    __slots__ = ["info", "obs", "reward", "terminated", "truncated"]
    INFO_FIELD_NUMBER: _ClassVar[int]
    OBS_FIELD_NUMBER: _ClassVar[int]
    REWARD_FIELD_NUMBER: _ClassVar[int]
    TERMINATED_FIELD_NUMBER: _ClassVar[int]
    TRUNCATED_FIELD_NUMBER: _ClassVar[int]
    info: Info
    obs: NumpyArray
    reward: float
    terminated: bool
    truncated: bool
    def __init__(self, obs: _Optional[_Union[NumpyArray, _Mapping]] = ..., reward: _Optional[float] = ..., terminated: bool = ..., truncated: bool = ..., info: _Optional[_Union[Info, _Mapping]] = ...) -> None: ...
