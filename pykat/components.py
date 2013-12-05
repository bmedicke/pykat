# -*- coding: utf-8 -*-
"""
Created on Mon Jan 28 11:10:01 2013

@author: Daniel
"""
import exceptions
import pykat.exceptions as pkex
import pykat
from pykat.node_network import *
from pykat.exceptions import *

import pykat.gui.resources
import pykat.gui.graphics
from pykat.gui.graphics import *
from pykat.SIfloat import *

next_component_id = 1

class NodeGaussSetter(object):
    def __init__(self, component, node):                
        self.__comp = component
        self.__node = node
    
    @property
    def node(self):
        return self.__node
    
    @property
    def q(self):
        return self.__node.qx
        
    @q.setter
    def q(self, value):
        self.__node.setGauss(self.__comp, value)
        
    @property
    def qx(self):
        return self.__node.qx
    @qx.setter
    def qx(self, value):
        self.__node.setGauss(self.__comp, value)
    
    @property
    def qy(self):
        return self.__node.qy
    @qy.setter
    def qy(self, value):
        self.__node.setGauss(self.__comp, self.qx, value)
        
class Component(object) :
    def __init__(self, name):
        self.__name = name
        self._svgItem = None
        self._requested_node_names = []
        self._kat = None
        self.tag = None
        
        # store a unique ID for this component
        global next_component_id
        self.__id = next_component_id
        next_component_id += 1
        
        # This creates an instance specific class for the component
        # this enables us to add properties to instances rather than
        # all classes
        cls = type(self)
        self.__class__ = type(cls.__name__, (cls,), {})
            
    def _on_kat_add(self, kat):
        """
        Called when this component has been added to a kat object.
        kat is the finesse.kat object which it now belongs to and
        node_array is an array specific to this object which contains
        references to the nodes that are attached to it.
        """
        if self._kat != None:
            raise pkex.BasePyKatException("Component has already been added to a finesse.kat object")
            
        self._kat = kat
        
        kat.nodes.registerComponentNodes(self, self._requested_node_names, self.__on_node_change)
        
    def __on_node_change(self):
        # need to update the node gauss parameter setter members 
        self.__update_node_setters()
        
    def __update_node_setters(self):
        # check if any node setters have already been added. If so we
        # need to remove them. This function should get called if the nodes
        # are updated, either by some function call or the GUI
        key_rm = [k for k in self.__dict__ if k.startswith("__nodesetter_", 0, 13)]
        
        # now we have a list of which to remove
        for key in key_rm:
            ns = self.__dict__[key]
            detattr(self, '__nodesetter_' + ns._node.name)
            delattr(self, ns._node.name)
        
        for node in self.nodes:
            if type(node) != pykat.node_network.DumpNode:
                ns = NodeGaussSetter(self, node)
                self.__add_node_setter(ns)
        
    def __add_node_setter(self, ns):

        if not isinstance(ns, NodeGaussSetter):
            raise exceptions.ValueError("Argument is not of type NodeGaussSetter")
        
        name = ns.node.name
        fget = lambda self: self.__get_node_setter(name)
        
        setattr(self.__class__, name, property(fget))
        setattr(self, '__nodesetter_' + name, ns)                   

    def __get_node_setter(self, name):
        return getattr(self, '__nodesetter_' + name)   
        
    @staticmethod
    def parseFinesseText(text):    
        raise NotImplementedError("This function is not implemented")
            
    def getFinesseText(self):
        """ Base class for individual finesse optical components """    
        raise NotImplementedError("This function is not implemented")
        
    def getQGraphicsItem(self):    
        return None      
    
    @property
    def nodes(self): return self._kat.nodes.getComponentNodes(self) 
    
    @property    
    def name(self): return self.__name      
    
    @property
    def id(self): return self.__id
    
    
    
class Param(float):
    def __new__(self,name,value):
        return float.__new__(self,SIfloat(value))
         
    def __init__(self,name,value):
        self.__name = name
        
    name = property(lambda self: self.__name)
           
