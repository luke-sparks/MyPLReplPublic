# Author: Zach McKee
# Course: CPSC 326, Spring 2019
import mypl_token as token
import mypl_error as error
class Lexer(object):

    def __init__(self, input_stream):
        self.line = 1
        self.column = 0
        self.input_stream = input_stream
    
    def __peek(self):
        pos = self.input_stream.tell()
        symbol = self.input_stream.read(1)
        self.input_stream.seek(pos)
        return symbol
    
    def __read(self):
        return self.input_stream.read(1)

    def __remove_whitespace(self):
        if(self.__peek() == ' '):
            while(self.__peek() == ' '):
                self.__read()
                self.column += 1

    def next_token(self):
        curSymbol = ''
        
        #Remove spaces
        self.__remove_whitespace()

        #Remove newlines if found
        if (self.__peek() == '\n') :
            while(self.__peek() == '\n'):
                self.__read()
                self.line += 1
            self.column = 0

        #If I see a comment, get to the next line
        if(self.__peek() == '#'):
            while(self.__peek() != '\n' and self.__peek() != ''):
                self.__read()
                self.column += 1
            if (self.__read() != ''):
                self.line += 1
                self.column = 0
            return self.next_token()

        #If there is a letter, get the whole identifyer
        if(self.__peek().isalpha()):
            while(self.__peek().isalpha() or self.__peek().isdigit() or self.__peek() == '_'):
                curSymbol += self.__read()
                self.column += 1

        #If there are double quotes, get the whole string
        elif(self.__peek() == '"') :
            curSymbol += self.__read()
            self.column += 1
            #Keep reading in the string until the next double quotes are found
            while(self.__peek() != '"' and self.__peek() != '\n' and self.__peek() != ''):
                curSymbol += self.__read()
                self.column += 1
            #Check to see if there was a newline or missing closing quote
            if(self.__peek() == '\n') :
                raise error.MyPLError("reached newline reading string", self.line, self.column + 1)
            elif(self.__peek() != '"'):
                raise error.MyPLError('missing closing quotes' , self.line, self.column + 1)
            else:
                curSymbol += self.__read()
                self.column += 1
            
        #If there is a digit, get the whole number
        elif(self.__peek().isdigit()):
            #Keep reading until you do not find any more digits
            while(self.__peek().isdigit()):
                curSymbol += self.__read()
                self.column += 1
                if(curSymbol == '0' and self.__peek().isdigit()):
                    raise error.MyPLError('unexpeted symbol "%s"' % self.__peek(), self.line, self.column + 1)
            #If theres a period, it's a float.
            if(self.__peek() == '.'):
                curSymbol += self.__read()
                self.column += 1
                changed = 0
                #Keep reading digits after the period
                while(self.__peek().isdigit()):
                    curSymbol += self.__read()
                    self.column += 1
                    changed = 1
                if(self.__peek().isalpha()):
                    raise error.MyPLError('unexpected symbol "%s"' % self.__peek(), self.line, self.column + 1)
                #Make sure there are digits after the decimal
                if(changed == 0):
                    raise error.MyPLError("missing digit in float value", self.line, self.column + 1)
                #Make sure there is only one decimal point
                elif(self.__peek() == '.'):
                    raise error.MyPLError("Too many decimal points in float value", self.line, self.column + 1)
            elif (self.__peek().isalpha()):
                raise error.MyPLError('unexpcted symbol "%s"' % self.__peek(), self.line, self.column + 1)
        #If nothing above was triggerd,
        #the next symbol is punctuation or EOS
        else:
            curSymbol += self.__read()
            #If the symbol is EOS, do not increment the colmumn
            if(curSymbol == '!'  and self.__peek() != '='):
                error.MyPLError('missing "=" after "!"', self.line, self.column)
            if(curSymbol != ''):
                self.column += 1
            #Check to see if the symbol is >=, <=, ==, or != and include the =
            #second equals sign and incriment the column
            if ((curSymbol == '>' or curSymbol == '=' or curSymbol == '!' or curSymbol == '<') and self.__peek() == '='):
                curSymbol += self.__read()
                self.column += 1
        
        #Check the current symbol against all possibilities and return
        #a token of the correct type
        #Verify the symbol is not a space.
        #If it is, return the next token
        if(curSymbol == ' ' or curSymbol == '\t'):
            return self.next_token()

        if(curSymbol == ''):
            return token.Token(token.EOS, curSymbol, self.line, self.column)
        elif (curSymbol == '='):
            return token.Token(token.ASSIGN, curSymbol, self.line, self.column)
        elif (curSymbol == ','):
            return token.Token(token.COMMA, curSymbol, self.line, self.column)
        elif (curSymbol == ':'):
            return token.Token(token.COLON, curSymbol, self.line, self.column)
        elif (curSymbol == '/'):
            return token.Token(token.DIVIDE, curSymbol, self.line, self.column)
        elif (curSymbol == '.'):
            return token.Token(token.DOT, curSymbol, self.line, self.column)
        elif (curSymbol == '=='):
            return token.Token(token.EQUAL, curSymbol, self.line, self.column - 1)
        elif (curSymbol == '>'):
            return token.Token(token.GREATER_THAN, curSymbol, self.line, self.column)
        elif (curSymbol == '>='):
            return token.Token(token.GREATER_THAN_EQUAL, curSymbol, self.line, self.column - 1)
        elif (curSymbol == '<'):
            return token.Token(token.LESS_THAN, curSymbol, self.line, self.column)
        elif (curSymbol == '<='):
            return token.Token(token.LESS_THAN_EQUAL, curSymbol, self.line, self.column - 1)
        elif (curSymbol == '!='):
            return token.Token(token.NOT_EQUAL, curSymbol, self.line, self.column - 1)
        elif (curSymbol == '('):
            return token.Token(token.LPAREN, curSymbol, self.line, self.column)
        elif (curSymbol == ')'):
            return token.Token(token.RPAREN, curSymbol, self.line, self.column)
        elif (curSymbol == '-'):
            return token.Token(token.MINUS, curSymbol, self.line, self.column)
        elif (curSymbol == '%'):
            return token.Token(token.MODULO, curSymbol, self.line, self.column)
        elif (curSymbol == '*'):
            return token.Token(token.MULTIPLY, curSymbol, self.line, self.column)
        elif (curSymbol == '+'):
            return token.Token(token.PLUS, curSymbol, self.line, self.column)
        elif (curSymbol == ';'):
            return token.Token(token.SEMICOLON, curSymbol, self.line, self.column)
        elif (curSymbol == 'bool'):
            return token.Token(token.BOOLTYPE, curSymbol, self.line, self.column - len(curSymbol) + 1)
        elif (curSymbol == 'int'):
            return token.Token(token.INTTYPE, curSymbol, self.line, self.column - len(curSymbol) + 1)
        elif (curSymbol == 'float'):
            return token.Token(token.FLOATTYPE, curSymbol, self.line, self.column - len(curSymbol) + 1)
        elif (curSymbol == 'string'):
            return token.Token(token.STRINGTYPE, curSymbol, self.line, self.column - len(curSymbol) + 1)
        elif (curSymbol == 'struct'):
            return token.Token(token.STRUCTTYPE, curSymbol, self.line, self.column - len(curSymbol) + 1)
        elif (curSymbol == 'and'):
            return token.Token(token.AND, curSymbol, self.line, self.column - len(curSymbol) + 1)
        elif (curSymbol == 'or'):
            return token.Token(token.OR, curSymbol, self.line, self.column - len(curSymbol) + 1)
        elif (curSymbol == 'not'):
            return token.Token(token.NOT, curSymbol, self.line, self.column - len(curSymbol) + 1)
        elif (curSymbol == 'while'):
            return token.Token(token.WHILE, curSymbol, self.line, self.column - len(curSymbol) + 1)
        elif (curSymbol == 'do'):
            return token.Token(token.DO, curSymbol, self.line, self.column - len(curSymbol) + 1)
        elif (curSymbol == 'if'):
            return token.Token(token.IF, curSymbol, self.line, self.column - len(curSymbol) + 1)
        elif (curSymbol == 'then'):
            return token.Token(token.THEN, curSymbol, self.line, self.column - len(curSymbol) + 1)
        elif (curSymbol == 'else'):
            return token.Token(token.ELSE, curSymbol, self.line, self.column - len(curSymbol) + 1)
        elif (curSymbol == 'elif'):
            return token.Token(token.ELIF, curSymbol, self.line, self.column - len(curSymbol) + 1)
        elif (curSymbol == 'end'):
            return token.Token(token.END, curSymbol, self.line, self.column - len(curSymbol) + 1)
        elif (curSymbol == 'fun'):
            return token.Token(token.FUN, curSymbol, self.line, self.column - len(curSymbol) + 1)
        elif (curSymbol == 'var'):
            return token.Token(token.VAR, curSymbol, self.line, self.column - len(curSymbol) + 1)
        elif (curSymbol == 'set'):
            return token.Token(token.SET, curSymbol, self.line, self.column - len(curSymbol) + 1)
        elif (curSymbol == 'return'):
            return token.Token(token.RETURN, curSymbol, self.line, self.column - len(curSymbol) + 1)
        elif (curSymbol == 'new'):
            return token.Token(token.NEW, curSymbol, self.line, self.column - len(curSymbol) + 1)
        elif (curSymbol == 'nil'):
            return token.Token(token.NIL, curSymbol, self.line, self.column - len(curSymbol) + 1)
        elif (curSymbol == 'true' or curSymbol == 'false'):
            return token.Token(token.BOOLVAL, curSymbol, self.line, self.column - len(curSymbol) + 1)
        elif ('"' in curSymbol):
            return token.Token(token.STRINGVAL, curSymbol[1:len(curSymbol)-1], self.line, self.column - len(curSymbol) + 1)
        elif (curSymbol[0].isdigit()):
            if('.' in curSymbol):
                return token.Token(token.FLOATVAL, curSymbol, self.line, self.column - len(curSymbol) + 1)
            else:
                return token.Token(token.INTVAL, curSymbol, self.line, self.column - len(curSymbol) + 1)
        else:
            return token.Token(token.ID, curSymbol, self.line, self.column - len(curSymbol) + 1)