from ferry.core import Communicator

comm = Communicator("ferry_server", "ferry_client", "ferry_lock", port=5005, create=False)

comm.close()
