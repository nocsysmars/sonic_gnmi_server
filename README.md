# my_gnmi_server

- Dependent python package
```sh
  pyangbind, pyang, protobuf, grpcio, futures
```

- Run the server:
```sh
  python nocsys_sonic_gnmi_server.py localhost:5001
```

- Run the client:
    > just an example, get your client program elsewhere
```sh
  gnmi -addr localhost:5001 get "/lldp/interfaces/interface"
```

- OpenConfig yang models can bed used:
    - /lldp/
    - /interfaces/
    - /components/
    - /network-instances/network-instance[name=DEFAULT]/fdb/

- List the path available:
```sh
  gnmi -addr localhost:5001 get "/"
```
