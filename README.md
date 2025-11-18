# CS 258 Assignment 3 — Experiment 1 (IP Routing) & Experiment 2 (SDN/L2)

This repo contains:

exp1.py — builds a routed topology (two Linux routers) and verifies end-to-end connectivity across multiple /24 subnets.

exp2.py — builds a two-switch OVS L2 topology and demonstrates OpenFlow control using ovs-ofctl.

Both scripts automatically write their outputs to text files:

result1.txt (Exp 1)

result2.txt (Exp 2)

## Steps to run:

Install Ubuntu.

Make sure mininet is installed.

Inside your project, open a terminal and run the below commands to execute Experiment 1

'''
sudo mn -c
sudo python3 exp1.py
cat result1.txt
'''

You will see the results saved to result1.txt

and for Experiment 2 run

'''
sudo mn -c
sudo HOLD=1 python3 exp2.py
'''

Open another terminal and run

'''
sudo ovs-ofctl -O OpenFlow13 show s1            | sudo tee -a result2.txt
sudo ovs-ofctl -O OpenFlow13 dump-flows s1      | sudo tee -a result2.txt

sudo ovs-ofctl -O OpenFlow13 add-flow s1 "in_port=2,actions=drop"       | sudo tee -a result2.txt
sudo ovs-ofctl -O OpenFlow13 add-flow s1 "in_port=1,actions=output:3"   | sudo tee -a result2.txt

sudo ovs-ofctl -O OpenFlow13 dump-flows s1      | sudo tee -a result2.txt
'''

You will see the results saved to result2.txt


