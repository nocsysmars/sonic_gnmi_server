# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: sonic_loopback_interface.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


import ywrapper_pb2 as ywrapper__pb2
import yext_pb2 as yext__pb2
import sonic_loopback_interface_enums_pb2 as sonic__loopback__interface__enums__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='sonic_loopback_interface.proto',
  package='openconfig',
  syntax='proto3',
  serialized_options=b'\n\025com.nocsys.openconfig',
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x1esonic_loopback_interface.proto\x12\nopenconfig\x1a\x0eywrapper.proto\x1a\nyext.proto\x1a$sonic_loopback_interface_enums.proto\"\xe1\x0e\n\x16SonicLoopbackInterface\x12\x85\x01\n\x12loopback_interface\x18\x8b\xe7\x8f\xd0\x01 \x01(\x0b\x32\x34.openconfig.SonicLoopbackInterface.LoopbackInterfaceB/\x82\x41,/sonic-loopback-interface/loopback-interface\x1a\xbe\r\n\x11LoopbackInterface\x12\xd5\x01\n loopback_interface_ipprefix_list\x18\x9c\xe8\xf4\xac\x01 \x03(\x0b\x32U.openconfig.SonicLoopbackInterface.LoopbackInterface.LoopbackInterfaceIpprefixListKeyBP\x82\x41M/sonic-loopback-interface/loopback-interface/loopback-interface-ipprefix-list\x12\xb9\x01\n\x17loopback_interface_list\x18\xc4\xe6s \x03(\x0b\x32M.openconfig.SonicLoopbackInterface.LoopbackInterface.LoopbackInterfaceListKeyBG\x82\x41\x44/sonic-loopback-interface/loopback-interface/loopback-interface-list\x1a\xd0\x03\n\x1dLoopbackInterfaceIpprefixList\x12\x97\x01\n\x06\x66\x61mily\x18\xbf\xde\xbf\xe3\x01 \x01(\x0e\x32*.openconfig.SonicLoopbackInterfaceIpFamilyBW\x82\x41T/sonic-loopback-interface/loopback-interface/loopback-interface-ipprefix-list/family\x12\xc2\x01\n\x05scope\x18\xb5\xd7\xfe{ \x01(\x0e\x32X.openconfig.SonicLoopbackInterface.LoopbackInterface.LoopbackInterfaceIpprefixList.ScopeBV\x82\x41S/sonic-loopback-interface/loopback-interface/loopback-interface-ipprefix-list/scope\"P\n\x05Scope\x12\x0f\n\x0bSCOPE_UNSET\x10\x00\x12\x1b\n\x0cSCOPE_global\x10\x01\x1a\t\x82\x41\x06global\x12\x19\n\x0bSCOPE_local\x10\x02\x1a\x08\x82\x41\x05local\x1a\x9b\x03\n LoopbackInterfaceIpprefixListKey\x12\x89\x01\n\x17loopback_interface_name\x18\x01 \x01(\tBh\x82\x41\x65/sonic-loopback-interface/loopback-interface/loopback-interface-ipprefix-list/loopback-interface-name\x12m\n\tip_prefix\x18\x02 \x01(\tBZ\x82\x41W/sonic-loopback-interface/loopback-interface/loopback-interface-ipprefix-list/ip-prefix\x12|\n loopback_interface_ipprefix_list\x18\x03 \x01(\x0b\x32R.openconfig.SonicLoopbackInterface.LoopbackInterface.LoopbackInterfaceIpprefixList\x1a\x96\x01\n\x15LoopbackInterfaceList\x12}\n\x08vrf_name\x18\x85\xac\x81\x80\x01 \x01(\x0b\x32\x15.ywrapper.StringValueBP\x82\x41M/sonic-loopback-interface/loopback-interface/loopback-interface-list/vrf-name\x1a\x8a\x02\n\x18LoopbackInterfaceListKey\x12\x80\x01\n\x17loopback_interface_name\x18\x01 \x01(\tB_\x82\x41\\/sonic-loopback-interface/loopback-interface/loopback-interface-list/loopback-interface-name\x12k\n\x17loopback_interface_list\x18\x02 \x01(\x0b\x32J.openconfig.SonicLoopbackInterface.LoopbackInterface.LoopbackInterfaceListB\x17\n\x15\x63om.nocsys.openconfigb\x06proto3'
  ,
  dependencies=[ywrapper__pb2.DESCRIPTOR,yext__pb2.DESCRIPTOR,sonic__loopback__interface__enums__pb2.DESCRIPTOR,])



