# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: gym_grpc/gym.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import struct_pb2 as google_dot_protobuf_dot_struct__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x12gym_grpc/gym.proto\x12\x03\x65nv\x1a\x1cgoogle/protobuf/struct.proto\"\x17\n\x05\x45nvID\x12\x0e\n\x06\x65nv_id\x18\x01 \x01(\t\"\x18\n\x06Status\x12\x0e\n\x06status\x18\x01 \x01(\x08\"8\n\nNumpyArray\x12\x0c\n\x04\x64\x61ta\x18\x01 \x01(\x0c\x12\r\n\x05shape\x18\x02 \x01(\x0c\x12\r\n\x05\x64type\x18\x03 \x01(\t\"\x18\n\x06\x41\x63tion\x12\x0e\n\x06\x61\x63tion\x18\x01 \x01(\x05\"\x14\n\x04Seed\x12\x0c\n\x04seed\x18\x01 \x01(\x05\"z\n\x07Options\x12(\n\x06params\x18\x01 \x03(\x0b\x32\x18.env.Options.ParamsEntry\x1a\x45\n\x0bParamsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12%\n\x05value\x18\x02 \x01(\x0b\x32\x16.google.protobuf.Value:\x02\x38\x01\"t\n\x04Info\x12%\n\x06params\x18\x01 \x03(\x0b\x32\x15.env.Info.ParamsEntry\x1a\x45\n\x0bParamsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12%\n\x05value\x18\x02 \x01(\x0b\x32\x16.google.protobuf.Value:\x02\x38\x01\"8\n\tResetArgs\x12\x0c\n\x04seed\x18\x01 \x01(\x05\x12\x1d\n\x07options\x18\x02 \x01(\x0b\x32\x0c.env.Options\"D\n\x0bResetReturn\x12\x1c\n\x03obs\x18\x01 \x01(\x0b\x32\x0f.env.NumpyArray\x12\x17\n\x04info\x18\x02 \x01(\x0b\x32\t.env.Info\"z\n\nStepReturn\x12\x1c\n\x03obs\x18\x01 \x01(\x0b\x32\x0f.env.NumpyArray\x12\x0e\n\x06reward\x18\x02 \x01(\x02\x12\x12\n\nterminated\x18\x03 \x01(\x08\x12\x11\n\ttruncated\x18\x04 \x01(\x08\x12\x17\n\x04info\x18\x05 \x01(\x0b\x32\t.env.Info2\x83\x01\n\x03\x45nv\x12\'\n\nInitialize\x12\n.env.EnvID\x1a\x0b.env.Status\"\x00\x12+\n\x05Reset\x12\x0e.env.ResetArgs\x1a\x10.env.ResetReturn\"\x00\x12&\n\x04Step\x12\x0b.env.Action\x1a\x0f.env.StepReturn\"\x00\x62\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'gym_grpc.gym_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _OPTIONS_PARAMSENTRY._options = None
  _OPTIONS_PARAMSENTRY._serialized_options = b'8\001'
  _INFO_PARAMSENTRY._options = None
  _INFO_PARAMSENTRY._serialized_options = b'8\001'
  _ENVID._serialized_start=57
  _ENVID._serialized_end=80
  _STATUS._serialized_start=82
  _STATUS._serialized_end=106
  _NUMPYARRAY._serialized_start=108
  _NUMPYARRAY._serialized_end=164
  _ACTION._serialized_start=166
  _ACTION._serialized_end=190
  _SEED._serialized_start=192
  _SEED._serialized_end=212
  _OPTIONS._serialized_start=214
  _OPTIONS._serialized_end=336
  _OPTIONS_PARAMSENTRY._serialized_start=267
  _OPTIONS_PARAMSENTRY._serialized_end=336
  _INFO._serialized_start=338
  _INFO._serialized_end=454
  _INFO_PARAMSENTRY._serialized_start=267
  _INFO_PARAMSENTRY._serialized_end=336
  _RESETARGS._serialized_start=456
  _RESETARGS._serialized_end=512
  _RESETRETURN._serialized_start=514
  _RESETRETURN._serialized_end=582
  _STEPRETURN._serialized_start=584
  _STEPRETURN._serialized_end=706
  _ENV._serialized_start=709
  _ENV._serialized_end=840
# @@protoc_insertion_point(module_scope)
