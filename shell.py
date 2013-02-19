# -*- coding: utf-8 -*-

from code import InteractiveConsole
from copy import deepcopy
from kivy.app import App
from kivy.base import EventLoop
from kivy.clock import Clock
from kivy.config import Config
from kivy.graphics import *
from kivy.lang import Builder
from kivy.properties import ListProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from sympy import *
from sympy.abc import *
from sympy.utilities.lambdify import lambdify
import sys

from keyboard import *

DEBUG = True
FONT_NAME = "res/font/ubuntu-mono/UbuntuMono-R.ttf"
FONT_SIZE = 24
Builder.load_file( "kipycalc.kv" )

class PyShell( BoxLayout ) :

    def __init__( self, plotFoo ) :
        self.console = InteractiveConsole()
        BoxLayout.__init__( self, orientation="vertical" )
        frm = BoxLayout( orientation="vertical" )
        self.listed = TextInput()
        self.listed.font_name = FONT_NAME
        self.listed.readonly = True
        self.listed.size_hint = 1, 0.2
        self.listed.font_size = FONT_SIZE
        frm.add_widget( self.listed )
        self.kb = CucuKeyboard( self.onBtnExecPress, plotFoo )
        self.kb.size_hint = 1, 0.8
        frm.add_widget( self.kb )
        frm.size_hint = 1,1
        self.add_widget( frm )

    def start( self ) : 
        if not DEBUG :
            sys.stdout = self
            sys.stderr = self
        self.loadBuiltins()

    def loadBuiltins( self ) :
        self.console.push( "from math import *\n" )
        self.console.push( "from sympy import *\n" )
        self.console.push( "from sympy.abc import *\n" )

    def write( self, sometext ) :
        self.listed.text += sometext
   
    def inputOk( self, someInputString ) :
        print( "in: " + someInputString )
        if someInputString.find( "integrate" ) != -1 : 
            print( "This may take long... please wait" )
        return True

    def onBtnExecPress( self, instance ) :
        command = self.kb.current.text
        if self.inputOk( command ) :
            if self.console.push( command ) :
                print( "#More input required" )
            else : 
                self.kb.flush() 
