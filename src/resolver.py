import socket, sys

# DNS can send and recieve "n" number of packets
# That's why we need to declare a buffer size
# the ip address here belongs to Quad9
ServerAddressPort = ('9.9.9.9', 53)
BufferSize = 1024

# We can connect and bind. We would typically bind 
# if we wanted to be on the receiving end of UDP requests 
# and connect when we want to connect to a remote UDP server.
UDPSock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPSock.connect(ServerAddressPort)

# the send method is typically used for TCP (which requires 
# handshakes from clients to server) while sendto will need 
# you to specify an intended udp server. In theory you should 
# be able to do this without needing to connect to the server. 
# Try it out!
UDPSock.sendto()

LessInfo = UDPSock.recv(BufferSize)
MoreInfo = UDPSock.recvfrom(BufferSize)

print("Less: " + LessInfo + "\n")
print("More: " + MoreInfo + "\n")


def EncodeDomainName(DomainName: str) -> str:
    parts = DomainName.split(".")

# ["twitter", "com"]
    for index, part in enumerate(parts):
        parts[index] = str(len(part)) + part

    parts.append(r'0')
    encoding: str = "".join(parts)

    return encoding

# todo: write class make this dunder init method
def MakeQuestionHeader(QueryID: int) -> str:

    return

if __name__ == "__main__":
    print(EncodeDomainName("sdg.twitter.com"))
