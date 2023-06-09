import dataclasses
import socket, random, os, sys
from io import BytesIO
import struct
from dataclasses import dataclass
from typing import List
import pprint

# DNS can send and recieve "n" number of packets
# That's why we need to declare a buffer size
# the ip address here belongs to Quad9 (9.9.9.9)
ServerAddressPort = ("8.8.8.8", 53)
BufferSize: int = 1024

# it's the internet and here's for the other type values:
# https://datatracker.ietf.org/doc/html/rfc1035#section-3.2.2
CLASS_IN = 1
TYPE_A = 1
TYPE_NS = 2


# There are 13 Authoritative Nameservers (a-m).
# This is where we start making requests and then they point us 
# left or right. see: https://www.iana.org/domains/root/servers
ROOT_SERVERS = {
    "a.root-servers.net": "198.41.0.4", # Verisign, Inc.
    "b.root-servers.net": "199.9.14.201", # USC Information Sciences Institute
    "c.root-servers.net": "192.33.4.12", # Cogent Communications
    "d.root-servers.net": "199.7.91.13", # UMD
    "e.root-servers.net": "192.203.230.10", # NASA (AMES Research Center)
    "f.root-servers.net": "192.5.5.241", # Internet Systems Consortium
    "g.root-servers.net": "192.112.36.4", # US Department of Defense
    "h.root-servers.net": "198.97.190.53", # US Army (Research Lab)
    "i.root-servers.net": "192.36.148.17", # Netnod
    "j.root-servers.net": "192.58.128.30", # Verisign, Inc.
    "k.root-servers.net": "193.0.14.129", # RIPE NCC
    "l.root-servers.net": "199.7.83.42", # ICANN
    "m.root-servers.net": "202.12.27.33", # WIDE Project
}

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
    # RECURSION_DESIRED = 1 << 8
    RECURSION_NOT_DESIRED = 0
    header = UDPHeader(id, flags=RECURSION_NOT_DESIRED, QDCOUNT=1)
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

    if type_ == TYPE_NS:
        data = DecodeDomainName(reader)
    elif type_ == TYPE_A:
        data = IPToString(reader.read(data_len))
    else: 
        data = reader.read(data_len)

    return DNSResponse(name, type_, class_, ttl, data)


def LookupDNS(domain: str, type_: int) -> str:
    # if starts with www. remove
    query = MakeDNSQuery(domain, type_)

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

def ADNSLookup(ip: str, domain: str, type_: int) -> DNSPacket:
    query = MakeDNSQuery(domain, type_)
    UDPSock.sendto(query, (ip, 53))

    data, _ = UDPSock.recvfrom(BufferSize)
    response = DNSPacket
    response.parse_dns_packet(response, data)

    return response


def GetNameServer(packet: DNSPacket) -> str:
    for x in packet.authorities:
        if x.type_ == TYPE_NS:
            return x.data.decode('utf-8')
        
def GetAnswer(packet: DNSPacket) -> bytes:
    for x in packet.answers:
        if x.type_ == TYPE_A:
            return x.data
        
def GetNameServerIP(packet):
    for x in packet.additionals:
        if x.type_ == TYPE_A:
            return x.data
        
def ResolveDNS(domain: str, type_: int):
    name_server, name_server_ip = random.choice(list(ROOT_SERVERS.items()))

    while True:
        print(f"Querying {name_server} ({name_server_ip}) for {domain}")
        response = ADNSLookup(name_server_ip, domain, type_)

        if ip := GetAnswer(response):
            print("fin", ip)
            return ip
        elif ip := GetNameServerIP(response):
            name_server_ip = ip
            name_server = GetNameServer(response)
        elif ns_domain := GetNameServer(response):
            return ResolveDNS(ns_domain, TYPE_A)
        else:
            raise Exception("Unable to find IP address")

if __name__ == "__main__":
    domain = input("Enter domain name: \n")
    auth_server = input("Enter Authoritative Server: \n")
    ip = ResolveDNS(domain, 1)
    print(ip)

# what nameserver do we ask -> where does it send us -> 
# todo: add support for parsing ipv6
# todo: add tables