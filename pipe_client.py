from ferry.pipes import PipeEnv, FIFO
from tqdm import trange
env = PipeEnv(FIFO)

# env.reset()
for i in trange(1000):
    # print(i)
    # action = np.array([0], dtype=int)
    obs, reward, done, info = env.step()
    # if terminated or truncated:
    #     env.reset()

# env.close()
# cleanup()