from ferry.gpt_memory import MemEnv, cleanup

import numpy as np
from tqdm import trange
env = MemEnv()

env.reset()
for i in trange(1000):
    # print(i)
    action = np.array([0], dtype=int)
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        env.reset()

env.close()
cleanup()