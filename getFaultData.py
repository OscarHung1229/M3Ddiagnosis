from circuit import Circuit
import sys
import random

design = sys.argv[1]
cir = Circuit(design)
cir.parseHierVerilog("/home/sh528/M3Ddesigns/"+design+"/die0.v")
cir.parseHierVerilog("/home/sh528/M3Ddesigns/"+design+"/die1.v")
cir.parseTop("/home/sh528/M3Ddesigns/"+design+"/top.v")

n_faults = int(sys.argv[2])
faulty_gates = random.sample(cir.Gate, k=2*n_faults)
print("Start creating {} fault injection data".format(n_faults))

cnt = 0
fname = design+"/"+design+"_inject_w_MIV.dat"
with open(fname, "w") as f:
	f.write("Fault type  Faulty pin  Gate Level\n")

for name in faulty_gates:
	g = cir.Gate[name]
	if "SDFF" in g.gtype or "Dummy" in g.gtype:
		continue
	elif "test_se" in g.name:
		continue
	elif "clock" in g.name or "clk" in g.name:
		continue
	elif "reset" in g.name or "rst" in g.name:
		continue
	
	if g.gtype == "MIV":
		faulty_pin = "Z"
	else:
		faulty_pin = random.sample(g.pins, k=1)[0]
	
	if random.random() <= 0.5:
		fault_type = "r"
	else:
		fault_type = "f"

	with open(fname, "a") as f:
		f.write("{}  {}/{}  {}\n".format(fault_type, g.name, faulty_pin, g.level))

	cnt += 1

	if cnt == n_faults:
		break
