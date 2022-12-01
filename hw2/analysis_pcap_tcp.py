import os
import sys
import socket
import dpkt


def inet_to_str(inet):
    # First try ipv4 and then ipv6
    try:
        return socket.inet_ntop(socket.AF_INET, inet)
    except ValueError:
        return socket.inet_ntop(socket.AF_INET6, inet)


def pcap_parse():
    path = input("Enter the complete file path of the pcap file:")
    while not os.path.isfile(path) or not path.endswith(".pcap"):
        print("Please enter a correct pcap file path")
        path = input("Enter the complete file path of the pcap file:")
    print()
    f = open(path, 'rb')
    pcap = dpkt.pcap.Reader(f)

    throughput = {}  # map for calculating throughput
    synSeq = {}  # map for determining the first two transactions of each flow
    rtt = {}  # records the total rtt for throughput
    winScaling = {}  # records the window scaling for each flow
    tripleCount = {}  # record the number of triple ack for each flow
    cwnd = {}  # records the size of congestion windows for each flow
    finalPrint = {}  # final prints array for each flow
    irtt = {}  # keeps initial rtt for each flow
    tripleArray = {}  # dup ack seq array
    timeout = {}  # keeps timeout count
    twoTransactions = {}
    for ts, buf in pcap:
        eth = dpkt.ethernet.Ethernet(buf)  # getting connections
        if eth.type != dpkt.ethernet.ETH_TYPE_IP:  # check if Ip type
            continue

        ip = eth.data  # get ip data
        if ip.p != dpkt.ip.IP_PROTO_TCP:  # check if TCP protocol
            continue

        tcp = ip.data  # get tcp data
        ipSrc = inet_to_str(ip.src)  # human readable ip
        ipDst = inet_to_str(ip.dst)  # human readable ip
        tu = (tcp.sport, ipSrc, tcp.dport, ipDst)  # make up tcp flow start
        reverseTu = (tcp.dport, ipDst, tcp.sport, ipSrc)
        if tcp.flags == 0x02:  # flag is syn, i.e. first request connection
            throughput[tu] = len(tcp)  # initiate a port

            # index 0 indicates whether the first trans is still going on
            # index 1 indicates how many transactions has been sent
            # index 2 indicates what stage is the first transaction at
            # index 3 indicates what stage is the second transaction at
            synSeq[tu] = (False, 0, -1, -1)
            irtt[tu] = ts  # original timestamp
            rtt[tu] = ts  # original timestamp
            timeout[tu] = ({}, -1, ts)  # index 0 keeps the transactions, 1 keeps the count, 2 is the rtt
            cwnd[tu] = (-1, [], -1)  # array recording 3 size, -1 is count window
            tripleCount[tu] = (tcp.ack, 0, 0)  # first count dups, second count triple
            tripleArray[tu] = []  # array of requested triple acks
            twoTransactions[tu] = {}
            for name, value in dpkt.tcp.parse_opts(tcp.opts):  # getting the window scaling factor from options
                if name == 3:
                    winScaling[tu] = 2 ** int.from_bytes(value, "big")
            finalPrint[tu] = []  # initialize and add print statements
            finalPrint[tu].append(
                "TCP flow: (source port: " + str(tcp.sport) + ", source IP: " + ipSrc + ", dest port: " + str(
                    tcp.dport) + ", dest IP: " + ipDst + ")")
            # print flow
        elif tcp.flags & dpkt.tcp.TH_ACK and tcp.flags & dpkt.tcp.TH_SYN:  # if flag is [ack, syn]
            synSeq[reverseTu] = (False, 0, -1, -1)  # verify ack and syn
            irtt[reverseTu] = ts - irtt[reverseTu]
            timeout[reverseTu] = ({}, -1, ts - timeout[reverseTu][2])

        # elif tcp.flags & dpkt.tcp.TH_ACK and tcp.flags & dpkt.tcp.TH_PUSH:
        #     if tu in throughput.keys():  # increment throughput
        #         throughput[tu] = throughput[tu] + len(tcp)
        #
        #     if timeout[tu][1] == -1:  # mark when transaction start after [PSH, ACK]
        #         timeout[tu] = ({}, 0, timeout[tu][2])
        #
        #     if cwnd[tu][2] == -1:  # mark when transaction start after [PSH, ACK]
        #         cwnd[tu] = (ts, [0], 0)

        elif tcp.flags & dpkt.tcp.TH_FIN and tu in rtt:
            rtt[tu] = ts - rtt[tu]  # end of a flow, calculate overall rtt
        else:
            tcpSeq = tcp.seq  # sequence number
            tcpAck = tcp.ack  # ack number
            tcpWin = tcp.win  # window value
            if tu in synSeq.keys() and synSeq[tu][1] < 2:  # not yet three way, but should be third
                if tcp.flags == 0x10 and not synSeq[tu][0] and len(tcp.data) == 0:  # if only ack in third shake,
                    synSeq[tu] = (True, 0, -1, -1)  # set true since three way finished

                else:  # append transaction statements
                    if timeout[tu][1] == -1:  # mark when transaction start after handshake or piggy back
                        timeout[tu] = ({}, 0, timeout[tu][2])

                    if cwnd[tu][2] == -1:  # mark when transaction start after handshake or piggy back
                        cwnd[tu] = (ts, [0], 0)

                    fs = "first" if synSeq[tu][1] < 1 else "second"
                    finalPrint[tu].append(
                        "\tThe " + fs + " transaction from sender: \n\t\tseq: " + str(tcpSeq) + "\n\t\tACK number: " + str(
                            tcpAck) + "\n\t\tReceived window size: " + str(tcpWin *
                                                                       winScaling[tu])
                    )

                    if synSeq[tu][1] == 0:  # still on first transaction
                        synSeq[tu] = (True, synSeq[tu][1] + 1, tcp.seq + len(tcp.data), -1)
                    else:  # reached second request
                        synSeq[tu] = (True, synSeq[tu][1] + 1, synSeq[tu][2], tcp.seq + len(tcp.data))
            elif reverseTu in synSeq.keys() and synSeq[reverseTu][0] and (
                    tcp.ack == synSeq[reverseTu][2] or tcp.ack == synSeq[reverseTu][3]):  # receiver sends
                if tcp.ack == synSeq[reverseTu][2]:  # first response
                    finalPrint[reverseTu].append(
                        "\tThe first transaction from receiver: \n\t\tseq: " + str(tcpSeq) + "\n\t\tACK number: " + str(
                            tcpAck) + "\n\t\tReceived window size: " + str(tcpWin *
                                                                       winScaling[reverseTu])
                    )
                elif tcp.ack == synSeq[reverseTu][3]:  # second response
                    finalPrint[reverseTu].append(
                        "\tThe second transaction from the receiver: \n\t\tseq: " + str(tcpSeq) + "\n\t\tACK number: " + str(
                            tcpAck) + "\n\t\tReceived window size: " + str(tcpWin *
                                                                       winScaling[reverseTu])
                    )
                    # end of two transactions, set false
                    synSeq[reverseTu] = (False, synSeq[reverseTu][1], synSeq[reverseTu][2], synSeq[reverseTu][3])

            if tu in throughput.keys():  # increment throughput
                throughput[tu] = throughput[tu] + len(tcp)

            if tu in cwnd.keys() and -1 < cwnd[tu][2] < 3:  # increment packet number for current cwnd
                startTime = cwnd[tu][0]
                array = cwnd[tu][1]
                count = cwnd[tu][2]
                if irtt[tu] <= ts - startTime:  # if the currentTS - startTS > rtt interval, then next window
                    count += 1
                    if count < 3:
                        array.append(1)  # append the counter for next window
                    startTime = ts  # update start time
                else:
                    array[count] += 1  # increment counter
                cwnd[tu] = (startTime, array, count)

            if tu in timeout.keys():  # keep the transactions if sender
                inner = timeout[tu][0]
                inner[tcp.seq] = ts
            elif reverseTu in timeout.keys():  # if receiver sends, check time
                inner = timeout[reverseTu][0]
                count = timeout[reverseTu][1]
                newRTT = timeout[reverseTu][2]
                if tcp.ack in inner:  # if is responding to sender
                    timeDiff = ts - inner[tcp.ack]  # time of sender sends to receiver responds
                    if timeDiff >= newRTT * 2:  # if less than 2 * rtt
                        count += 1  # a potential time out
                    inner.pop(tcp.ack)  # get rid of the transaction after process
                timeout[reverseTu] = (inner, count, newRTT)  # update new timeout

        if reverseTu in tripleCount:  # sum triple count
            if tripleCount[reverseTu][0] == tcp.ack:  # if same ack, increment ack count
                if tripleCount[reverseTu][1] == 0:
                    tripleCount[reverseTu] = (tcp.ack, 2, tripleCount[reverseTu][2])
                else:
                    tripleCount[reverseTu] = (tcp.ack, tripleCount[reverseTu][1] + 1, tripleCount[reverseTu][2])
                if tcp.ack not in tripleArray[reverseTu] and tripleCount[reverseTu][1] >= 3:
                    tripleArray[reverseTu].append(tcp.ack)
            else:  # else increment triple count and update ack number
                count = tripleCount[reverseTu][2]
                # if tripleCount[reverseTu][1] >= 3:
                tripleCount[reverseTu] = (tcp.ack, 0, count)

        if tu in tripleArray and tcp.seq in tripleArray[tu]:  # if the sender resends a requested triple ack, count += 1
            tripleCount[tu] = (tripleCount[tu][0], tripleCount[tu][1], tripleCount[tu][2]+1)

    for sender in throughput.keys():  # print total throughput from each port
        finalPrint[sender].append("\tTotal throughput: " + str(throughput[sender] / rtt[sender]))

    for sender in cwnd.keys():  # print statement of cwnd sizes
        finalPrint[sender].append(
            "\tThree congestion windows in order: " + str(cwnd[sender][1])
        )

    for sender in tripleCount.keys():  # print statements of triple count
        triple = tripleCount[sender][2]
        finalPrint[sender].append("\tTotal number of triple ack: " + str(triple))

    for sender in timeout.keys():
        time = timeout[sender][1]
        finalPrint[sender].append(("\tTotal number of timeouts: " + str(time)))

    for flow in finalPrint.values():
        for prints in flow:
            print(prints)

        print()


if __name__ == "__main__":
    pcap_parse()
