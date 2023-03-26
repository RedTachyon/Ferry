from ferry.pipes import PipeServer, FIFO, EnvWorker

server = PipeServer("CartPole-v1", FIFO)
# server = EnvWorker("CartPole-v1", FIFO)
server.run()

