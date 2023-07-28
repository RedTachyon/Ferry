from ferry.pipes import PipeServer

server = PipeServer("CartPole-v1")
# server = EnvWorker("CartPole-v1", FIFO)
server.run()