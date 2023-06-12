import os, sys
import src.resolver as r
import click
import tabulate

tutorial = '''
When you try to visit https://dotdotgo.com (or any other domain name), your browser has to figure out where 
the computer serving this site lives on the internet. In other words, it needs to find its IP address or resolve 
its domain name. To do this, your browser contacts a number of DNS servers starting from a root server to its 
response until the domain has been resolved.

There are only 13 authoritative root servers for the internet (controlled by ICANN) and each one holds information 
about top level domain name extensions. In our case, we’d be looking for one that has information about `.com` 
domains. Here’s a list of the 13 -> https://www.iana.org/domains/root/servers 

Note: We can send a request to any of these domains and be sure that it’ll redirect us to another nameserver if it 
does not hold records for whatever domain we’re looking for. Look, the root server is redirecting us to another 
nameserver (198.6.1.82) that may hold `.com` domains.

We finally have an answer! The nameserver responded with the domain for our initial request. So now we can connect 
to 131.193.179.160 to browse the site. But what if we wanted to find a subdomain, like subdot.dotdotgo.com? We 
would just need to make another query to the authoritative name server for our dotdotgo.com site.

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
You can also try
'''

# sample output for no tut scans
# encrypted-tbn0.gstatic.com
# ----------------------------------------
# Record Name . . . . . : encrypted-tbn0.gstatic.com
# Record Type . . . . . : 1
# Time To Live  . . . . : 142
# Data Length . . . . . : 4
# Section . . . . . . . : Answer
# A (Host) Record . . . : 142.250.180.14

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

def unmarshall_response(response: list[r.DNSResponse]):
    data = {}

    for x in response:
        data["Record Name"] = x.name
        data["Record Type"] = x.type_
        data["Time To Live"] = x.ttl
        data["Record Class"] = x.class_
        data["Record"] = x.data

    return data

def draw_table(data: dict):
    res = ''
    max_count = 0

    for k, v in data.items():
        line  = '{:.<20}: {}\n'.format(k, v)
        if len(line) > max_count:
            max_count = len(line)
        res = res + line

    return res, max_count

def block_print():
    sys.stdout = open(os.devnull, 'w')

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
    if type_value is None:
        type_value = "A"

    block_print()
    type_value = r.TYPES[type_value]
    _, response = r.ResolveDNS(domain, type_value)
    enable_print()



    if clean:
        data = unmarshall_response(response)
        table, width = draw_table(data)

        underline = '-' * width
        header = '\n{}\n{}\n'.format(domain, underline)

        table = header + table
        click.echo(table)
    else:
        return #tut

if __name__ == '__main__':
    dns_lookup()