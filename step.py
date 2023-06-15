import os, sys
import src.resolver as r
import click
import tabulate
from math import ceil, floor
from tld import get_tld


fourth = """
As more and more devices now need to be on the internet, we can now resolve domain names to ipv6 addresses and not 
just ipv4 (like, 127.0.0.1 or 131.193.178.160).

But this seems like a slow process? Thankfully, it isn't. The average DNS lookup time is between 20 and 120 
milliseconds. To even improve this, the nameservers do a number of things: they cache domain names they encounter 
so that they can serve subsequent requests faster or optimize requests to return less information (AName instead 
of CName). When they cache records, they store them alongside TTLs (time to live) that tell the server how long 
to store this record. But in theory, the closer you are, physically, to the server you are looking for, the less 
time it should take. It should take me less time to resolve domain names (and receive resources) for servers in 
Lagos, Nigeria than ones in Nanjing, China.

And that’s it, you now know as much about DNS as I do.
"""

# if we need to use CNAME
# apis.google.com
# ----------------------------------------
# Record Name . . . . . : apis.google.com
# Record Type . . . . . : 5
# Time To Live  . . . . : 55
# Data Length . . . . . : 8
# Section . . . . . . . : Answer
# CNAME Record  . . . . : plus.l.google.com

# Record Name . . . . . : plus.l.google.com
# Record Type . . . . . : 1
# Time To Live  . . . . : 55
# Data Length . . . . . : 4
# Section . . . . . . . : Answer
# A (Host) Record . . . : 216.58.223.206

# Resolver.py "google.com" → point to this intro guide. Maybe it takes an optional domain name.
# Resolver.py –d “facebook.com” → no explanation just the boxes
# Resolver.py –t “twitter.com” {type} → just the IP address


class Query:
    auth_name_server: str
    auth_ip_address: str
    domain: str

    def __init__(self, data):
        self.auth_name_server = data[0]
        self.auth_ip_address = data[1]
        self.domain = data[2]


def unmarshall_response(response: list[r.DNSResponse]):
    data = {}

    for x in response:
        data["Record Name"] = x.name
        data["Record Type"] = x.type_
        data["Time To Live"] = x.ttl
        data["Record Class"] = x.class_
        data["Record"] = x.data

    return data

def format_line(line, max_length):
    half_dif = (max_length - len(line)) / 2 # in Python 3.x float division
    return '| ' + ' ' * ceil(half_dif) + line + ' ' * floor(half_dif) + ' |\n'

def boxed_msg(msg):
    lines = msg.split('\n')
    max_length = max([len(line) for line in lines])
    horizontal = '+' + '-' * (max_length + 2) + '+\n'
    res = horizontal
    for l in lines:
        res += format_line(l, max_length)
    res += horizontal
    return res.strip()

def arrow_msg(msg, dir):
    if dir == ">":
        line = "{:-^20}>".format(msg)
    elif dir == "<":
        line = "<{:-^20}".format(msg)
    else:
        return None
    return line

def insert_wspace(box):
    longest_line = 0
    
    for i in box:
        if longest_line < len(i):
            longest_line = len(i)
    
    line = ' ' * longest_line
    box.insert(1, line)
    box.insert(-1, line)

    return box

def make_diagram(x, max=None):
    if max is None:
        max = 0
    
    while True:
        if len(x[0]) == len(x[1]) == len(x[2]):
            for i in range(1, 7):
                print(' '.join(y[i] for y in x))  #this works
                # result = ''
                # for y in x:
                #     result += y[i]
                # print(result)
                return
        elif max > len(x[0]):
            x[0] = insert_wspace(x[0])
            # print(x[0])
            return make_diagram(x, max)
        elif max > len(x[1]):
            x[1] = insert_wspace(x[1])
            # print(x[1])
            return make_diagram(x, max)
        elif max > len(x[2]):
            x[2] = insert_wspace(x[2])
            # print(x[2])
            return make_diagram(x, max)


def draw_table(data: dict):
    res = ""
    max_count = 0

    for k, v in data.items():
        line = "{:.<20}: {}\n".format(k, v)
        if len(line) > max_count:
            max_count = len(line)
        res = res + line

    return res, max_count


def block_print():
    sys.stdout = open(os.devnull, "w")


# Restore
def enable_print():
    sys.stdout = sys.__stdout__


@click.command()
@click.option(
    "--clean",
    "-c",
    help="Simple DNS query without tutorial",
    is_flag=True,
    default=False,
    is_eager=True,
)
@click.option(
    "--type-value",
    "-t",
    type=click.Choice(r.TYPES.keys(), case_sensitive=False),
    help="DNS query with specific record type",
)
@click.argument("domain", type=click.STRING)
def dns_lookup(domain, type_value, clean):
    tld = get_tld("https://"+domain)
    if tld is None: #make assumption
        tld = domain.split(".")
        tld = tld[len(tld) - 1]

    if type_value is None:
        type_value = "A"

    block_print()
    type_value = r.TYPES[type_value]
    data, response, ip = r.ResolveDNS(domain, type_value)
    enable_print()

    if clean:
        data = unmarshall_response(response)
        table, width = draw_table(data)

        underline = "-" * width
        header = "\n{}\n{}\n".format(domain, underline)

        table = header + table
        click.echo(table)
    else:
        query_data = []
        for x in data:
            query = Query(x)
            query_data.append(query)

        for x in query_data:

            match query_data.index(x):
                case 0:
                    first = "When you try to visit {} (or any other domain name), your browser has to figure out where the computer serving this site lives on the internet. In other words, it needs to find its IP address or resolve its domain name. To do this, your browser contacts a number of DNS servers starting from a root server to its response until the domain has been resolved.\n{}"
                    # make diagram
                    box1 = '''\n{}\n'''.format(boxed_msg("Your\ncomputer")) 
                    box2 = '''\n{}\n'''.format(boxed_msg("{}\n({})\n\nroot server".format(query_data[0].auth_ip_address, query_data[0].auth_name_server)))
                    arrows = '''\n{}\n{}\n'''.format(arrow_msg(query_data[0].domain, ">"), arrow_msg("&{}:{}".format(tld, query_data[1].auth_ip_address), "<"))
                    
                    max = 0
                    x = [box1.split('\n'), arrows.split('\n'), box2.split('\n')]
                    for y in x:
                        if max < len(y):
                            max = len(y)

                    diagram = make_diagram(x, max)
                    first = first.format(query_data[0].domain, diagram)
                    print(first)
                case 1:
                    diagram = ''
                    second = "There are only 13 authoritative root servers for the internet (controlled by ICANN) and each one holds information about nameservers that point to specific top level domain name extensions. In our case, we’d be looking for one that has information about `.com` domains. Here’s a list of the other 12 -> https://www.iana.org/domains/root/servers.\n\nNote: We can send a request to any of these domains and be sure that it’ll redirect us to another nameserver if it does not hold records for whatever domain we’re looking for. Look, the root server is redirecting us to another nameserver ({}) that may hold `{}` domains."
                    second = second.format(query_data[1].auth_ip_address, tld, diagram)
                    print(second)
                case _ if query_data.index(x) == len(query_data) -1:
                    diagram = ''
                    third = "We finally have an answer! The nameserver responded with the IP for our initial request, {}, and we can now browse the site. But what if we wanted to find a subdomain, like subdomain.{}? We would just need to make another query to the authoritative name server for our {} site.\n{}"
                    third = third.format(ip, domain, domain, diagram)
                    print(third)
                case _:
                    # default case
                    diagram = 'farts'
                    print(diagram)
                    

        return  # tut


if __name__ == "__main__":
    dns_lookup()