class mirror(Component):
    def __init__(self,name,node1,node2,R=0,T=0,phi=0,Rcx=0,Rcy=0,xbeta=0,ybeta=0,mass=0, r_ap=0):
        
        Component.__init__(self,name)
        
        self._requested_node_names.append(node1)
        self._requested_node_names.append(node2)

        self.__r_ap = float(r_ap)        
        self.__mass = float(mass)
        self.__R = float(R)
        self.__T = float(T)
        self.__phi = float(phi)
        self.__Rcx = float(Rcx)
        self.__Rcy = float(Rcy)
        self.__xbeta = float(xbeta)
        self.__ybeta = float(ybeta)
    
    @property
    def r_ap(self): return Param('r_ap', self.__r_ap)
    @r_ap.setter
    def r_ap(self,value): self.__aperture = float(value)

    @property
    def mass(self): return Param('mass', self.__mass)
    @mass.setter
    def mass(self,value): self.__mass = float(value)
    
    @property
    def R(self): return Param('R', self.__R)
    @R.setter
    def R(self,value): self.__R = float(value)
    
    @property
    def T(self): return Param('T', self.__T)
    @T.setter
    def T(self,value): self.__T = float(value)
        
    @property
    def phi(self): return Param('phi', self.__phi)
    @phi.setter
    def phi(self,value): self.__phi = float(value)
    
    @property
    def Rcx(self): return Param('Rcx', self.__Rcx)
    @Rcx.setter
    def Rcx(self,value): self.__Rcx = float(value)
    
    @property
    def Rcy(self): return Param('Rcy', self.__Rcy)
    @Rcy.setter
    def Rcy(self,value): self.__Rcy = float(value)
    
    @property
    def xbeta(self): return Param('xbeta', self.__xbeta)
    @xbeta.setter
    def xbeta(self,value): self.__xbeta = float(value)
    
    @property
    def ybeta(self): return Param('ybeta', self.__ybeta)
    @ybeta.setter
    def ybeta(self,value): self.__ybeta = float(value)
    
    @property
    def Rc(self):
        if self.Rcx == self.Rcy:
            return self.Rcx
        else:
            return [self.Rcx, self.Rcy]
    
    @Rc.setter
    def Rc(self,value):
        self.Rcx = float(value)
        self.Rcy = float(value)
    
    @staticmethod
    def parseFinesseText(text):
        values = text.split(" ")

        if values[0] != "m":
            raise exceptions.RuntimeError("'{0}' not a valid Finesse mirror command".format(text))

        values.pop(0) # remove initial value
        
        if len(values) != 6:
            raise exceptions.RuntimeError("Mirror Finesse code format incorrect '{0}'".format(text))

        return mirror(values[0], values[4], values[5], R=values[1], T=values[2], phi=values[3])
        
    def getFinesseText(self):        
        rtn = []
            
        rtn.append('m {0} {1} {2} {3} {4} {5}'.format(
                self.name, self.__R, self.__T, self.__phi,
                self.nodes[0].name, self.nodes[1].name))

        if self.r_ap != 0: rtn.append("attr {0} r_ap {1}".format(self.name,self.__r_ap))            
        if self.mass != 0: rtn.append("attr {0} mass {1}".format(self.name,self.__mass))
        if self.Rcx != 0: rtn.append("attr {0} Rcx {1}".format(self.name,self.__Rcx))
        if self.Rcy != 0: rtn.append("attr {0} Rcy {1}".format(self.name,self.__Rcy))
        if self.xbeta != 0: rtn.append("attr {0} xbeta {1}".format(self.name,self.__xbeta))
        if self.ybeta != 0: rtn.append("attr {0} ybeta {1}".format(self.name,self.__ybeta))
        
        return rtn
        
    def getQGraphicsItem(self):
        if self._svgItem == None:
            self._svgItem = pykat.gui.graphics.ComponentQGraphicsItem(":/resources/mirror_flat.svg", self ,[(-4,15,self.nodes[0]), (14,15,self.nodes[1])])
            
        return self._svgItem
   
   
