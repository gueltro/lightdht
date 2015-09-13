"""
    Basic program to show the useage of lightdht.
    
    We run a dht node and log all incoming queries.
"""
import logging
import time
import os

import lightdht


# Enable logging:
loglevel = logging.DEBUG
req_handler = logging.StreamHandler(open("incoming-requests.log","a"))
req_handler.setLevel(loglevel)
formatter = logging.Formatter("[%(levelname)s@%(created)s] %(message)s")
req_handler.setFormatter(formatter)
stdout_handler = logging.StreamHandler()
stdout_handler.setFormatter(formatter)
logging.getLogger("krpcserver").setLevel(loglevel)
logging.getLogger("krpcserver").addHandler(req_handler)
logging.getLogger("krpcserver").addHandler(stdout_handler)
logging.getLogger("lightdht").setLevel(loglevel)
logging.getLogger("lightdht").addHandler(req_handler)
logging.getLogger("lightdht").addHandler(stdout_handler)

# Create a DHT node.
m = 10 # multiplicity of my seer

class Seer():
    def __init__(self, m):
        ids_ = [os.urandom(20) for i in range(m)]
        ports = [54769 + i for i in range(m)]
        self.fingers = [lightdht.DHT(port=ports[i], id_=ids_[i], version="XN\x00\x00") for i in range(m)] 

    def __enter__(self):
        for finger in self.fingers:
            finger.start()

    def __exit__(self):
        for finger in self.fingers:
            finger.shutdown()

seer = Seer(m)
# where to put our product
outf = open("crawl.log","a")

# handler
def makehandler(dht):
    def myhandler(rec, c):
        try:    
            if rec["y"] =="q":
                if rec["q"] == "get_peers" or rec["q"] == "announce_peer":
                    print >>outf,";".join(
                        [   str(time.time()),
                            rec["a"].get("id").encode("hex"),
                            rec["a"].get("info_hash").encode("hex"),
                            repr(c),
                        ])
                    outf.flush()
                        
        finally:
            # always ALWAYS pass it off to the real handler
            dht.default_handler(rec,c) 
    return myhandler

for dht in seer.fingers:
    dht.handler = makehandler(dht)
    dht.active_discovery = False
    dht.self_find_delay = 30

# Start it!
with seer:
    # Go to sleep and let the DHT service requests.
    while True:
        time.sleep(1)
