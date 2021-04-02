import numpy as np
import torch
import dgl
import dgl.function as fn


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
        
        for onode in wire.outnode:
            dstID = onode.ID
            edge.append((srcID,dstID))
            
#     Connect fanin to fanout in a gate
    for g in cir.Gate:
        gate = cir.Gate[g]
        if "SDFF" in gate.gtype:
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
        topEdge.append((srcID, dstID))
        site_flag[dstID] = 1
        
    for n in g.pins:
        if g.nodes[n] not in g.outnode:
            dstID = g.nodes[n].ID
            if site_flag[dstID] == 1:
                continue
            else:
                topEdge.append((srcID, dstID))
                site_flag[dstID] = 1
                backprop_dfs(cir, g.pins[n], srcID, topEdge, site_flag)
                
def backprop(cir):
    dist = {}
    topEdge = []
    topNodeID = 0
    for sc in cir.scanchains:
        for gate in sc:
            dist[gate.name] = topNodeID
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

        wire = node.net
        faningate = wire.fanin
        loc = -1

        if faningate == 0:
            loc = 0
        else:
        #     Output pin of a gate
            if faningate == cir.Gate[gate]:
                die_in = faningate.die
                cnt = 0
                for fo in wire.fanout:
                    if fo.die == die_in:
                        cnt += 1
                        break

                if cnt > 0:
                    loc = die_in
                else:
                    loc = 2
            else:
                if faningate.die == cir.Gate[gate].die:
                    loc = faningate.die
                else:
                    loc = 2

        if loc == 0:
            location[ID] = torch.tensor([1,0,0])
        elif loc == 1:
            location[ID] = torch.tensor([0,1,0])
        elif loc == 2:
            location[ID] = torch.tensor([0,0,1])
        else:
            assert(False)
            
    return location

def getDatasetfromLog(cir, dic, g, num_patterns, num_samples):
    dataset = []
    f1 = open("ldpc_GNN_inject.dat", "r")
    l = f1.readlines()
    f1.close()
    l = l[1:]

    for line in l:
        words = line.split()
        gname = words[1].split("/")[0]
        pname = words[1].split("/")[1]
        logname = "ldpc_GNN/Logs/"+gname+"_"+pname+"_st"+words[0]+".log"

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
        r = np.zeros((g.number_of_nodes('topNode'), num_patterns), dtype=np.dtype('float32'))
        success = True
        for fault in l2:
            w2 = fault.split()
            if len(w2) != 5:
                success = False
                break
            pat = int(w2[0])-1
            chname = w2[1]
            loc = int(w2[2])


            chain = cir.scanchains[cir.sopin.index(chname)]
            gname = chain[::-1][loc].name
            srcID = dic[gname]
            r[srcID][pat] = 1.0

        if not success:
            continue
        if not np.count_nonzero(r):
            continue
            
        dataset.append((r, label))
        if len(dataset) == num_samples:
            break
    return dataset

def getSubgraphs(hg, dataset):
    subgraphs = []
    hg = hg.to('cuda')
    for d, l in dataset:    
        with hg.local_scope():
            h = torch.from_numpy(d).to('cuda')
            result = torch.sum(h,dim=0)
            hg.nodes['topNode'].data['h'] = h
            hg['topEdge'].update_all(message_func=fn.copy_u('h','m'), reduce_func=fn.sum('m', 'h'), etype='topEdge')
            h_N = torch.mul(hg.nodes['faultSite'].data['h'], hg.nodes['faultSite'].data['feats'])
            t = torch.all(h_N == result, dim=1).float()
            nid = torch.nonzero(t, as_tuple=True)[0]
            g = hg.subgraph({'faultSite': nid})

            infeats = torch.cat([g.nodes['faultSite'].data['in_degree'], g.nodes['faultSite'].data['out_degree'], g.nodes['faultSite'].data['top_degree']], dim=1)
            infeats = torch.cat([infeats, g.nodes['faultSite'].data['loc']], dim=1)
            infeats = torch.cat([infeats, g.nodes['faultSite'].data['level']], dim=1)
            infeats = torch.cat([infeats, g.in_degrees(etype='net').view(-1,1).float()], dim=1)
            infeats = torch.cat([infeats, g.out_degrees(etype='net').view(-1,1).float()], dim=1)

            g = dgl.to_homogeneous(g)
    #         g = dgl.add_self_loop(g)
    #         g = dgl.add_reverse_edges(g)
    #         g.nodes['faultSite'].data['infeats'] = infeats
            g.ndata['infeats'] = infeats

            g = g.to('cpu')
            subgraphs.append((g, l))

        if len(subgraphs)%500 == 0:
            print(len(subgraphs))

    hg = hg.to('cpu')
    return subgraphs