class space(Component):
    def __init__(self, name, node1, node2, L=0, n=1):
        Component.__init__(self,name,)
        
        self._requested_node_names.append(node1)
        self._requested_node_names.append(node2)
        
        self.__L = SIfloat(L)
        self.__n = SIfloat(n)
        self._QItem = None
        
    @property
    def L(self): return Param('L', self.__L)
    @L.setter
    def L(self,value): self.__L = SIfloat(value)
    @property
    def n(self): return Param('n', self.__n)
    @n.setter
    def n(self,value): self.__n = SIfloat(value)
    
    @staticmethod
    def parseFinesseText(text):
        values = text.split(" ")

        if values[0] != "s":
            raise exceptions.RuntimeError("'{0}' not a valid Finesse space command".format(text))

        values.pop(0) # remove initial value
        
        if len(values) == 5:
            return space(values[0],values[3],values[4],L=values[1],n=values[2])
        elif len(values) == 4:
            return space(values[0],values[2],values[3],L=values[1])
        else:
            raise exceptions.RuntimeError("Space Finesse code format incorrect '{0}'".format(text))
        
    def getFinesseText(self):
        if self.__n == 1:
            return 's {0} {1} {2} {3}'.format(self.name, self.__L, self.nodes[0].name, self.nodes[1].name)            
        else:
            return 's {0} {1} {2} {3} {4}'.format(self.name, self.__L, self.__n, self.nodes[0].name, self.nodes[1].name)            
       
    def getQGraphicsItem(self):
        if self._QItem == None:
            self._QItem = pykat.gui.graphics.SpaceQGraphicsItem(self)
        
        return self._QItem  

    # def changeNode(self, node_old, node_new):
        # '''
        # Called when a space's node has been connected
        # to another components node
        # '''
        # node_new.connect(self)
        # node_old.disconnect(self)
        
        # if self._nodes[0] == node_old:
            # self._nodes[0] = node_new
        
        # if self._nodes[1] == node_old:
            # self._nodes[1] = node_newf

    
class laser(Component):
    def __init__(self,name,node,P=1,f_offset=0,phase=0):
        Component.__init__(self,name)
        
        self._requested_node_names.append(node)
        
        self.__power = float(P)
        self.__f_offset = float(f_offset)
        self.__phase = float(phase)
        
    @property
    def power(self): return Param('P', self.__power)
    @power.setter
    def power(self,value): self.__power = float(value)
    
    @property
    def f_offset(self): return Param('f', self.__f_offset)
    @f_offset.setter
    def f_offset(self,value): self.__f_offset = float(value)
    
    @property
    def phase(self): return Param('phase', self.__phase)
    @phase.setter
    def phase(self,value): self.__phase = float(value)
    
    @staticmethod
    def parseFinesseText(text):
        values = text.split(" ")

        if values[0] != "l":
            raise exceptions.RuntimeError("'{0}' not a valid Finesse laser command".format(text))

        values.pop(0) # remove initial value
        
        if len(values) == 5:
            return laser(values[0],values[4],P=values[1],f_offset=values[2],phase=values[3])
        elif len(values) == 4:
            return laser(values[0],values[3],P=values[1],f_offset=values[2], phase=0)
        else:
            raise exceptions.FinesseParse("Laser Finesse code format incorrect '{0}'".format(text))
    
    def getFinesseText(self):
        return 'l {0} {1} {2} {3} {4}'.format(self.name, self.__power, self.__f_offset, self.__phase, self.nodes[0].name)            
         
    def getQGraphicsItem(self):
        if self._svgItem == None:
            self._svgItem = pykat.gui.graphics.ComponentQGraphicsItem(":/resources/laser.svg", self, [(65,25,self.nodes[0])])
            
        return self._svgItem
            
