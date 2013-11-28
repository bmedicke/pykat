# -*- coding: utf-8 -*-
"""
Created on Sun Jan 27 10:02:41 2013

@author: Daniel
"""
import exceptions
import pykat.gui.graphics
import pykat.exceptions as pkex
from pykat.components import Component
from pykat.detectors import Detector

class NodeNetwork(object):
    def __init__(self, kat):
        self._nodes = {}
        self.__kat = kat
        
    def createNode(self, node_name):
        if node_name == 'dump':
            return DumpNode()
            
        if node_name in self._nodes:
            # then this node already exists
            return self._nodes[node_name]
        else:
            n = Node(node_name, self)
            self.__add_node(n) # add node as a member of this object, e.g. kat.nodes.n
            self._nodes[node_name] = n
            return n
        
    def removeNode(self, node):
        if not isinstance(node,Node):
            raise exceptions.ValueError("node argument is not of type Node")
        
        if node.name not in self._nodes:
            raise exceptions.RuntimeError("Trying to remove node {0} when it has not been added".format(node.name))
        
        C = node.getComponents()
        
        if C[0][0] is not None or C[0][1] is not None:
            raise exceptions.RuntimeError("Cannot remove a node which is attached to components still")
            
        if len(C[1]) > 0:
            raise exceptions.RuntimeError("Cannot remove a node which is attached to detectors still")
        
        self.__remove_node(node)
        del self._nodes[node.name] 
        
    def hasNode(self, name):
        return (name in self._nodes)
    
    def getNodes(self):
        return self._nodes.copy()
    
    def dumpInfo(self):
        
        for name in self._nodes:
            
            n = self._nodes[name]
            items = n.getComponents()
            comp = items[0][:]
            det = items[1]
            
            if comp[0] == None:
                comp1 = 'dump'
            else:
                comp1 = comp[0].name
            
            if comp[1] == None:
                comp2 = 'dump'
            else:
                comp2 = comp[1].name    
            
            detectors = ""
            
            if len(det) > 0:
                detectors = "Detectors: "
                
                for d in det:
                    detectors = detectors + d.name + " "
                
            print "node: {0} connected:{1} {2}->{3} {4}".format(
                    n.name,n.isConnected(),comp1, comp2, detectors)
       
    def __add_node(self, node):

        if not isinstance(node, Node):
            raise exceptions.ValueError("Argument is not of type Node")
        
        name = node.name
        fget = lambda self: self.__get_node(name)
        
        setattr(self.__class__, name, property(fget))
        setattr(self, '__node_' + name, node)                   
    
    def __remove_node(self, node):
        if not isinstance(node, Node):
            raise exceptions.ValueError("Argument is not of type Node")
        
        name = node.name
        setattr(self, '__node_' + name)
        delattr(self.__class__, name)
        
    def __get_node(self, name):
        return getattr(self, '__node_' + name)        
        
