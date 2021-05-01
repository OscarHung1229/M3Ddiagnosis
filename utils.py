import numpy as np
import torch
import dgl
import dgl.function as fn
import time
import matplotlib.pyplot as plt
import random

def CreateGraphByFaultSite(cir):
#     Create edges
    edge = []
#     Connect stem and branches in a net
    for w in cir.Wire:
        wire = cir.Wire[w]
        innode = wire.innode
        if innode == 0:
            continue
            
        srcID = innode.ID
        
        if wire.fanin != 0 and wire.fanin.gtype == "Dummy":
            inwire = wire.fanin.pins["A"]
            while True:
                if inwire.fanin != 0 and inwire.fanin.gtype == "Dummy":
                    inwire = inwire.fanin.pins["A"]
                else:
                    break
                    
            if inwire.innode == 0:
                continue
            srcID = inwire.innode.ID            
        
        for i in range(len(wire.outnode)):
            onode = wire.outnode[i]
            ogate = wire.fanout[i]
            if ogate.gtype == "Dummy":
                continue
            elif ogate.gtype == "MIV":
                onode = ogate.outnode[0]
            dstID = onode.ID
            edge.append((srcID,dstID))
            
    #     Connect fanin to fanout in a gate
    for g in cir.Gate:
        gate = cir.Gate[g]
        if "SDFF" in gate.gtype:
            continue
        
        elif "Dummy" in gate.gtype:
            for name in gate.nodes:
                if gate.nodes[name] in gate.outnode:
                    dstID = gate.nodes[name].ID
                else:
                    srcID = gate.nodes[name].ID
            edge.append((srcID,dstID))
            continue
            
        elif "MIV" in gate.gtype:
            for name in gate.nodes:
                if gate.nodes[name] not in gate.outnode:
                    dstID = gate.nodes[name].ID
                    edge.append((dstID,dstID))
            continue
            
        for n in gate.outnode:
            dstID = n.ID
            for name in gate.nodes:
                if gate.nodes[name] in gate.outnode:
                    continue
                srcID = gate.nodes[name].ID
                edge.append((srcID,dstID))

    return edge

def backprop_dfs(cir, w, srcID, topEdge, site_flag):
    if w.fanin == 0:
        return
    g = w.fanin
    if "SDFF" in g.gtype:
        return
    
    if len(g.outpin) == 2 and w == g.outpin[1]:
        dstID = g.outnode[1].ID
        if site_flag[dstID] == 1:
            return
        topEdge.append((srcID, dstID))
        site_flag[dstID] = 1
    else:
        dstID = g.outnode[0].ID
        if site_flag[dstID] == 1:
            return
        if g.gtype != "Dummy":
            topEdge.append((srcID, dstID))
        site_flag[dstID] = 1
        
    for n in g.pins:
        if g.nodes[n] not in g.outnode:
            dstID = g.nodes[n].ID
            if site_flag[dstID] == 1:
                continue
            else:
                if g.gtype != "Dummy" and g.gtype != "MIV":
                    topEdge.append((srcID, dstID))
                site_flag[dstID] = 1
                backprop_dfs(cir, g.pins[n], srcID, topEdge, site_flag)
                
def backprop(cir, dfs=True):
    dist = {}
    topEdge = []
    topNodeID = 0
    for sc in cir.scanchains:
        for gate in sc:
            dist[gate.name] = topNodeID
            if dfs:
                dstID = cir.Node[gate.name+"_D"].ID
                topEdge.append((topNodeID, dstID))
                site_flag = np.zeros(len(cir.Node))
                backprop_dfs(cir, gate.pins["D"], topNodeID, topEdge, site_flag)
            topNodeID += 1
            
    return dist, topEdge

def getLevel(cir):
    level = []
    for n in cir.Node:
        if cir.Node[n].net.fanin == 0:
            level.append(0)
        else:
            level.append(cir.Node[n].net.fanin.level)
    level = torch.tensor(level).view(-1,1)
    return level

def getLocation(cir, num_nodes):
    location = torch.zeros((num_nodes, 3))
    for n in cir.Node:
        node = cir.Node[n]
        ID = node.ID
        idx = node.name.rfind("_")
        gate = node.name[:idx]
        pin = node.name[idx+1:]
        
        
        if cir.Gate[gate].die == 0:
            location[ID] = torch.tensor([1,0,0])
        elif cir.Gate[gate].die == 1:
            location[ID] = torch.tensor([0,1,0])
        elif cir.Gate[gate].die == 2:
            location[ID] = torch.tensor([0,0,1])

#         wire = node.net
#         faningate = wire.fanin
#         loc = -1

#         if faningate == 0:
#             loc = 0
#         else:
#         #     Output pin of a gate
#             if faningate == cir.Gate[gate]:
#                 die_in = faningate.die
#                 cnt = 0
#                 for fo in wire.fanout:
#                     if fo.die == die_in:
#                         cnt += 1
#                         break

#                 if cnt > 0:
#                     loc = die_in
#                 else:
#                     loc = 2
#             else:
#                 if faningate.die == cir.Gate[gate].die:
#                     loc = faningate.die
#                 else:
#                     loc = 2

