import dataclasses
import socket, random, os, sys
from io import BytesIO
import struct
from dataclasses import dataclass
from typing import List

# DNS can send and recieve "n" number of packets
# That's why we need to declare a buffer size
# the ip address here belongs to Quad9 (9.9.9.9)
ServerAddressPort = ("8.8.8.8", 53)
BufferSize: int = 1024

# it's the internet and here's for the other type values:
# https://datatracker.ietf.org/doc/html/rfc1035#section-3.2.2
CLASS_IN = 1
TYPE_A = 1

# We can connect and bind. We would typically bind 
# if we wanted to be on the receiving end of UDP requests 
# and connect when we want to connect to a remote UDP server.
# setsockopt allows us to reuse the server after a shutdown.
# SOCK_DGRAM signifies UDP and AF_INET let's the computer know we're
# sending the packets over the internet.
UDPSock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
# UDPSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

@dataclass
class UDPHeader:
    id: int
    # Flags = (0 << 3) | 0 | 1
    flags: int
    QDCOUNT: int = 0
    ANCOUNT: int = 0
    NSCOUNT: int = 0
    ARCOUNT: int = 0

    # the ! let's python know we want the order of bytes in 
    # big endian (which is the goto with network packets) as 
    # opposed to little endian.
    # Q: should self not have a type?
    def get_bytes(self) -> bytes:
        header = dataclasses.astuple(self)
        header = struct.pack('!HHHHHH', *header)
        return header

@dataclass
class UDPQuestion:
    name: bytes
    type_: int
    class_: int

    def get_bytes(self) -> bytes:
        question = self.name + struct.pack("!HH", self.type_, self.class_)
        return question

@dataclass
class DNSResponse:
    name: bytes
    type_: int
    class_: int
    ttl: int
    data: bytes

class DNSPacket:
    header: UDPHeader
    questions: List[UDPQuestion]
    answers: List[DNSResponse]
    authorities: List[DNSResponse]
    additionals: List[DNSResponse]

    def parse_dns_packet(self, data):
        reader = BytesIO(data)
        header = ParseResponse(reader)
        questions = [ParseQuestion(reader) for _ in range(header.QDCOUNT)]
        answers = [ParseRecord(reader) for _ in range(header.ANCOUNT)]
        authorities = [ParseRecord(reader) for _ in range(header.NSCOUNT)]
        additionals = [ParseRecord(reader) for _ in range(header.ARCOUNT)]

        self.header = header
        self.questions = questions
        self.answers = answers
        self.authorities = authorities
        self.additionals = additionals

        return header, questions, answers, authorities, additionals

def EncodeDomainName(domain: str) -> bytes:
    encoding = b""
    parts = domain.split('.')

    for _, part in enumerate(parts):
        encoding += bytes([len(part)]) + part.encode()
    return encoding + b"\x00"

        # parts[index] = str(len(part)) + part
    # parts.append("\x0")
    # encoding = "".join(parts)

def DecodeDomainName(reader: BytesIO) -> bytes:
    parts = []
    while (length := reader.read(1)[0]) != 0:
        if length & 192:
            parts.append(DecodeCompressedDomain(length, reader))
            break
        else:
            parts.append(reader.read(length))
    return b'.'.join(parts)

def DecodeCompressedDomain(length: int, reader: BytesIO) -> bytes:
    pointer_bytes = bytes([length & 63]) + reader.read(1)
    pointer = struct.unpack("!H", pointer_bytes)[0]
    current_pos = reader.tell()
    reader.seek(pointer)
    result = DecodeDomainName(reader)
    reader.seek(current_pos)
    return result
 
def MakeDNSQuery(domain: str, type_: str):
    name = EncodeDomainName(domain)
    id = random.randint(0, 65535)
    RECUSRION_DESIRED = 1 << 8
    header = UDPHeader(id, flags=RECUSRION_DESIRED, QDCOUNT=1)
    question = UDPQuestion(name, type_, CLASS_IN)
    return header.get_bytes() + question.get_bytes()

# unmarshall dns reponse
def ParseResponse(reader) -> UDPHeader:
    items = struct.unpack("!HHHHHH", reader.read(12))
    return UDPHeader(*items)

def ParseQuestion(reader) -> UDPQuestion:
    name = DecodeDomainName(reader)
    data = reader.read(4)
    type_, class_ = struct.unpack("!HH", data)
    return UDPQuestion(name, type_, class_)

def ParseRecord(reader) -> DNSResponse:
    name = DecodeDomainName(reader)
    data = reader.read(10)
    type_, class_, ttl, data_len = struct.unpack("!HHIH", data)
    data = reader.read(data_len)
    return DNSResponse(name, type_, class_, ttl, data)


def LookupDNS(domain: str, type: int) -> str:
    query = MakeDNSQuery(domain, type)

    # the send method is typically used for TCP (which requires 
    # handshakes from clients to server) while sendto will need 
    # you to specify an intended udp server. You should 
    # be able to do this without needing to connect to the server.
    # Q: You know what's odd? You can't call socket.recvfrom (more info) after 
    # calling .recv (less info) is this because it has already been read?
    UDPSock.sendto(query, ServerAddressPort)
    data, _ = UDPSock.recvfrom(BufferSize)

    response = DNSPacket
    response.parse_dns_packet(response, data)

    return IPToString(response.answers[0].data)

def IPToString(IP: bytes) -> str:
    return ".".join([str(x) for x in IP])

# print(IPToString(ip))
# ParseResponse(reader)
# ParseQuestion(reader)
# ParseRecord(reader)


if __name__ == "__main__":
    domain = input("Enter domain name: \n")
    ip = LookupDNS(domain, 1)
    print(ip)