class Node(object):
    class gauss_version:
        w0_z = 1
        z_zR = 2
        
    def __init__(self, name, network):
        self._comp1 = None
        self._comp2 = None
        self._detectors = []
        self.__name = name
        self._item = None
        self._network = network
        self.__gauss = None
        self.__gauss_version = None
        
    @property
    def network(self): return self._network
    
    @property
    def gauss(self): return self.__gauss
    
    def removeGauss():
        self.__gauss_version = None
        self.__gauss = None
        
    def gauss_w0_z(self, w0, z, w0y=None, zy=None):
        self.__gauss = []
        self.__gauss.append(w0)
        self.__gauss.append(z)
        
        if w0y != None and zy != None:
            self.__gauss.append(w0y)
            self.__gauss.append(zy)
            
        self.__gauss_version = Node.gauss_version.w0_z
        
    def getFinesseText(self):
        
        if not self.isConnected() or self.__gauss == None or self.__gauss_version == None:
            return None
            
            
        comp = ""
        
        if self._comp2 == None:
            comp = self._comp1.name
        else:
            comp = self._comp2.name
        
        rtn = []
        
        if self.__gauss_version == Node.gauss_version.w0_z:
            
            if len(self.__gauss) == 2:
                rtn.append("gauss gauss_{node} {comp} {node} {w0} {z}".format(node=self.name, comp=comp, w0=self.__gauss[0], z=self.__gauss[1]))
            elif len(self.__gauss) == 4:
                rtn.append("gauss gauss_{node} {comp} {node} {w0x} {zx} {w0y} {zy}".format(node=self.name, comp=comp, w0x=self.__gauss[0], zx=self.__gauss[1], w0y=self.__gauss[2], zy=self.__gauss[3]))
            else:
                raise pkex.BasePyKatException("Unexpected number of gaussian parameters")
        else:
            raise pkex.BasePyKatException("Unexpected gauss version")
            
        return rtn
        
    def isConnected(self):
        if (self._comp1 is not None) and (self._comp2 is not None):
            return True
        else:
            return False
      
    def remove(self):
        self._network.removeNode(self)
        
        if self._item != None:
            self._item.scene().removeItem(self._item)
    
    def disconnect(self, obj):
    
        if not (isinstance(obj,Component) or isinstance(obj,Detector)):
            raise exceptions.ValueError("Object is not a component or detector")
        
        if isinstance(obj, Component):
            
            if self._comp1 == obj:
                self._comp1 = None
            elif self._comp2 == obj:
                self._comp2 = None
            else:
                raise exceptions.RuntimeError("Cannot dettach {0} from node {1}".format(
                                    obj.name, self.__name))
          
        else:
            # we must have a detector as we check above            
            self._detectors.remove(obj)
    
        if self._item is not None:
            self._item.refresh()
            
    
    def connect(self, obj):

        if not (isinstance(obj,Component) or isinstance(obj,Detector)):
            raise exceptions.ValueError("Object is not a component or detector")
        
        if isinstance(obj, Component):
            
            if self._comp1 == None:
                self._comp1 = obj
            elif self._comp2 == None:
                self._comp2 = obj
            else:
                raise exceptions.RuntimeError("Cannot attach {0} to node {1} as it is already connected: {2} and {3}".format(
                                    obj.name, self.__name,self._comp1.name,self._comp2.name))
            
            if self._comp1 == self._comp2:
                raise exceptions.RuntimeError("Cannot connect {0} to both sides of node".format(obj.name))            
        else:
            # we must have a detector as we check above            
            self._detectors.append(obj)
    
        if self._item is not None:
            self._item.refresh()
            
    def getQGraphicsItem(self,dx=0,dy=0,nsize=8,parent=None):
        if self._item == None:
            self._item = pykat.gui.graphics.NodeQGraphicItem(self,
                                                             dx,dy,
                                                             -nsize/2,-nsize/2,
                                                             nsize,nsize,parent)
            
        return self._item
    
    def getComponents(self):
        ''' Returns a tuple with the first being the 2 components that 
        connect to the node. The second item is a list of the detectors at the
        node'''
        return [(self._comp1, self._comp2),self._detectors]
        
    def amIConnected(self, obj):
        """
        Checks if obj is connected to the node. Returns true or false in tuple
        with None or the other object and the node index which it is attached to
        """ 
        if obj == self._comp1:
            if self._comp2 == None:
                ix = -1
            else:
                ix = self._comp2.getNodes().index(self)
                
            return [True, self._comp2, ix]
        elif obj == self._comp2:
            if self._comp1 == None:
                ix = -1
            else:
                ix = self._comp1.getNodes().index(self)
                
            return [True, self._comp1, ix]
        else:
            return [False, None]
        
    def __getname(self):
        return self.__name      
        
    name = property(__getname)
    
class DumpNode(Node):
    def __init__(self):
        Node.__init__(self, 'dump', None)
        
        