#         if loc == 0:
#             location[ID] = torch.tensor([1,0,0])
#         elif loc == 1:
#             location[ID] = torch.tensor([0,1,0])
#         elif loc == 2:
#             location[ID] = torch.tensor([0,0,1])
#         else:
#             assert(False)
            
    return location

def addfeatures(cir, num_nodes):
    feat = torch.zeros((num_nodes, 2))
    for n in cir.Node:
        node = cir.Node[n]
        ID = node.ID
        idx = node.name.rfind("_")
        gate = node.name[:idx]
        pin = node.name[idx+1:]

        
        
        wire = node.net
        if wire in cir.Gate[gate].outpin:
            feat[ID][0] = 1
            
        if "MIV" in gate:
            feat[ID][1] = 1
        else:
            for fo in wire.fanout:
                if fo.die == 2:
                    feat[ID][1] = 1
                    break
            
    return feat



def getDatasetfromLog(cir, design, dic, g, num_patterns, num_samples=-1, start_pat=0, end_pat=-1, shuffle=True):
    print("Start generating data")
    
    
    dataset = []
    dstIDset = []
#     f1 = open(design+"/"+design+"_inject_extra.dat", "r")
    if cir.design == "ldpc_GNN" or cir.design == "tate_GNN":
        f1 = open(design+"/unique.dat", "r")
    else:
        f1 = open(design+"/TDF_600_inject.dat", "r")
    l = f1.readlines()
    f1.close()
    l = l[1:]
    if shuffle:
        random.shuffle(l)

    for line in l:
        words = line.split()
        gname = words[1].split("/")[0]
        pname = words[1].split("/")[1]
        if cir.design == "ldpc_GNN" or cir.design == "tate_GNN":
            logname = design+"/Logs_w_MIV/"+gname+"_"+pname+"_st"+words[0]+".log"
        else:
            logname = design+"/Logs_w_MIV_TDF_600/"+gname+"_"+pname+"_st"+words[0]+".log"
        
        if words[1].split("/")[-1] == "nextstate":
            pname = "D"
        elif words[1].split("/")[-1] == "IQ":
            pname = "Q"

        dstID = cir.Node[gname+"_"+pname].ID
        label = -1
        if g.nodes['faultSite'].data['loc'][dstID][0] == 1:
            label = 0
        elif g.nodes['faultSite'].data['loc'][dstID][1] == 1:
            label = 1
        else:
            label = 2
            
        f2 = open(logname, "r")
        l2 = f2.readlines()[1:]
        f2.close()

        
        num_pat = end_pat-start_pat
        success = True
        subnodes = []
        for fault in l2:
            w2 = fault.split()
            if len(w2) != 5:
#                 continue
                success = False
                break
            pat = int(w2[0])-1

            if pat < start_pat:
                continue
            
            if pat >= end_pat:
                break
            
            chname = w2[1]
            loc = int(w2[2])


            chain = cir.scanchains[cir.sopin.index(chname)]
            gname = chain[::-1][loc].name
            srcID = dic[gname]
            
            tmpnodes =  g.successors(srcID, etype=('topNode', 'topEdge', 'faultSite')).numpy()
        
            if len(subnodes):
                tmpnodes = np.intersect1d(subnodes, tmpnodes)
                
            subnodes = np.array([idx for idx in tmpnodes if g.nodes['faultSite'].data['feats'][idx][pat-start_pat] == 1.0])

            if not len(subnodes):
                break


        if not success:
            continue
        if not len(subnodes):
            print("No candidates!!!, {}".format(logname))
            continue
        
        with g.local_scope():
            sg = g.subgraph({'faultSite': subnodes})

            assert(dstID in sg.ndata[dgl.NID]['faultSite'])

            infeats = torch.cat([sg.nodes['faultSite'].data['in_degree'], sg.nodes['faultSite'].data['out_degree'], sg.nodes['faultSite'].data['top_degree']], dim=1)
            infeats = torch.cat([infeats, sg.nodes['faultSite'].data['loc']], dim=1)
            infeats = torch.cat([infeats, sg.nodes['faultSite'].data['level']], dim=1)
            infeats = torch.cat([infeats, sg.nodes['faultSite'].data['more']], dim=1)
            infeats = torch.cat([infeats, sg.in_degrees(etype='net').view(-1,1).float()], dim=1)
            infeats = torch.cat([infeats, sg.out_degrees(etype='net').view(-1,1).float()], dim=1)

            sg = dgl.to_homogeneous(sg)
            sg = dgl.add_reverse_edges(sg)
            sg.ndata['infeats'] = infeats
            
        sg = dgl.add_self_loop(sg)
        
        dataset.append((sg, label))
        dstIDset.append(dstID)
        
        if len(dataset)%50 == 0:
            print(len(dataset))
        
        if len(dataset) == num_samples:
            break
            
    print("Finish generating data")
    return dataset, dstIDset

def getSubgraphs(hg, dataset, dstIDset, debug=False, start_pat=0, end_pat=-1):
    print("Start generating subgraphs")
    subgraphs = []
    
