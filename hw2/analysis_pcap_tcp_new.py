import os
from re import L
import sre_compile
import sys
import socket
from turtle import ScrolledCanvas
import dpkt

SYNCING = 0
SYNCING_ACK = 1
SYNCING_FIN = 2
FIRST = 3
SECOND = 4
FIN = 5


def inet_to_str(inet):
    # First try ipv4 and then ipv6
    try:
        return socket.inet_ntop(socket.AF_INET, inet)
    except ValueError:
        return socket.inet_ntop(socket.AF_INET6, inet)


def readfile():
    path = input("Enter the complete file path of the pcap file:")
    while not os.path.isfile(path) or not path.endswith(".pcap"):
        print("Please enter a correct pcap file path")
        path = input("Enter the complete file path of the pcap file:")
    print()
    pacp = open(path, 'rb')
    file = dpkt.pcap.Reader(pacp)
    return file

def find_current_sender(arr, sport, dport):
    for c in arr:
        if sport == c.get_src_port() or dport == c.get_src_port():
            return c
    return None


class conn:
    def __init__(self,src_port,dest_port, sender, ts=-1):
        self.src_port = src_port 
        self.dest_port = dest_port 
        self.throughput = 0
        self.triple_ACK = 0
        self.irtt = 0
        self.stage = SYNCING
        self.win_scaling = None
        self.sender = sender
        self.seqs = {}
        self.prints = [None] * 5
        self.start_time = ts
        self.c_window_index = 0
        self.end_time = 0
        self.c_window_array = [1,0,0]
        self.c_window_start_time = 0
        self.timeout = 0
        self.last_ack = [-1, 1]
        self.dup_acks =[]
        self.triple_count = 0
        self.first = [None, None]
        self.second = [None, None]

    def add_throughput(self, size):
        self.throughput += size

    def set_win_scale(self, win_scale):
        self.win_scaling = win_scale

    def get_src_port(self):
        return self.src_port

    def set_stage(self, stage):
        self.stage = stage

    def is_sender(self):
        return self.sender

    def get_stage(self):
        return self.stage
    
    def set_prints(self, s ,i):
        self.prints[i] = s

    def get_win_scale(self):
        return self.win_scaling

    def set_irtt(self, time):
        self.irtt = time - self.start_time 

    def set_end_time(self, time):
        self.end_time = time

    def set_c_window(self, ts):
        if self.c_window_index >= 3:
            return
        if self.irtt <= ts - self.c_window_start_time:
            self.c_window_index += 1
            if self.c_window_index < 3:
                self.c_window_array[self.c_window_index] += 1
            self.c_window_start_time = ts
        else:
            self.c_window_array[self.c_window_index] += 1
    
    def set_c_window_start(self,ts):
        self.c_window_start_time = ts

    def set_last_ack(self, ack):
        self.last_ack[0] = ack
    

    def add_seqs(self, seq, ts):
        self.seqs[seq] = ts

    def check_timeout(self, ack, ts):
        if ack in self.seqs and (ts - self.seqs[ack]) >= self.irtt * 2: #time out
            self.timeout += 1
    
    def check_triple_ack(self, ack):
        if self.last_ack[0] == ack: # if received the same ack as last time
            self.last_ack[1] += 1
            if self.last_ack[1] >= 3: #triple ack
                self.dup_acks.append(ack)
        else:
            self.last_ack = [ack, 1]


    def check_triple_sent(self, seq):
        if seq in self.dup_acks:
            self.triple_count += 1
    
    def get_dst_port(self):
        return self.dest_port

    def set_first_status(self, status):
        self.first[0] = status

    def set_first_ack(self, expected_ack):
        self.first[1] = expected_ack

    def set_second_status(self, status):
        self.second[0] = status

    def set_second_ack(self, expected_ack):
        self.second[1] = expected_ack

    def get_first(self):
        return self.first

    def get_second(self):
        return self.second
    
    def print(self):
        for s in self.prints:
            print(s)
        print(f"Total throughput: {(self.throughput/(self.end_time - self.start_time))}")
        print(f"Three congestion windows in order: {self.c_window_array}")
        print(f"Total number of retransmission occurred due to triple ack: {self.triple_count}")
        print(f"Total number of retransmission occurred due to timeout: {self.timeout}")


