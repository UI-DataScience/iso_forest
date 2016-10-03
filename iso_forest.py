"isolated forest functions"
__author__ = 'Matias Carrasco Kind'
import numpy as np
import random as rn
import os
from version import __version__
import igraph as ig

def c_factor(n) :
    return 2.0*(np.log(n-1)+0.5772156649) - (2.0*(n-1.)/n)

class iForest(object):
    def __init__(self,X, ntrees,  sample_size, limit=None):
        self.ntrees = ntrees
        self.X = X
        self.nobjs = len(X)
        self.sample = sample_size
        self.Trees = []
        self.limit = limit
        if limit is None:
            self.limit = int(np.ceil(np.log2(self.sample)))
        self.c = c_factor(self.sample)        
        for i in range(self.ntrees):
            ix = rn.sample(range(self.nobjs), self.sample)
            X_p = X[ix]
            self.Trees.append(iTree(X_p, 0, self.limit))

    def compute_paths(self, X_in = None):
        if X_in is None:
            X_in = self.X
        S = np.zeros(len(X_in))
        for i in  range(len(X_in)):
            h_temp = 0
            for j in range(self.ntrees):
                h_temp += PathFactor(X_in[i],self.Trees[j]).path*1.0
            Eh = h_temp/self.ntrees
            S[i] = 2.0**(-Eh/self.c)
        return S
        
        

class Node(object):
    def __init__(self, X, q, p, e, left, right, node_type = '' ):
        self.e = e
        self.size = len(X)
        self.X = X # to be removed
        self.q = q
        self.p = p
        self.left = left
        self.right = right
        self.ntype = node_type




class iTree(object):

    """
    Unique entries for X
    """

    def __init__(self,X,e,l):
        self.e = e # depth
        self.X = X #save data for now
        self.size = len(X) #  n objects
        self.Q = np.arange(np.shape(X)[1], dtype='int') # n dimensions
        self.l = l # depth limit
        self.p = None
        self.q = None
        self.exnodes = 0
        self.root = self.make_tree(X,e,l)
        

    def make_tree(self,X,e,l):
        self.e = e
        if e >= l or len(X) <= 1:
            left = None
            right = None
            self.exnodes += 1
            return Node(X, self.q, self.p, e, left, right, node_type = 'exNode' )
        else:
            self.q = rn.choice(self.Q)
            self.p = rn.uniform(X[:,self.q].min(),X[:,self.q].max())
            w = np.where(X[:,self.q] < self.p,True,False)
            return Node(X, self.q, self.p, e,\
            left=self.make_tree(X[w],e+1,l),\
            right=self.make_tree(X[~w],e+1,l),\
            node_type = 'inNode' )

    def get_node(self, path):
        node = self.root
        for p in path:
            if p == 'L' : node = node.left
            if p == 'R' : node = node.right
        return node
        
            
class PathFactor(object):
    def __init__(self,x,itree):
        self.path_list=[]        
        self.x = x
        self.e = 0
        self.path = self.find_path(itree.root)

    def find_path(self,T):
        if T.ntype == 'exNode':
            if T.size == 1: return self.e
            else:
                self.e = self.e + c_factor(T.size)
                return self.e
        else:
            a = T.q
            self.e += 1
            if self.x[a] < T.p:
                self.path_list.append('L')
                return self.find_path(T.left)
            else:
                self.path_list.append('R')
                return self.find_path(T.right)

def all_branches(node, current=[], branches = None):
    current = current[:node.e]
    if branches is None: branches = []
    if node.ntype == 'inNode':
        current.append('L')
        all_branches(node.left, current=current, branches=branches)
        current = current[:-1]
        current.append('R')
        all_branches(node.right, current=current, branches=branches)
    else:
        branches.append(current)
    return branches


def branch2num(branch):
    num = [0]
    for b in branch:
        if b == 'L':
            num.append(num[-1] * 2 + 1)
        if b == 'R':
            num.append(num[-1] * 2 + 2)
    return num

def gen_graph(branches):
    num_branches = [branch2num(i) for i in branches]
    all_nodes = [j for branch in num_branches for j in branch]
    all_nodes = np.unique(all_nodes).tolist()
    g=ig.Graph()
    for k in all_nodes : g.add_vertex(str(k))
    t=[]
    for j in range(len(branches)):
        branch = branch2num(branches[j])
        for i in range(len(branch)-1):
            pair = [branch[i],branch[i+1]]
            if pair not in t:
                t.append(pair)
                g.add_edge(str(branch[i]),str(branch[i+1]))
    return g