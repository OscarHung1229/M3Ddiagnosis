import sys
import time
from operator import itemgetter	
import random

#Global matrix for signal propagation
NotMap = [1, 0, 2, 4, 3]
TransMap = [
	[0, 3, 2, 0, 3],
 	[4, 1, 2, 4, 1]
]	
AndMap = [
	[0, 0, 0, 0, 0],
	[0, 1, 2, 3, 4],
	[0, 2, 2, 2, 0],
	[0, 3, 2, 3, 0],
	[0, 4, 0, 0, 4]
] 
OrMap = [
	[0, 1, 2, 3, 4],
	[1, 1, 1, 1, 1],
	[2, 1, 2, 1, 2],
	[3, 1, 1, 3, 1],
	[4, 1, 2 ,1 ,4]
]

XorMap = [
	[0, 1, 2, 3, 4],
	[1, 0, 2, 4, 3],
	[2, 2, 2, 2, 2],
	[3, 4, 2, 0, 1],
	[4, 3, 2, 1, 0]
]


class Gate:
	def __init__(self, gtype, name, die = 1):
		self.gtype = gtype			#Gate type
	 	self.level = -1					#Level in the circuit
	 	self.name = name				#Gate name
	 	self.pins = {}					#Input/Output pins
		self.die = die					#Die0/Die1
		self.initvalue = 99			#Record inital state for TDF patterns
		self.outpin = []				#Output pin
		
	def add_pins(self, ptype, wire):
		self.pins[ptype] = wire
	def set_level(self,l):
		self.level = l
	

	def ev(self, first, debug = False):
	
		value = -1
		if "INV" in self.gtype:
				if self.pins["A"].value == 99:
					print(self.pins["A"].name)
				self.pins["ZN"].set_value(NotMap[self.pins["A"].value], first)
			
		elif "AND" in self.gtype:
			for p in self.pins:
				pin = self.pins[p]
				if "Z" in p:
					continue
				if value == -1:
					value = pin.value
				else:
					value = AndMap[value][pin.value]
			if "NAND" in self.gtype:
				self.pins["ZN"].set_value(NotMap[value], first)
			else: 
				self.pins["ZN"].set_value(value, first)

		elif self.gtype.startswith("OR") or self.gtype.startswith("NOR"):
			for p in self.pins:
				pin = self.pins[p]
				if "Z" in p:
					continue
				if value == -1:
					value = pin.value
				else:
					value = OrMap[value][pin.value]
			if "NOR" in self.gtype:
				self.pins["ZN"].set_value(NotMap[value], first)
			else: 
				self.pins["ZN"].set_value(value, first)
		
		elif self.gtype.startswith("XOR"):
			self.pins["Z"].set_value(XorMap[self.pins["A"].value][self.pins["B"].value], first)
			
		elif self.gtype.startswith("XNOR"):
			self.pins["ZN"].set_value(NotMap[XorMap[self.pins["A"].value][self.pins["B"].value]], first)

		elif self.gtype.startswith("AOI21_"):
			value = AndMap[self.pins["B1"].value][self.pins["B2"].value]
			value = OrMap[self.pins["A"].value][value]
			self.pins["ZN"].set_value(NotMap[value], first)

		elif self.gtype.startswith("AOI22_"):
			v1 = AndMap[self.pins["B1"].value][self.pins["B2"].value]
			v2 = AndMap[self.pins["A1"].value][self.pins["A2"].value]
			value = OrMap[v1][v2]
			self.pins["ZN"].set_value(NotMap[value], first)
			
		elif self.gtype.startswith("AOI211_"):
			value = AndMap[self.pins["C1"].value][self.pins["C2"].value]
			value = OrMap[self.pins["B"].value][value]
			value = OrMap[self.pins["A"].value][value]
			self.pins["ZN"].set_value(NotMap[value], first)

		elif self.gtype.startswith("AOI221_"):
			v1 = AndMap[self.pins["C1"].value][self.pins["C2"].value]
			v2 = AndMap[self.pins["B1"].value][self.pins["B2"].value]
			value = OrMap[self.pins["A"].value][v1]
			value = OrMap[v2][value]
			self.pins["ZN"].set_value(NotMap[value], first)

		elif self.gtype.startswith("AOI222_"):
			v1 = AndMap[self.pins["C1"].value][self.pins["C2"].value]
			v2 = AndMap[self.pins["B1"].value][self.pins["B2"].value]
			v3 = AndMap[self.pins["A1"].value][self.pins["A2"].value]
			value = OrMap[v1][v2]
			value = OrMap[v3][value]
			self.pins["ZN"].set_value(NotMap[value], first)
				
		elif self.gtype.startswith("OAI21_"):
			v1 = OrMap[self.pins["B1"].value][self.pins["B2"].value]
			value = AndMap[v1][self.pins["A"].value]	
			self.pins["ZN"].set_value(NotMap[value], first)

		elif self.gtype.startswith("OAI22_"):
			v1 = OrMap[self.pins["B1"].value][self.pins["B2"].value]
			v2 = OrMap[self.pins["A1"].value][self.pins["A2"].value]
			value = AndMap[v1][v2]
			self.pins["ZN"].set_value(NotMap[value], first)

		elif self.gtype.startswith("OAI211_"):
			v1 = OrMap[self.pins["C1"].value][self.pins["C2"].value]
			value = AndMap[v1][self.pins["A"].value]	
			value = AndMap[value][self.pins["B"].value]	
			self.pins["ZN"].set_value(NotMap[value], first)

		elif self.gtype.startswith("OAI221_"):
			v1 = OrMap[self.pins["C1"].value][self.pins["C2"].value]
			v2 = OrMap[self.pins["B1"].value][self.pins["B2"].value]
			value = AndMap[v1][self.pins["A"].value]	
			value = AndMap[value][v2]
			self.pins["ZN"].set_value(NotMap[value], first)

		elif self.gtype.startswith("OAI222_"):
			v1 = OrMap[self.pins["C1"].value][self.pins["C2"].value]
			v2 = OrMap[self.pins["B1"].value][self.pins["B2"].value]
			v3 = OrMap[self.pins["A1"].value][self.pins["A2"].value]
			value = AndMap[v1][v2]
			value = AndMap[value][v3]
			self.pins["ZN"].set_value(NotMap[value], first)

		elif self.gtype.startswith("OAI33_"):
			v1 = OrMap[self.pins["B1"].value][self.pins["B2"].value]
			v2 = OrMap[self.pins["B3"].value][v1]
			v3 = OrMap[self.pins["A1"].value][self.pins["A2"].value]
			v4 = OrMap[self.pins["A3"].value][v3]
			value = AndMap[v2][v4]
			self.pins["ZN"].set_value(NotMap[value], first)

		elif self.gtype.startswith("MUX"):
			v1 = AndMap[self.pins["A"].value][NotMap[self.pins["S"].value]]
			v2 = AndMap[self.pins["B"].value][self.pins["S"].value]
			self.pins["Z"].set_value(OrMap[v1][v2], first)

		elif self.gtype.startswith("FA"):
			v1 = XorMap[self.pins["A"].value][self.pins["B"].value]
			self.pins["S"].set_value(XorMap[v1][self.pins["CI"].value], first)
			v2 = OrMap[self.pins["A"].value][self.pins["B"].value]
			v3 = AndMap[v2][self.pins["CI"].value]
			v4 = AndMap[self.pins["A"].value][self.pins["B"].value]
			self.pins["CO"].set_value(OrMap[v3][v4], first)

		elif "DFF" in self.gtype:
			if self.pins["Q"].value == 99:
				self.pins["Q"].set_value(self.pins["D"].value, first)
				if "QN" in self.pins:
					self.pins["QN"].set_value(NotMap[self.pins["D"].value], first)
			else:
				value = TransMap[self.pins["Q"].value][self.pins["D"].value]
				self.pins["Q"].set_value(value, first)
				if "QN" in self.pins:
					self.pins["QN"].set_value(NotMap[value], first)
				

		else:
			self.pins["Z"].set_value(self.pins["A"].value, first)


