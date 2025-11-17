#!/usr/bin/env python3
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel, info
import os, time

# Write a titled section into the results file
def _write(fh, title, out):
    fh.write(f"\n--- {title} ---\n")
    fh.write(out.strip() + "\n")

def run():
    # Create network with OVS in standalone mode
    net = Mininet(controller=None, link=TCLink, switch=OVSKernelSwitch)

    # Add switches (standalone, OF13) 
    info("*** Add switches (standalone, OpenFlow13)\n")
    s1 = net.addSwitch('s1', failMode='standalone', protocols='OpenFlow13')
    s2 = net.addSwitch('s2', failMode='standalone', protocols='OpenFlow13')

    # Add hosts (single L2 subnet) 
    info("*** Add hosts\n")
    h1 = net.addHost('h1', ip='10.0.0.1/24')
    h2 = net.addHost('h2', ip='10.0.0.2/24')
    h3 = net.addHost('h3', ip='10.0.0.3/24')

    # Create links (controls port numbers on s1/s2) 
    info("*** Create links (controls port numbers)\n")
    # Port mapping based on link creation order:
    #   s1-eth1 <-> h1
    #   s1-eth2 <-> h2
    #   s1-eth3 <-> s2-eth1
    #   s2-eth2 <-> h3
    net.addLink(h1, s1)   
    net.addLink(h2, s1)   
    net.addLink(s1, s2)   
    net.addLink(s2, h3)   

    # Start the emulated network 
    info("*** Start network\n")
    net.start()

    # Optional pause: to run manual ovs-ofctl from another terminal
    if os.environ.get("HOLD") == "1":
        input("\n[exp2] Topology is up. In another terminal you can run:\n"
              "  sudo ovs-ofctl show s1\n"
              "  sudo ovs-ofctl dump-flows s1\n"
              '  sudo ovs-ofctl add-flow s1 "in_port=2,actions=drop"\n'
              '  sudo ovs-ofctl add-flow s1 "in_port=1,actions=output:3"\n'
              "Press ENTER here to continue and let the script do it automatically...\n")

    # Record baseline state, add flows, and test reachability 
    with open('result2.txt', 'w') as fh:
        fh.write("Experiment 2: SDN (L2) results\n")

        # Before adding flows: port state and flow table on s1
        _write(fh, "ovs-ofctl show s1 (before)",
               s1.cmd('ovs-ofctl -O OpenFlow13 show s1'))
        _write(fh, "ovs-ofctl dump-flows s1 (before)",
               s1.cmd('ovs-ofctl -O OpenFlow13 dump-flows s1'))

        # Baseline connectivity (standalone OVS learns MACs and forwards)
        _write(fh, "h1 -> h3 BEFORE", h1.cmd(f'ping -c 1 {h3.IP()}'))
        _write(fh, "h2 -> h3 BEFORE", h2.cmd(f'ping -c 1 {h3.IP()}'))

        # OpenFlow rules on s1
        # Drop all traffic that arrives IN on s1-eth2 (in_port=2)
        drop_cmd = 'ovs-ofctl -O OpenFlow13 add-flow s1 "in_port=2,actions=drop"'
        # Forward all traffic that arrives IN on s1-eth1 OUT to s1-eth3 (in_port=1 -> output:3)
        fwd_cmd  = 'ovs-ofctl -O OpenFlow13 add-flow s1 "in_port=1,actions=output:3"'

        # Record the exact commands used
        _write(fh, "Command used (drop all traffic from s1-eth2)", drop_cmd)
        _write(fh, "Command used (forward s1-eth1 -> s1-eth3)",   fwd_cmd)

        # Apply the flows on s1
        s1.cmd(drop_cmd)
        s1.cmd(fwd_cmd)

        # After adding flows: show the flow table reflects our policy
        _write(fh, "ovs-ofctl dump-flows s1 (after)",
               s1.cmd('ovs-ofctl -O OpenFlow13 dump-flows s1'))

        # Connectivity after policy enforcement
        # h1->h3 should work (steered to s1-eth3), h2->h3 should fail (dropped on in_port=2).
        _write(fh, "h1 -> h3 AFTER", h1.cmd(f'ping -c 1 {h3.IP()}'))
        _write(fh, "h2 -> h3 AFTER", h2.cmd(f'ping -c 1 {h3.IP()}'))

    info("See result2.txt\n")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()