def pcap_parse():
    connarray = [] # store the value of each connection
    count = 0
    for ts, buf in readfile():
        eth = dpkt.ethernet.Ethernet(buf)  # getting connections
        if eth.type != dpkt.ethernet.ETH_TYPE_IP:  # check if Ip type
            continue

        ip = eth.data  # get ip data
        if ip.p != dpkt.ip.IP_PROTO_TCP:  # check if TCP protocol
            continue

        tcp = ip.data  # get tcp data

        sender = find_current_sender(connarray, tcp.sport, tcp.dport)

        if sender is None:
            sender = conn(tcp.sport, tcp.dport, True, ts)  # make up tcp flow start
            connarray.append(sender)
        
        
        if tcp.flags == 0x02:  # flag is syn, i.e. first request connection
            
            sender.add_throughput(len(tcp))

            for name, value in dpkt.tcp.parse_opts(tcp.opts):  # getting the window scaling factor from options
                if name == 3:
                    sender.set_win_scale(2 ** int.from_bytes(value, "big"))
                    break
            sender.set_prints(f"Found flow on src port {tcp.sport} and dest port {tcp.dport}", 0)

        elif tcp.flags & dpkt.tcp.TH_ACK and tcp.flags & dpkt.tcp.TH_SYN:
            sender.set_stage(SYNCING_ACK)
            sender.set_irtt(ts)
            sender.set_last_ack(tcp.ack)
        elif tcp.flags & dpkt.tcp.TH_FIN:
            sender.set_end_time(ts)
        else:
            current_seq = tcp.seq  # sequence number
            current_ack = tcp.ack  # ack number
            current_win = tcp.win  # window value

            if sender.get_src_port() == tcp.sport: # pakcet by sender
                if sender.get_stage() == SYNCING_ACK: # not yet finished sync
                    if tcp.flags == 0x10 and len(tcp.data) == 0: # no piggy back
                        sender.set_stage(SYNCING_FIN)
                    else: # has piggy back
                        sender.set_prints(f"First request:\n\t (seq={current_seq}, ack={current_ack}, received window size={current_win * sender.get_win_scale()}", 1)
                        sender.set_stage(FIRST)
                        sender.set_c_window_start(ts)
                        sender.set_c_window(ts)
                        sender.set_expected_ack(tcp.seq, len(tcp.data))
                elif sender.get_stage() == SYNCING_FIN: 
                    sender.set_prints(f"First request:\n\t (seq={current_seq}, ack={current_ack}, received window size={current_win * sender.get_win_scale()}", 1)
                    sender.set_stage(FIRST)
                    sender.set_c_window_start(ts)
                    sender.set_c_window(ts)
                    sender.set_first_status(False)
                    sender.set_first_ack(tcp.seq + len(tcp.data))
                elif sender.get_stage() == FIRST:
                    sender.set_prints(f"Second request:\n\t (seq={current_seq}, ack={current_ack}, received window size={current_win * sender.get_win_scale()}", 3)
                    sender.set_stage(SECOND)
                    sender.set_second_status(False)
                    sender.set_second_ack(tcp.seq + len(tcp.data))
                else:
                    sender.set_c_window(ts)
                
                
                sender.add_throughput(len(tcp))
                sender.add_seqs(current_seq, ts)
                sender.check_triple_sent(current_seq)

                
                
            else: # packet by receiver
                if sender.get_first()[0] == False and sender.get_first()[1] == tcp.ack:
                    sender.set_first_status = True
                    sender.set_prints(f"First Response: \n\t (seq={current_seq}, ack={current_ack}, received window size={current_win * sender.get_win_scale()}", 2)
                elif sender.get_second()[0] == False and sender.get_second()[1] == tcp.ack:
                    sender.set_second_status = True
                    sender.set_prints(f"Second Response: \n\t (seq={current_seq}, ack={current_ack}, received window size={current_win * sender.get_win_scale()}", 4)
                    sender.set_stage(FIN)

                sender.check_timeout(current_ack, ts)
                sender.check_triple_ack(tcp.ack)
    for c in connarray:
        c.print()
        print()
                

pcap_parse()               
