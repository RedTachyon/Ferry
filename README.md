# Ferry

Ferry is a tool that enables interacting with [Gymnasium](https://github.com/Farama-Foundation/Gymnasium) environments
over a network connection (including locally) via gRPC.

The potential applications include:

- Simulating the environment on a separate machine
- Interfacing with environments built with different languages, without a dedicated Python link
- (future) Interacting with environments running in real time

The main intent is interfacing with games built in powerful engines like Unity and Unreal.
Adding a gRPC query or a server in the environment code will expose it for interaction with the standard
Gymnasium API.

There are two possible paradigms -- the environment runs either as a server, or as a client.

ClientEnv has a relatively intuitive interpretation. The server maintains an instance of the environment, 
and calls its methods according to the gRPC calls. The user (or the RL algorithm) calls the methods of `ClientEnv`, 
which in turn calls the gRPC methods on the server.

ServerEnv works the other way around. It expects that the user creates a server which implements a policy, 
and the environment lives in a client which can query that policy. When the client queries the server, it sends an observation, 
and receives the following observation.


In summary, in ClientEnv:
- The underlying environment logic lives on the server
- The `Env` instance exists in the client
- The algorithmic logic is in the client

In ServerEnv:
- The underlying environment logic is in the client
- The `Env` instance exists on the server
- The algorithmic logic is on the server


The `ServerEnv` implementation is inspired by ML-Agents, but we generally recommend using `ClientEnv`.

TODO: profiling with fast/slow languages on the server/client