class Wire:
	def __init__(self, wtype, name):
		self.wtype = wtype			#Wire type
		self.value = 99					#Signal on this wire
		self.name = name				#Wire name
 		self.fanin = 0					#Fanin gate
		self.fanout = []				#Fanout gates	
		self.v1 	 = 99					#Value of v1
		self.v2		 = 99					#Value of v2
		self.prob	 = -1.0				#Prob for preferred fill
	
	def connect(self, gate, direction):
		if direction == "IN":
			self.fanin = gate
			gate.outpin.append(self)
		else:
			self.fanout.append(gate)
	
	def set_value(self, v, first):
		self.value = v
		if first:
			self.v1 = v
			if v == 2:
				self.prob = 0.5
			else:
				self.prob = float(v)
		else:
			self.v2 = v

class Circuit:
	def __init__(self, design):
		self.Pi = [] 						#Primary Input
		self.Po = []						#Primary Output
		self.Wire = {}					#Wires
		self.Gate = {}					#Standard Cell Gates
		self.sorted_Gate = {}		#Sorted gates by their levels
		self.scanchains = []		#Scanchains
		self.maxlevel = -1			#Maxlevel
		self.design = design
		self.WSA = []						#For WSA calculation
		self.prefix = []				#For ILP intermediate pattern
		self.sopin = []					#For dumpFaultSTIL
		self.faulty_gate = 0		#For fault injection
		self.faulty_pin = 0			#For fault injection
		self.defect = ""				#For fault injection

	def debug(self):
		cnt0 = 0
		cnt1 = 0
		for g in self.Gate:
			if self.Gate[g].die == 0:
				cnt0 += 1
			else:
				cnt1 += 1
		print("Die0 gate count: {0}".format(cnt0))
		print("Die1 gate count: {0}".format(cnt1))

	def reset(self):
		for w in self.Wire:
			self.Wire[w].set_value(99, True)
			self.Wire[w].v2 = 99
			self.Wire[w].prob = -1

		if self.design == "netcard":
			self.Wire["net1"].set_value(0, True)
			self.Wire["net1"].set_value(0, False)
			self.Wire["net8"].set_value(0, True)
			self.Wire["net8"].set_value(0, False)
		elif self.design == "netcard_GNN":
			self.Wire["net1"].set_value(0, True)
			self.Wire["net1"].set_value(0, False)
			self.Wire["net2"].set_value(0, True)
			self.Wire["net2"].set_value(0, False)
			self.Wire["net3"].set_value(0, True)
			self.Wire["net3"].set_value(0, False)
			self.Wire["net10"].set_value(0, True)
			self.Wire["net10"].set_value(0, False)
	
	#Verilog Parser
	def parseVerilog(self, infile):
		print("Start parsing verilog netlist")
		begin = time.time()
		f = open(infile, "r")
		
		for line in f:
			if ");" in line:
				break

		#Parse Primary Inputs
		for line in f:
			l = line.strip().strip(";")
			wires = l.split(",")
			for w in wires:
				if ("input" in w):
					w = w.replace("input","")
				elif not w:
					continue
				name = w.strip()
				newWire = Wire("PI", name)
				self.Wire[name] = newWire
			
			if ";" in line:
				break	

		#Parse Primary Outputs
		for line in f:
			l = line.strip().strip(";")
			wires = l.split(",")
			for w in wires:
				if ("output" in w):
					w = w.replace("output","")
				elif not w:
					continue
				name = w.strip()
				newWire = Wire("PO", name)
				self.Wire[name] = newWire
			
			if ";" in line:
				break	
			
		#Parse Wires
		for line in f:
			l = line.strip().strip(";")
			wires = l.split(",")
			for w in wires:
				if ("wire " in w):
					w = w.replace("wire ","")
				elif not w:
					continue
				name = w.strip()
				newWire = Wire("WIRE", name)
				self.Wire[name] = newWire
			
			if ";" in line:
				break	
		
		#Direct assign
		for line in f:
			if "assign" not in line:
			 break
			words = line.split()
			inwire = words[3].strip(";")
			outwire = words[1]
			
			gname = "Dummy_" + inwire
			newGate = Gate("Dummy", gname)
			newGate.add_pins("A", self.Wire[inwire])
			self.Wire[inwire].connect(newGate, "OUT")
			newGate.add_pins("Z", self.Wire[outwire])
			self.Wire[outwire].connect(newGate, "IN")
			self.Gate[gname] = newGate
			
		i = 0
		#Parse Gates
		l = ""
		for line in f:
			if not line:
				continue
			elif "endmodule" in line:
				break
			l += line.strip()
			if ";" not in line:
				continue
			
			gtype = l.split()[0]
			name = l.split()[1]
			newGate = Gate(gtype, name)

			pins = l.split(",")
			for p in pins:
				idx1 = p.find(".")
				idx2 = p.find("(", idx1)
				idx3 = p.find(")", idx2)
				
				ptype = p[idx1+1:idx2].strip()
				wire = p[idx2+1:idx3].strip()
				newGate.add_pins(ptype, self.Wire[wire])
				if "Z" in ptype:
					self.Wire[wire].connect(newGate, "IN")
				elif "CO" in ptype:
					self.Wire[wire].connect(newGate, "IN")
				elif "Q" in ptype:
					self.Wire[wire].connect(newGate, "IN")
				elif ptype == "S" and gtype.startswith("FA"):
					self.Wire[wire].connect(newGate, "IN")
				else:
					self.Wire[wire].connect(newGate, "OUT")
					

			self.Gate[name] = newGate
			l = ""
		
		f.close()

		end = time.time()
		print("End parsing verilog netlist\nCPU time: {0:.2f}s\n".format(end-begin))
		
	def parsePartition(self, filename):
		print("Start parsing partition report")
		begin = time.time()
		f = open(filename, "r")
		for line in f:
			name = line.rstrip()
			self.Gate[name].die = 0
		f.close()
		end = time.time()
		print("End parsing partition report\nCPU time: {0:.2f}s\n".format(end-begin))
			
				
	def levelize(self):
		for p in self.Pi:
			self.levelize_dfs(p, 1)
		for sc in self.scanchains:
			for gate in sc:
				gate.set_level(0)
				self.levelize_dfs(gate.pins["Q"], 1)
				if "QN" in gate.pins:
					self.levelize_dfs(gate.pins["QN"], 1)

		#print("Max level:" + str(self.maxlevel))
		
		self.sorted_Gate = [[] for x in range(self.maxlevel+1)]
		for g in self.Gate:
			gate = self.Gate[g]
			l = gate.level
			self.sorted_Gate[l].append(gate)
	
	def levelize_dfs(self, wire, level):
		for gate in wire.fanout:
			if "DFF" in gate.gtype:
				continue
			if gate.level < level:
				gate.set_level(level)
				self.maxlevel = max(level, self.maxlevel)
				if "Z" in gate.pins:
					self.levelize_dfs(gate.pins["Z"], level+1)
				if "ZN" in gate.pins:
					self.levelize_dfs(gate.pins["ZN"], level+1)
				if "CO" in gate.pins:
					self.levelize_dfs(gate.pins["CO"], level+1)
				if "S" in gate.pins and gate.gtype.startswith("FA"):
					self.levelize_dfs(gate.pins["S"], level+1)
	
	def parseSTIL(self, infile):
		print("Start parsing STIL patterns")
		begin = time.time()

		f = open(infile, "r")
		chain = []

		
		for line in f:
			if "SignalGroups" in line:
				break

		#PI
		for line in f:
			words = line.split("\"")
			for name in words:
				if name in self.Wire:
					self.Pi.append(self.Wire[name])	
			if ";" in line:
				break

		for i in range(2):
			for line in f:
				if ";" in line:
					break

		#PO
		for line in f:
			words = line.split("\"")
			for name in words:
				if name in self.Wire:
					self.Po.append(self.Wire[name])	
			if ";" in line:
				break

		#Scan Chains
		inchain = False
		for line in f:
			if "PatternBurst" in line:
				break

			if "ScanOut " in line:
				word = line.rstrip().split()[-1]
				self.sopin.append(word[1:-2])
				continue

			if not inchain:
				if "ScanCells" not in line:
					continue

			inchain = True
			for words in line.split("\""):
				if "." not in words:
					continue
				idx1 = words.find(".")+1
				idx2 = words.find(".", idx1+1)
				name = words[idx1:idx2]
				chain.append(self.Gate[name])
			
			if ";" in line:
				inchain = False
				self.scanchains.append(chain)
				chain = []
		
		#Levelization after parsing scan chains
		self.levelize()
		#self.dumpSTILprefix(infile)
		self.injectfault()

		for line in f:
			if "pattern 0" in line:
				break

		idx1 = infile.find("/")
		idx2 = infile.find(".stil")
		rptname = infile[idx1+1:idx2]
		with open(self.design+"/"+rptname+".log", "w") as flog:
			flog.write(".pattern_file_name {0}.stil\n".format(rptname))
		
		#Patterns
		finalpattern = False
		cnt = -1
		while not finalpattern:
			cnt += 1
			step = "load"
			si = []
			launch = []
			capture = []
			so = []
				
			l = ""
			count = 0
			
			for line in f:
				if "Ann" in line:
					continue
				elif "Call" in line:
					if "capture" in line and step == "launch":
					 	step = "capture"
					elif "multiclock_capture" in line and cnt != 0:
					 	step = "launch"
					elif "multiclock_capture" in line and cnt == 0:
					 	step = "capture"
					elif "allclock_launch" in line:
					 	step = "launch"
					elif (step == "capture") and ("load" in line):
					 	step = "unload"

					if "end" in line:
						print("Final Pat")
						finalpattern = True
					continue

				l += line.strip()
				if ";" not in line:
					continue
				else:
					idx1 = l.find("=")+1
					idx2 = l.find(";")
					subline = l[idx1:idx2]
					if step == "load":
						si.append(subline)
					elif step == "launch":
						launch.insert(0, subline)
					elif step == "capture":
						capture.append(subline)
					elif step == "unload":
						so.append(subline)
						count += 1
						if count == len(self.scanchains):
							break
					l = ""

			if cnt == 0:
				print("Pass Pattern {0}".format(cnt))
				continue


			if cnt == 199:
				finalpattern = True

			if self.test(si, launch, capture, so, cnt, infile, finalpattern):
				print("Pattern {0} success!".format(cnt))
			else:
				print("Pattern {0} failed!".format(cnt))


		f.close()
		endtime = time.time()
		print("End parsing STIL patterns\nCPU time: {0:.2f}s\n".format(endtime-begin))

	def evaluate(self, first):
		cost = 0
		if "ldpc" in self.design and not first:
			for w in self.Pi:
				if w.v2 != 2 and w.v2 != 99:
					w.set_value(w.v2, False)
				else:
					w.set_value(w.v1, False)
					#assert(w.v1 != 2)

		for i in range(len(self.sorted_Gate)):
			gates = self.sorted_Gate[i]	
			if i == 0:
				# Renew PPI
				if not first:
					l = []
					for g in gates:
						vD = g.pins["D"].value
						vQ = g.pins["Q"].value
						if vD == vQ:
							l.append(vD)
						elif vD == 2:
							l.append(2)
						elif vQ == 2:
							l.append(vD)
						elif vD == 1 and vQ == 0:
							l.append(3)
							if g.die == 0:
								cost += len(g.pins["Q"].fanout) + 1
						elif vD == 0 and vQ == 1:
							l.append(4)
							if g.die == 0:
								cost += len(g.pins["Q"].fanout) + 1
						else:
							print("D: " + str(vD))
							print("Q: " + str(vQ))
							assert(False)
					
					for i in range(len(gates)):
						g = gates[i]
						g.pins["Q"].set_value(l[i], first)
						if "QN" in g.pins:
							if l[i] < 2:
								g.pins["QN"].set_value(1-l[i], first)
							elif l[i] == 2:
								g.pins["QN"].set_value(2, first)
							elif l[i] == 3:
								g.pins["QN"].set_value(4, first)
								if g.die == 0:
									cost += len(g.pins["QN"].fanout) + 1
							elif l[i] == 4:
								g.pins["QN"].set_value(3, first)
								if g.die == 0:
									cost += len(g.pins["QN"].fanout) + 1
							else:
								assert(False)

						if g.name == "r909_reg":
							print("Start")
							print(g.pins["Q"].value)
					
				else:
					for g in gates:
						if g.pins["Q"].value == 99:
							print("False " + g.name + " " + g.pins["D"].name + " " + str(g.pins["D"].value))
						elif "QN" in g.pins and g.pins["QN"].value == 99:
							print("False " + g.name + " " + g.pins["D"].name + " " + str(g.pins["D"].value))
						
			else:	
				for g in gates:
					if g.name == self.faulty_gate and not first:
						if g.pins[self.faulty_pin] in g.outpin:
							g.ev(first)
							print(g.pins[self.faulty_pin].value)
							if self.defect == "str" and g.pins[self.faulty_pin].value == 3:
								g.pins[self.faulty_pin].set_value(0,first)
							elif self.defect == "stf" and g.pins[self.faulty_pin].value == 4:
								g.pins[self.faulty_pin].set_value(1,first)
						else:
							if self.defect == "str" and g.pins[self.faulty_pin].value == 3:
								g.pins[self.faulty_pin].set_value(0,first)
								g.ev(first)
								#g.pins[self.faulty_pin].set_value(3,first)
							elif self.defect == "stf" and g.pins[self.faulty_pin].value == 4:
								g.pins[self.faulty_pin].set_value(1,first)
								g.ev(first)
								#g.pins[self.faulty_pin].set_value(4,first)
						continue
						
					g.ev(first)
					if not first and g.die == 0:
						for w in g.outpin:
							if w.value > 2:
								cost += len(w.fanout) + 1
					
		return cost
					

	def test(self, si, launch, capture, so, pat, infile, end):
		idx1 = infile.find("/")
		idx2 = infile.find(".stil")
		rptname = infile[idx1+1:idx2]

		if len(launch) == 0:
		 return True

		self.reset()


		#Assign scan chains
		for i in range(len(si)):
			scanvalue = si[i][::-1]
			scanchain = self.scanchains[i]
			assert len(scanvalue) == len(scanchain)
			for j in range(len(scanvalue)):
				if scanvalue[j] == "N":
					scanchain[j].pins["Q"].set_value(2, True)
					if "QN" in scanchain[j].pins:
						scanchain[j].pins["QN"].set_value(2, True)
				else:
					v = int(scanvalue[j])
					scanchain[j].pins["Q"].set_value(v, True)
					if "QN" in scanchain[j].pins:
						scanchain[j].pins["QN"].set_value(1-v, True)
		
		#Launch
		pulse = False
		reset = False
		for i in range(len(launch[0])):
			v = 0
			if launch[0][i] == "P":
				v = 1
				if self.Pi[i].name == "clk" or self.Pi[i].name == "clock" or self.Pi[i].name == "ispd_clk":
					pulse = True
				else:
					reset = True
			elif launch[0][i] == "1":
				v = 1
			elif launch[0][i] == "N":
				v = 2
			self.Pi[i].set_value(v, True)


		#Evaluate to launch transition at SIs
		if pulse:
			c1 = self.evaluate(True)

		#Capture
		for i in range(len(capture[0])):
			v = 0
			if capture[0][i] == "P" or capture[0][i] == "1":
				v = 1
			elif capture[0][i] == "N":
				v = 2
			self.Pi[i].set_value(v, False)

		c2 = self.evaluate(False)

		result = True
		f_capture = []
		f_capture.append(capture[0])
		f_so = []
		#Output at POs	
		l_po = ""
		for i in range(len(capture[1])):
			#print(capture[1][i])
			if self.Po[i].value == 99:
				l_po += "X"
				continue

			if self.Po[i].value == 0 or self.Po[i].value == 4:
				l_po += "L"
				if capture[1][i] == "H":
					print("Error at PO " + self.Po[i].name + " " + str(self.Po[i].value))
					with open(self.design+"/"+rptname+".log", "a") as flog:
						flog.write("   {0}  {1}\n".format(pat,self.Po[i].name))
					result = False
			elif self.Po[i].value == 1 or self.Po[i].value == 3:
				l_po += "H"
				if capture[1][i] == "L":
					print("Error at PO " + self.Po[i].name + " " + str(self.Po[i].value))
					with open(self.design+"/"+rptname+".log", "a") as flog:
						flog.write("   {0}  {1}\n".format(pat,self.Po[i].name))
					result = False
		f_capture.append(l_po)	
			#if capture[1][i] == "L":
			#	if self.Po[i].value != 0 and self.Po[i].value != 4:
			#		print("Error at PO " + self.Po[i].name + " " + str(self.Po[i].value))
			#		with open(self.design+"/"+rptname+".log", "a") as flog:
			#			flog.write("   {0}  {1}\n".format(pat,self.Po[i].name))
			#		result = False
			#else:
			#	if self.Po[i].value != 1 and self.Po[i].value != 3:
			#		print("Error at PO " + self.Po[i].name + " " + str(self.Po[i].value))
			#		with open(self.design+"/"+rptname+".log", "a") as flog:
			#			flog.write("   {0}  {1}\n".format(pat,self.Po[i].name))
			#		result = False


		#Output at SOs
		for i in range(len(so)):
			l_so = ""
			scanvalue = so[i][::-1]
			scanchain = self.scanchains[i]
			for j in range(len(scanvalue)):
				if scanchain[j].pins["D"].value == 0 or scanchain[j].pins["D"].value == 4:
					l_so += "L"
					if scanvalue[j] == "H":
			 			print("Error at SO " + scanchain[j].name + " " + str(scanchain[j].pins["D"].value))
						with open(self.design+"/"+rptname+".log", "a") as flog:
							flog.write("   {0}  {1}  {2}  (exp=1, got=0)\n".format(pat,self.sopin[i],len(scanvalue)-1-j))
						result = False
				elif scanchain[j].pins["D"].value == 1 or scanchain[j].pins["D"].value == 3:
					l_so += "H"
					if scanvalue[j] == "L":
			 			print("Error at SO " + scanchain[j].name + " " + str(scanchain[j].pins["D"].value))
						with open(self.design+"/"+rptname+".log", "a") as flog:
							flog.write("   {0}  {1}  {2}  (exp=0, got=1)\n".format(pat,self.sopin[i],len(scanvalue)-1-j))
						result = False
			f_so.append(l_so[::-1])



			#	if scanvalue[j] == "L":
			#		if scanchain[j].pins["D"].value != 0 and scanchain[j].pins["D"].value != 4:
			#	 		print("Error at SO " + scanchain[j].name + " " + str(scanchain[j].pins["D"].value))
			#			with open(self.design+"/"+rptname+".log", "a") as flog:
			#				flog.write("   {0}  {1}  {2}  (exp=0, got=1)\n".format(pat,self.sopin[i],len(scanvalue)-1-j))
			#			result = False
			#	else:
			#		if scanchain[j].pins["D"].value != 1 and scanchain[j].pins["D"].value != 3:
			#			print("Error at SO " + scanchain[j].name + " " + str(scanchain[j].pins["D"].value))
			#			with open(self.design+"/"+rptname+".log", "a") as flog:
			#				flog.write("   {0}  {1}  {2}  (exp=1, got=0)\n".format(pat,self.sopin[i],len(scanvalue)-1-j))
			#			result = False
		
		#self.dumpFaultSTIL(si, launch, f_capture, f_so, pat, end)

		return result

	def dumpFaultSTIL(self, si, launch, f_capture, f_so, pat, end):
		fout = open(self.design+"/"+self.design+"_fault.stil", "a")
		prefix = self.prefix

		for i in range(len(prefix)):
			# Load
		 	if i < len(self.scanchains):
				fout.write(prefix[i]+"\n")
		 		if i == len(self.scanchains)-1:
					fout.write(si[i]+"\n; }\n")
				else:
					fout.write(si[i]+"\n;\n")
			
			# Launch and Capture
		 	elif i == len(self.scanchains):
				fout.write("   Call \"multiclock_capture\" {\n")
				pi_m = launch[0].replace("P","0")
				fout.write(prefix[i]+"\n"+pi_m+"; }\n")
				fout.write("   Call \"allclock_launch\" {\n")
				fout.write(prefix[i]+"\n"+launch[0]+"; }\n")
				fout.write("   Call \"allclock_capture\" {\n")
				fout.write(prefix[i]+"\n"+f_capture[0]+";\n")
		 	elif i == len(self.scanchains)+1:
				fout.write(prefix[i]+"\n"+f_capture[1]+"\n; }\n")
				fout.write("   Ann {* fast_sequential *}\n")
				if end:
					fout.write("   \"end "+ str(pat)+ " unload\": Call \"load_unload\" {\n")
				else:
					fout.write("   \"pattern " + str(pat+1)+"\": Call \"load_unload\" {\n")
			# Unload
			else:
				fout.write(prefix[i]+"\n")
				fout.write(f_so[i-len(self.scanchains)-2]+"\n;\n")
		
		if end:
			fout.write("  }\n}\n\n// Patterns reference")
		fout.close()

	def dumpSTILprefix(self, infile):
		print("Start dumping faulty STIL prefix")
		f = open(infile, "r")
		fout = open(self.design+"/"+self.design+"_fault.stil", "w")

		first = False
		prefix = []
		for line in f:
			fout.write(line)

			if "pattern 0" in line:
				first = True

			if first and "\"=" in line:
					idx1 = line.find("=")+1
					prefix.append(line[:idx1])

			if len(prefix) == 2*len(self.scanchains)+2 and ";" in line:
					break
	
		f.close()
		fout.close()
		self.prefix = prefix
		print("END dumping faulty STIL prefix")

	def injectfault(self):
		self.faulty_gate = "U51988"
		self.faulty_pin = "ZN"
	 	self.defect = "str"

design = sys.argv[1]
cir = Circuit(design)

f1 = design + "/" + design + ".v"
cir.parseVerilog(f1)
f2 = design + "/die0.rpt"
cir.parsePartition(f2)
cir.parseSTIL(sys.argv[2])