#     hg = hg.to('cuda')
    cnt = 0
    for d, l in dataset:
#         hg = hg.to('cuda')
        dstID = dstIDset[cnt]
        cnt += 1
        with hg.local_scope():
#             h = torch.from_numpy(d).to('cuda')
            h = torch.from_numpy(d)
#             cols = h.shape[1]
            result = torch.sum(h,dim=0)
            hg.nodes['topNode'].data['h'] = h
            hg['topEdge'].update_all(message_func=fn.copy_u('h','m'), reduce_func=fn.sum('m', 'h'), etype='topEdge')
            h_N = torch.mul(hg.nodes['faultSite'].data['h'], hg.nodes['faultSite'].data['feats'][:,start_pat:end_pat])
            t = torch.all(h_N == result, dim=1).float()
            nid = torch.nonzero(t, as_tuple=True)[0]
            g = hg.subgraph({'faultSite': nid})
            
            if debug:
#                 print(dstID)
#                 print(g.ndata[dgl.NID]['faultSite'])
#                 print("\n")
                assert(dstID in g.ndata[dgl.NID]['faultSite'])

            infeats = torch.cat([g.nodes['faultSite'].data['in_degree'], g.nodes['faultSite'].data['out_degree'], g.nodes['faultSite'].data['top_degree']], dim=1)
            infeats = torch.cat([infeats, g.nodes['faultSite'].data['loc']], dim=1)
            infeats = torch.cat([infeats, g.nodes['faultSite'].data['level']], dim=1)
            infeats = torch.cat([infeats, g.nodes['faultSite'].data['more']], dim=1)
            infeats = torch.cat([infeats, g.in_degrees(etype='net').view(-1,1).float()], dim=1)
            infeats = torch.cat([infeats, g.out_degrees(etype='net').view(-1,1).float()], dim=1)

            g = dgl.to_homogeneous(g)
#             g = dgl.add_self_loop(g)
            g = dgl.add_reverse_edges(g)
#             g.nodes['faultSite'].data['infeats'] = infeats
            g.ndata['infeats'] = infeats

#             g = g.to('cpu')
#             g = dgl.add_reverse_edges(g)
            g = dgl.add_self_loop(g)
            subgraphs.append((g, l))
        
        torch.cuda.empty_cache()

        if len(subgraphs)%500 == 0:
            print(len(subgraphs))

            
#     hg = hg.to('cpu')
#     torch.cuda.empty_cache()

    print("End generating subgraphs")
    return subgraphs

def getDatasetfromLogSep(cir, design, dic, g, num_patterns, num_samples=-1, start_pat=0, end_pat=-1, shuffle=True):
    print("Start generating data")
    
    
    dataset = []
    dstIDset = []
    if cir.design == "ldpc_GNN" or cir.design == "tate_GNN":
        f1 = open(design+"/unique.dat", "r")
    else:
        f1 = open(design+"/TDF_inject.dat", "r")
    l = f1.readlines()
    f1.close()
    l = l[1:]
    if shuffle:
        random.shuffle(l)

    for line in l:
        words = line.split()
        gname = words[1].split("/")[0]
        pname = words[1].split("/")[1]
        if cir.design == "ldpc_GNN" or cir.design == "tate_GNN":
            logname = design+"/Logs_w_MIV/"+gname+"_"+pname+"_st"+words[0]+".log"
        else:
            logname = design+"/Logs_w_MIV_TDF_600/"+gname+"_"+pname+"_st"+words[0]+".log"
        
        if words[1].split("/")[-1] == "nextstate":
            pname = "D"
        elif words[1].split("/")[-1] == "IQ":
            pname = "Q"

        dstID = cir.Node[gname+"_"+pname].ID
        label = -1
        if g.nodes['faultSite'].data['loc'][dstID][0] == 1:
            label = 0
        elif g.nodes['faultSite'].data['loc'][dstID][1] == 1:
            label = 1
        else:
            label = 2
            
        num_pat = end_pat-start_pat
        r = np.zeros((g.number_of_nodes('topNode'), num_pat), dtype=np.dtype('float32'))
            
        f2 = open(logname, "r")
        l2 = f2.readlines()[1:]
        f2.close()
        
        num_pat = end_pat-start_pat
        success = True
        subnodes = []
        for fault in l2:
            w2 = fault.split()
            if len(w2) != 5:
                success = False
                break
            pat = int(w2[0])-1
            
#             if pat >= num_patterns:
#                 break
            if pat < start_pat:
                continue
            
            if pat >= end_pat:
                break
            
            chname = w2[1]
            loc = int(w2[2])


            chain = cir.scanchains[cir.sopin.index(chname)]
            gname = chain[::-1][loc].name
            srcID = dic[gname]
            r[srcID][pat-start_pat] = 1.0

        if not success:
            continue
        if not np.count_nonzero(r):
            print("No candidates!!!, {}".format(logname))
            continue
        
        dataset.append((r, label))
        dstIDset.append(dstID)
        
        if len(dataset) == num_samples:
            break
            
    print("Finish generating data")
    return dataset, dstIDset