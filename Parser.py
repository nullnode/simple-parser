import sys
from TokenType import TokenType
from semantics import semantics
from queue import *

# Simple parser for Lua, by Alex Henson
# This program will take the output of a lexical analyzer and create a flattened parse tree.

# Changelog 1: alpha build completed, basic functionality with minimal inputs
# Changelog 2: test file forms a complete parse tree! now let's make it work with the other test files!
# Changelog 3: tweaked the id function to iterate through operators, fixed issue with stuff like x = x + 1
# Changelog 4: added delimiter | to certain keywords to help with the interpreter in project 3

# Addendum to Changelog 4:
'''
The addition of a | delimiter to keywords such as IF, WHILE, UNTIL, will allow the interpreter to capture the
final character and append the following arithmetic/relative expressions to the statement! This is a huge bonus 
which will allow us to combine statements/comparisons.
'''


class Parser(object):
    tree = semantics()
    tokenList = TokenType()

    #  our initializer will take in a file and read all of the lines (python has no .hasNext() like java!
    #  we'll strip our lines into single lines and then enumerate our input so we can access them individually!
    #  we're taking the enumerated file and adding each line to our tokens array so we can process them.
    #  we're also adding a list of the tokens to the tokens array in our tree file for archival purposes.
    def __init__(self, file):
        self.tokens = []

        with open(file) as input:  # sorta like while (lua.hasNext()), runs a block of code after opening a file
            content = input.readlines()
            content = [line.strip() for line in content]
        for sourceLine, line in enumerate(content):
            self.tokens.append(line)

    def print(self):
        for meanings in self.tree.bnf:
            print(str(meanings))

    # the bread & butter of the parser! first step is to call checkFirst() which will make sure our program has the
    # proper syntax to begin a function, ie: function (x)
    # look at the checkFirst() function and youll see why our second step is to set our index to 4, it's because we
    # have already looked at index 0-3 to make sure we have FUNCTION, ID, LEFT_PAREN, RIGHT_PAREN.
    # Next, we're iterating through our tokens until we reach FINISH, then we call our compare function while also
    # making sure aren't going out of bounds in our array by double-checking that the next token isn't FINISH.
    def parse(self):
        self.checkFirst()

        index = 4
        while self.tokens[index] != "FINISH":
            token = self.tokens[index]
            next = self.tokens[index + 1]
            self.compare(token, next, index)
            if self.tokens[index + 1] == "FINISH":
                break
            index += 1

    #  we're doing some preliminary checks to see if our function is syntactically correct!
    #  first let's make sure we have a function, followed by an identifier and left/right parenthesis
    #  we're basically making sure our program starts with something like function (x)
    def checkFirst(self):
        if self.tokens[0] != "FUNCTION":
            raise Exception("Program needs to start with FUNCTION")

        if self.tokens[1] != "ID":
            raise Exception("Program needs an ID for function")

        if self.tokens[2] != "LEFT_PAREN":
            raise Exception("Program needs left parenthesis")

        if self.tokens[3] != "RIGHT_PAREN":
            raise Exception("Program needs right parenthesis")

        self.tree.bnf.append("<program> -> function id()")

    # when our parser calls compare, we take in a token and also the NEXT token in the list! this allows us to
    # compare the two tokens and evaluate what procedure is being done in a very basic sense. our other functions
    # will determine any further complexity.
    def compare(self, token,  next, index):

        if token == "ID":
            self.idToken(next, index)
        elif token == "WHILE":
            self.whileToken(next, index)
        elif token == "DO":
            self.doToken()
        elif token == "END":
            self.endToken()
        elif token == "PRINT":
            self.printToken(next, index)
        elif token == "IF":
            self.ifToken()
        elif token == "UNTIL":
            self.untilToken()
        elif token == "REPEAT":
            self.repeatToken()
        elif token == "FOR":
            self.forToken()
        elif token == "ELSE":
            self.elseToken()

    #  The following functions represent keywords from the lexical analyzer and thereby we parse by specific functions:
    #  When a certain keyword is used, we append our parse tree with the relevant form. Take special note of ID function
    #  and also our operators function.
    #  Example: We have a WHILE token, so we append our parse tree with: <statement> -> <while_statement> |
    #  We use | at the end of *certain* keywords for use as a delimiter, because we know a while statement will require
    #  us to have left/right parenthesis and a statement inside. Thus, our interpreter will be able to see the | and
    #  add the necessary parenthesis and statement inside the loop.

    def elseToken(self):
        self.tree.append("<statement> -> <ELSE> |")  # delimiter not entirely necessary, added just in case
        # NOTE: the delimiter is not necessary here because we know aan ELSE statement will be on its own separate line

    def forToken(self):
        self.tree.bnf.append("<statement> -> <for> |")  # delimiter | added
        #  we have a | delimiter so we can grab the final character and append the conditional

    def repeatToken(self):
        self.tree.bnf.tree.append("<statement> -> <repeat> |")

    def untilToken(self):
        self.tree.bnf.tree.append("<statement> -> <until> |") # delimiter | added
        # the | delimiter allows us to grab the final char and ask "oh our last char is |? okay, whats the conditional?

    def ifToken(self):
        self.tree.bnf.append("<statement> -> <if statement> |") # delimited by |
        #  we see that our final char is | in the interpreter, so what's the conditional for the if statement?

    def printToken(self, next, index):
        if next != "LEFT_PAREN":
            raise Exception("print statement needs a left parenthesis")
        look = self.tokens[index + 2]
        if look == "ID":
            self.tree.bnf.append("<statement> -> <print_statement> <id>")
        look = self.tokens[index + 3]
        if look != "RIGHT_PAREN":
            raise Exception("end of print function needs a right parenthesis")

    def endToken(self):
        self.tree.bnf.append("<statement> -> <end>")

    def whileToken(self, next, index):
        self.tree.bnf.append("<statement> -> <while statement> |")  # the next tokens will be the conditional
        #  we're adding a | as a delimiter so the interpreter can pick up the last char and append the conditional

    def doToken(self):
        self.tree.bnf.append("<statement> -> <do>")  # correct bnf for this?

    def idToken(self, next, index):
        look = self.tokens[index + 2]  # we're looking ahead to the next token so see what our ID is doing
        if next == "ASSIGN_OPERATOR" and look == "LITERAL_INTEGER": # we're assigning our var to a number!
            self.tree.bnf.append("<assignment_statement> -> <id> <assignment_operator> <literal_integer>")
        elif next == "ASSIGN_OPERATOR" and look == "ID":  # we're assigning our var to another var! but wait...
            # okay, are we assigning x = y? are we assigning x = x + 2? x = x * 2? LETS TAKE A LOOK!
            peak = self.tokens[index + 3]  # taking a peak at what comes next in our tokens!
            for operators in self.tokenList.operators:  # iterating through our special operators array from TokenType!
                if peak == operators:  # oh heck, we found an arithmetic operator is the next token!
                    sneak = self.tokens[index + 4]  # lets SNEAK a peak and find out what our var is doing work on!
                    self.tree.bnf.append("<assignment_statement> -> <id> <assignment_operator> <id>" + " <" + operators + "> " + "<" + sneak + ">")
                    #  the line above is a clever way of adding a statement to our tree that says the following:
                    #  "here is my var, i want to assign it to THIS var BUT i also want to do some arithmetic to it!"
        self.operators(next, index)

    #  function which iterates through some basic relative expressions done to a var
    def operators(self, next, index):
        look = self.tokens[index + 2]

        if next == "LT_OPERATOR" and look == "LITERAL_INTEGER":
            self.tree.bnf.append("<relative expression> -> <id> <LT_Operator> <literal_integer>")
        elif next == "LT_OPERATOR" and look == "ID":
            self.tree.bnf.append("<relative expression> -> <id> <LT_Operator> <id>")

        elif next == "GT_OPERATOR" and look == "LITERAL_INTEGER":
            self.tree.bnf.append("<relative expression> -> <id> <GT_Operator> <literal_integer>")
        elif next == "GT_OPERATOR" and look == "ID":
            self.tree.bnf.append("<relative expression> -> <id> <GT_Operator> <id>")

        elif next == "EQ_OPERATOR" and look == "LITERAL_INTEGER":
            self.tree.bnf.append("<relative expression> -> <id> <EQ_Operator> <literal_integer>")
        elif next == "EQ_OPERATOR" and look == "ID":
            self.tree.bnf.append("<relative expression> -> <id> <EQ_Operator> <id>")

        elif next == "NE_OPERATOR" and look == "LITERAL_INTEGER":
            self.tree.bnf.append("<relative expression> -> <id> <NE_Operator> <literal_integer>")
        elif next == "NE_OPERATOR" and look == "ID":
            self.tree.bnf.append("<relative expression> -> <id> <NE_Operator> <id>")

        ''''' THE FOLLOWING CODE HAS BEEN COMMENTED OUT BECAUSE IT IS NO LONGER NEEDED:
              Look at TokenType class and notice that we have a special array for holding arithmetic expressions!
              
              
        elif next == "DIV_OPERATOR" and look == "LITERAL_INTEGER":
            self.tree.bnf.append("<arithmetic expression> -> <id> <DIV_Operator> <literal_integer>")
        elif next == "DIV_OPERATOR" and look == "ID":
            self.tree.bnf.append("<arithmetic expression> -> <id> <DIV_Operator> <id>")

        elif next == "ADD_OPERATOR" and look == "LITERAL_INTEGER":
           self.tree.bnf.append("<arithmetic expression> -> <id> <ADD_Operator> <literal_integer>")
        elif next == "ADD_OPERATOR" and look == "ID":
           self.tree.bnf.append("<arithmetic expression> -> <id> <ADD_Operator> <id>")

        elif next == "SUB_OPERATOR" and look == "LITERAL_INTEGER":
            self.tree.bnf.append("<arithmetic expression> -> <id> <SUB_Operator> <literal_integer>")
        elif next == "SUB_OPERATOR" and look == "ID":
            self.tree.bnf.append("<arithmetic expression> -> <id> <SUB_Operator> <id>")

        elif next == "MULT_OPERATOR" and look == "LITERAL_INTEGER":
            self.tree.bnf.append("<arithmetic expression> -> <id> <MULT_Operator> <literal_integer>")
        elif next == "MULT_OPERATOR" and look == "ID":
            self.tree.bnf.append("<arithmetic expression> -> <id> <MULT_Operator> <id>")

        elif next == "MOD_OPERATOR" and look == "LITERAL_INTEGER":
            self.tree.bnf.append("<arithmetic expression> -> <id> <MOD_Operator> <literal_integer>")
        elif next == "MOD_OPERATOR" and look == "ID":
            self.tree.bnf.append("<arithmetic expression> -> <id> <MOD_Operator> <id>")
'''

