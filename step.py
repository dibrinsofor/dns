from resolver import ResolveDNS
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