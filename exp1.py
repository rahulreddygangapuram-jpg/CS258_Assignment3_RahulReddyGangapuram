#!/usr/bin/env python3
from mininet.net import Mininet
from mininet.node import Node
from mininet.link import TCLink
from mininet.log import setLogLevel, info

# Linux router node with IPv4 forwarding enabled 
class LinuxRouter(Node):
    def config(self, **params):
        super().config(**params)
        # Enable IPv4 forwarding and relax reverse path filtering (multi-homed router interfaces)
        self.cmd('sysctl -w net.ipv4.ip_forward=1')
        self.cmd('sysctl -w net.ipv4.conf.all.rp_filter=0')
        self.cmd('sysctl -w net.ipv4.conf.default.rp_filter=0')
        self.cmd('for f in /proc/sys/net/ipv4/conf/*/rp_filter; do echo 0 > "$f"; done')

    def terminate(self):
        self.cmd('sysctl -w net.ipv4.ip_forward=0')
        super().terminate()

# Write a titled section into the results file
def W(fh, title, out):
    fh.write(f"\n--- {title} ---\n{(out or '').strip()}\n")

def run():
    # Create network
    net = Mininet(controller=None, link=TCLink)

    # Add routers
    info("*** Routers\n")
    r1 = net.addHost('r1', cls=LinuxRouter)
    r2 = net.addHost('r2', cls=LinuxRouter)

    # Add hosts
    info("*** Hosts\n")
    h1 = net.addHost('h1', ip='10.0.0.1/24')
    h2 = net.addHost('h2', ip='10.0.3.2/24')
    h3 = net.addHost('h3', ip='10.0.2.2/24')

    # Add links 
    info("*** Links (explicit interface names)\n")
    # h1 <-> r1
    net.addLink(h1, r1, intfName1='h1-eth0', intfName2='r1-eth0')
    # h2 <-> r1
    net.addLink(h2, r1, intfName1='h2-eth0', intfName2='r1-eth1')
    # r1 <-> r2
    net.addLink(r1, r2, intfName1='r1-eth2', intfName2='r2-eth0')
    # r2 <-> h3
    net.addLink(r2, h3, intfName1='r2-eth1', intfName2='h3-eth0')

    # Start the emulated network
    info("*** Start\n")
    net.start()

    # Ensure links are administratively up
    for n, ifs in {
        r1: ['r1-eth0','r1-eth1','r1-eth2'],
        r2: ['r2-eth0','r2-eth1'],
        h1: ['h1-eth0'],
        h2: ['h2-eth0'],
        h3: ['h3-eth0'],
    }.items():
        for i in ifs:
            n.cmd(f'ip link set {i} up')

    # Assign IPs on router interfaces
    def set_ip(node, ifname, cidr):
        node.cmd(f'ip addr flush dev {ifname}')
        node.cmd(f'ip addr add {cidr} dev {ifname}')

    # r1 side toward h1
    set_ip(r1, 'r1-eth0', '10.0.0.3/24')  

    # r1 side toward h2
    set_ip(r1, 'r1-eth1', '10.0.3.4/24')  

    # r1 side toward r2
    set_ip(r1, 'r1-eth2', '10.0.1.1/24')  

    # r2 side toward r1
    set_ip(r2, 'r2-eth0', '10.0.1.2/24')  

    # r2 side toward h3
    set_ip(r2, 'r2-eth1', '10.0.2.1/24')  

    # Configure host default routes, point to the local router
    h1.cmd('ip route replace default via 10.0.0.3')
    h2.cmd('ip route replace default via 10.0.3.4')
    h3.cmd('ip route replace default via 10.0.2.1')

    # Configure inter-router static routes
    # r1 learns how to reach 10.0.2.0/24 via r2
    # r2 learns how to reach 10.0.0.0/24 and 10.0.3.0/24 via r1
    r1.cmd('ip route replace 10.0.2.0/24 via 10.0.1.2')
    r2.cmd('ip route replace 10.0.0.0/24 via 10.0.1.1')
    r2.cmd('ip route replace 10.0.3.0/24 via 10.0.1.1')

    # Verify connectivity & record outputs
    with open('result1.txt', 'w') as fh:
        fh.write("Experiment 1: IP Routing results\n")

        # Neighbor sanity checks
        W(fh, "sanity: h1->r1 (10.0.0.3)", h1.cmd('ping -c1 10.0.0.3'))
        W(fh, "sanity: r1->r2 (10.0.1.2)", r1.cmd('ping -c1 10.0.1.2'))
        W(fh, "sanity: r2->r1 (10.0.1.1)", r2.cmd('ping -c1 10.0.1.1'))
        W(fh, "sanity: h3->r2 (10.0.2.1)", h3.cmd('ping -c1 10.0.2.1'))

        # Cross-subnet pings
        W(fh, "h1 -> h3 (10.0.2.2)", h1.cmd('ping -c1 10.0.2.2'))
        W(fh, "h2 -> h3 (10.0.2.2)", h2.cmd('ping -c1 10.0.2.2'))
        W(fh, "h3 -> h1 (10.0.0.1)", h3.cmd('ping -c1 10.0.0.1'))
        W(fh, "h3 -> h2 (10.0.3.2)", h3.cmd('ping -c1 10.0.3.2'))

        # IPs and routes on all nodes
        W(fh, "[r1 ip -br addr]", r1.cmd('ip -br addr'))
        W(fh, "[r2 ip -br addr]", r2.cmd('ip -br addr'))
        W(fh, "[r1 route]", r1.cmd('ip r'))
        W(fh, "[r2 route]", r2.cmd('ip r'))
        W(fh, "[h1 ip -br addr]", h1.cmd('ip -br addr'))
        W(fh, "[h2 ip -br addr]", h2.cmd('ip -br addr'))
        W(fh, "[h3 ip -br addr]", h3.cmd('ip -br addr'))

    info("See result1.txt\n")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
