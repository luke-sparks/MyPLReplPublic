#!/usr/bin/python3
#
# Authors: Zach McKee, Luke Sparks, Brewer Slack
# Final Project
# Desctription:
# Implementation of a REPL loop for usage with MyPL
import mypl_error as error
import mypl_lexer as lexer
import mypl_token as token
import mypl_parser as parser
import mypl_ast as ast
import mypl_type_checker as type_checker
import mypl_interpreter as interpreter
import mypl_symbol_table as sym_tbl
import mypl_error as error
import sys
from io import StringIO

value_table = sym_tbl.SymbolTable()
type_table = sym_tbl.SymbolTable()
repl_heap = {}

def main():
    print('MyPL REPL Version 0.4')
    print('Use ":" for commands, :help for list of commands.')
    keepGoing = True
    while(keepGoing):
        cur_stmt = input('>>> ')
        #See if the user just pressed enter
        if (len(cur_stmt) == 0):
            pass
        #Check to see if the current statement is a command
        elif (cur_stmt[0] == ':'):
            if ('help' in cur_stmt):
                printAllCommands()
            elif ('load' in cur_stmt):
                #If the command is load, load whatever file the user gave
                #Get the filename by seperating the statement on the space
                cur_stmt = cur_stmt[1:].split()
                #Make sure the stmt contained a file and that it's a .mypl file
                if(len(cur_stmt) != 2):
                    print('Improper usage of load')
                    print('use ":load filename"')
                elif(".mypl" not in cur_stmt[1]):
                    print('Improper usage of load')
                    print('Can only load ".mypl" files')
                else:
                    load(cur_stmt[1])
            elif ('save' in cur_stmt):
                #If the command is save, save to given file or create new one
                print('Save functionality currently not implemented')
            elif ('exit' in cur_stmt):
                keepGoing=False
                print('Goodbye\n')
            else:
                cur_stmt = cur_stmt[1:].split()[0]
                print('Unrecognized command "%s", use ":help" to view all commands.' % (cur_stmt))
        #Not a command, run and evaluate the statement
        else:
            try:
                the_lexer = lexer.Lexer(StringIO(cur_stmt))
                the_parser = parser.Parser(the_lexer)
                stmt_list = the_parser.parse()
                the_type_checker = type_checker.TypeChecker(type_table)
                stmt_list.accept(the_type_checker)
                the_interpreter = interpreter.Interpreter(value_table, repl_heap)
                the_interpreter.run(stmt_list)
            except error.MyPLError as e:
                print('Error: %s' % e.message)



'''
load()
This function takes in a filename as a string and loads
the contents from the files into the current REPL context.
@param name of file to be opened
'''
def load(filename):
    print('loading "%s"... not' % filename)

'''
save()
This function takes either a filename as a string or an empty string.
If it recieves a filename, it will save the current context to that file.
Else it will save to repl_save.mypl
@param name of file to be save to or empty string
'''
def save(filename):
    print('saving to "%s"... not' % filename)

def printAllCommands():
    print('~~~~~~~~~~~~~~~ REPL (Read Evaluate Print Loop) Commands ~~~~~~~~~~~~~~~~')
    print('Use ":" before your desired command to call a command. All commands are lower case')
    print('All files must be of ".mypl" extension to be loaded and saved')
    print('"help":\tPrints out all commands and how to use them\n')
    print('"load":\tUse load along with a filename to load a .mypl file into the REPL\n')
    print('"save":\tUse save along with a filename to save all current variables, functions and structs')
    print('       \tIf a filename is not specified, everything will be saved into a new file, repl_save.mypl\n')
    print('"exit":\tUse exit to quit out of the REPL loop')
    print()

main()