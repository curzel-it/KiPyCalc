# -*- coding: utf-8 -*-

from code import InteractiveConsole
import keyword
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView

from sympy import *
from sympy.abc import *
from sympy.utilities.lambdify import lambdify
import os
import sys
import time
from keyboard import *
from kivyextras import *
from history import *

FONT_NAME = "res/ubuntu-font-family-0.80/UbuntuMono-R.ttf"
FONT_SIZE = getFontSize()
DEBUG = False
INDENT = "    "
HOT_KEYS = [ 'as', 'assert', 'break', 'class', 'continue', 'def', 'del',\
             'elif', 'else', 'except', 'exec', 'finally', 'for', 'from',\
             'global', 'if', 'import', 'pass', 'print', 'pprint',\
             'raise', 'return', 'try', 'while', 'with', 'yield' ]

class PyShell( BoxLayout ) :

    def __init__( self, plotFoo ) :
        BoxLayout.__init__( self, orientation="vertical" )
        self._lastOutput = []
        self.console = InteractiveConsole()

        frm = BoxLayout( orientation="vertical" )
        self.listed = TextInput()
        self.listed.font_size = FONT_SIZE * ( 5/6.0 )
        self.listed.font_name = FONT_NAME
        self.listed.readonly = True
        self.listed.size_hint = 1, 0.3

        self.history = History()

        frm.add_widget( self.listed )
        self.kb = KiPyKeyboard( self.onBtnExecPress, plotFoo )
        self.kb.size_hint = 1, 0.7
        frm.add_widget( self.kb )
        frm.size_hint = 1,1
        self.add_widget( frm )

    def saveHtml( self ) :        
        self.history.put( History.KIPY_MSG, "Session saved on " + time.asctime() )
        path = "html/" + time.asctime().replace( " ", "_" ).replace( ":", "-" )

        if not os.path.exists( path ):
            os.makedirs( path )

        path = path + "/index.html"
        f = open( path, "w" )
        f.write( self.history.getHtml() )
        print( '#Saved to "sdcard\\org.cuuuurzel.KiPyCalc\\html\\current date"' )
        f.close()
        return path

    def start( self ) :
        if not DEBUG :
            sys.stdout = self
            sys.stderr = self
        self.history.put( History.KIPY_MSG, "Session started on " + time.asctime() )
        self.shellInit()

    def getInput( self ) :
        return self.kb.current.text

    def shellInit( self ) :
        initCode = open( "res/SHELL_INIT" ).read()
        for line in initCode.split("\n") :
            self.console.push( line )

    def write( self, sometext ) :
        self._lastOutput.append( sometext )
        self.listed.text += sometext

    def correctInput( self, stat ) :
        stat = stat.replace( "\t", INDENT )
        stat = stat.replace( "map", "lmap" )
        if stat == "\n" or stat == "" : stat = "ans\n"
        print( "in : " + stat[:-1] )

        if stat == "ans\n" or stat == "ans" :
            return "ans", True
        
        if not self.providesValidValue( stat.lower() ) :
            return stat, False
        return stat, True            

    def providesValidValue( self, stat ) :
        for key in HOT_KEYS :
            if stat.startswith( key ) : 
                if not stat[ len( key ) ].isalnum() :
                    return False
        return True

    def onBtnExecPress( self, instance ) :
        stat = self.kb.current.text + "\n"
        self.history.put( History.INPUT, stat[:-1] )
        if DEBUG :
            self._lastOutput.append( "Some output1" )
            self._lastOutput.append( "Some output2" )
        stat, updateAns = self.correctInput( stat )
        self.pushCode( stat, updateAns )
        self.history.put( History.OUTPUT, self._lastOutput[-2] )

    def pushCode( self, code, updateAns ) :
        if updateAns : code = "ans = " + code
        for line in code.split( "\n" ) :
            moreInputNeeded = self.console.push( line )
        self.afterRun( moreInputNeeded, updateAns )
        
    def withoutSpaces( self, line ) :
        return line.replace( " ", "" ).replace( "\t", "" )

    def afterRun( self, moreInputNeeded, printAns ) :
        if moreInputNeeded : 
            self.console.push( "\n" )
            print( "#Multiline instructions must be entered in one single step!" )
        else :
            if printAns : 
                self.console.push( "print( ans )\n" )
            self.kb.flush()             

    def lineIndent( self, line ) :
        i = 0
        for char in line :
            if char == " " : i += 1
        return i / 4