_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACEIPPREFIXLIST_SCOPE = _descriptor.EnumDescriptor(
  name='Scope',
  full_name='openconfig.SonicLoopbackInterface.LoopbackInterface.LoopbackInterfaceIpprefixList.Scope',
  filename=None,
  file=DESCRIPTOR,
  create_key=_descriptor._internal_create_key,
  values=[
    _descriptor.EnumValueDescriptor(
      name='SCOPE_UNSET', index=0, number=0,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='SCOPE_global', index=1, number=1,
      serialized_options=b'\202A\006global',
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='SCOPE_local', index=2, number=2,
      serialized_options=b'\202A\005local',
      type=None,
      create_key=_descriptor._internal_create_key),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=1086,
  serialized_end=1166,
)
_sym_db.RegisterEnumDescriptor(_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACEIPPREFIXLIST_SCOPE)


_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACEIPPREFIXLIST = _descriptor.Descriptor(
  name='LoopbackInterfaceIpprefixList',
  full_name='openconfig.SonicLoopbackInterface.LoopbackInterface.LoopbackInterfaceIpprefixList',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='family', full_name='openconfig.SonicLoopbackInterface.LoopbackInterface.LoopbackInterfaceIpprefixList.family', index=0,
      number=477097791, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=b'\202AT/sonic-loopback-interface/loopback-interface/loopback-interface-ipprefix-list/family', file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='scope', full_name='openconfig.SonicLoopbackInterface.LoopbackInterface.LoopbackInterfaceIpprefixList.scope', index=1,
      number=260025269, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=b'\202AS/sonic-loopback-interface/loopback-interface/loopback-interface-ipprefix-list/scope', file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
    _SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACEIPPREFIXLIST_SCOPE,
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=702,
  serialized_end=1166,
)

_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACEIPPREFIXLISTKEY = _descriptor.Descriptor(
  name='LoopbackInterfaceIpprefixListKey',
  full_name='openconfig.SonicLoopbackInterface.LoopbackInterface.LoopbackInterfaceIpprefixListKey',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='loopback_interface_name', full_name='openconfig.SonicLoopbackInterface.LoopbackInterface.LoopbackInterfaceIpprefixListKey.loopback_interface_name', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=b'\202Ae/sonic-loopback-interface/loopback-interface/loopback-interface-ipprefix-list/loopback-interface-name', file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='ip_prefix', full_name='openconfig.SonicLoopbackInterface.LoopbackInterface.LoopbackInterfaceIpprefixListKey.ip_prefix', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=b'\202AW/sonic-loopback-interface/loopback-interface/loopback-interface-ipprefix-list/ip-prefix', file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='loopback_interface_ipprefix_list', full_name='openconfig.SonicLoopbackInterface.LoopbackInterface.LoopbackInterfaceIpprefixListKey.loopback_interface_ipprefix_list', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1169,
  serialized_end=1580,
)

_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACELIST = _descriptor.Descriptor(
  name='LoopbackInterfaceList',
  full_name='openconfig.SonicLoopbackInterface.LoopbackInterface.LoopbackInterfaceList',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='vrf_name', full_name='openconfig.SonicLoopbackInterface.LoopbackInterface.LoopbackInterfaceList.vrf_name', index=0,
      number=268457477, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=b'\202AM/sonic-loopback-interface/loopback-interface/loopback-interface-list/vrf-name', file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1583,
  serialized_end=1733,
)

_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACELISTKEY = _descriptor.Descriptor(
  name='LoopbackInterfaceListKey',
  full_name='openconfig.SonicLoopbackInterface.LoopbackInterface.LoopbackInterfaceListKey',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='loopback_interface_name', full_name='openconfig.SonicLoopbackInterface.LoopbackInterface.LoopbackInterfaceListKey.loopback_interface_name', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=b'\202A\\/sonic-loopback-interface/loopback-interface/loopback-interface-list/loopback-interface-name', file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='loopback_interface_list', full_name='openconfig.SonicLoopbackInterface.LoopbackInterface.LoopbackInterfaceListKey.loopback_interface_list', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1736,
  serialized_end=2002,
)

_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE = _descriptor.Descriptor(
  name='LoopbackInterface',
  full_name='openconfig.SonicLoopbackInterface.LoopbackInterface',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='loopback_interface_ipprefix_list', full_name='openconfig.SonicLoopbackInterface.LoopbackInterface.loopback_interface_ipprefix_list', index=0,
      number=362624028, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=b'\202AM/sonic-loopback-interface/loopback-interface/loopback-interface-ipprefix-list', file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='loopback_interface_list', full_name='openconfig.SonicLoopbackInterface.LoopbackInterface.loopback_interface_list', index=1,
      number=1897284, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=b'\202AD/sonic-loopback-interface/loopback-interface/loopback-interface-list', file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACEIPPREFIXLIST, _SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACEIPPREFIXLISTKEY, _SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACELIST, _SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACELISTKEY, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=276,
  serialized_end=2002,
)

_SONICLOOPBACKINTERFACE = _descriptor.Descriptor(
  name='SonicLoopbackInterface',
  full_name='openconfig.SonicLoopbackInterface',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='loopback_interface', full_name='openconfig.SonicLoopbackInterface.loopback_interface', index=0,
      number=436466571, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=b'\202A,/sonic-loopback-interface/loopback-interface', file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=113,
  serialized_end=2002,
)

_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACEIPPREFIXLIST.fields_by_name['family'].enum_type = sonic__loopback__interface__enums__pb2._SONICLOOPBACKINTERFACEIPFAMILY
_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACEIPPREFIXLIST.fields_by_name['scope'].enum_type = _SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACEIPPREFIXLIST_SCOPE
_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACEIPPREFIXLIST.containing_type = _SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE
_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACEIPPREFIXLIST_SCOPE.containing_type = _SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACEIPPREFIXLIST
_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACEIPPREFIXLISTKEY.fields_by_name['loopback_interface_ipprefix_list'].message_type = _SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACEIPPREFIXLIST
_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACEIPPREFIXLISTKEY.containing_type = _SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE
_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACELIST.fields_by_name['vrf_name'].message_type = ywrapper__pb2._STRINGVALUE
_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACELIST.containing_type = _SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE
_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACELISTKEY.fields_by_name['loopback_interface_list'].message_type = _SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACELIST
_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACELISTKEY.containing_type = _SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE
_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE.fields_by_name['loopback_interface_ipprefix_list'].message_type = _SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACEIPPREFIXLISTKEY
_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE.fields_by_name['loopback_interface_list'].message_type = _SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACELISTKEY
_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE.containing_type = _SONICLOOPBACKINTERFACE
_SONICLOOPBACKINTERFACE.fields_by_name['loopback_interface'].message_type = _SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE
DESCRIPTOR.message_types_by_name['SonicLoopbackInterface'] = _SONICLOOPBACKINTERFACE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

SonicLoopbackInterface = _reflection.GeneratedProtocolMessageType('SonicLoopbackInterface', (_message.Message,), {

  'LoopbackInterface' : _reflection.GeneratedProtocolMessageType('LoopbackInterface', (_message.Message,), {

    'LoopbackInterfaceIpprefixList' : _reflection.GeneratedProtocolMessageType('LoopbackInterfaceIpprefixList', (_message.Message,), {
      'DESCRIPTOR' : _SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACEIPPREFIXLIST,
      '__module__' : 'sonic_loopback_interface_pb2'
      # @@protoc_insertion_point(class_scope:openconfig.SonicLoopbackInterface.LoopbackInterface.LoopbackInterfaceIpprefixList)
      })
    ,

    'LoopbackInterfaceIpprefixListKey' : _reflection.GeneratedProtocolMessageType('LoopbackInterfaceIpprefixListKey', (_message.Message,), {
      'DESCRIPTOR' : _SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACEIPPREFIXLISTKEY,
      '__module__' : 'sonic_loopback_interface_pb2'
      # @@protoc_insertion_point(class_scope:openconfig.SonicLoopbackInterface.LoopbackInterface.LoopbackInterfaceIpprefixListKey)
      })
    ,

    'LoopbackInterfaceList' : _reflection.GeneratedProtocolMessageType('LoopbackInterfaceList', (_message.Message,), {
      'DESCRIPTOR' : _SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACELIST,
      '__module__' : 'sonic_loopback_interface_pb2'
      # @@protoc_insertion_point(class_scope:openconfig.SonicLoopbackInterface.LoopbackInterface.LoopbackInterfaceList)
      })
    ,

    'LoopbackInterfaceListKey' : _reflection.GeneratedProtocolMessageType('LoopbackInterfaceListKey', (_message.Message,), {
      'DESCRIPTOR' : _SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACELISTKEY,
      '__module__' : 'sonic_loopback_interface_pb2'
      # @@protoc_insertion_point(class_scope:openconfig.SonicLoopbackInterface.LoopbackInterface.LoopbackInterfaceListKey)
      })
    ,
    'DESCRIPTOR' : _SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE,
    '__module__' : 'sonic_loopback_interface_pb2'
    # @@protoc_insertion_point(class_scope:openconfig.SonicLoopbackInterface.LoopbackInterface)
    })
  ,
  'DESCRIPTOR' : _SONICLOOPBACKINTERFACE,
  '__module__' : 'sonic_loopback_interface_pb2'
  # @@protoc_insertion_point(class_scope:openconfig.SonicLoopbackInterface)
  })
_sym_db.RegisterMessage(SonicLoopbackInterface)
_sym_db.RegisterMessage(SonicLoopbackInterface.LoopbackInterface)
_sym_db.RegisterMessage(SonicLoopbackInterface.LoopbackInterface.LoopbackInterfaceIpprefixList)
_sym_db.RegisterMessage(SonicLoopbackInterface.LoopbackInterface.LoopbackInterfaceIpprefixListKey)
_sym_db.RegisterMessage(SonicLoopbackInterface.LoopbackInterface.LoopbackInterfaceList)
_sym_db.RegisterMessage(SonicLoopbackInterface.LoopbackInterface.LoopbackInterfaceListKey)


DESCRIPTOR._options = None
_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACEIPPREFIXLIST_SCOPE.values_by_name["SCOPE_global"]._options = None
_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACEIPPREFIXLIST_SCOPE.values_by_name["SCOPE_local"]._options = None
_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACEIPPREFIXLIST.fields_by_name['family']._options = None
_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACEIPPREFIXLIST.fields_by_name['scope']._options = None
_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACEIPPREFIXLISTKEY.fields_by_name['loopback_interface_name']._options = None
_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACEIPPREFIXLISTKEY.fields_by_name['ip_prefix']._options = None
_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACELIST.fields_by_name['vrf_name']._options = None
_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE_LOOPBACKINTERFACELISTKEY.fields_by_name['loopback_interface_name']._options = None
_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE.fields_by_name['loopback_interface_ipprefix_list']._options = None
_SONICLOOPBACKINTERFACE_LOOPBACKINTERFACE.fields_by_name['loopback_interface_list']._options = None
_SONICLOOPBACKINTERFACE.fields_by_name['loopback_interface']._options = None
# @@protoc_insertion_point(module_scope)
