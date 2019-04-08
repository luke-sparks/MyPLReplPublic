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
import mypl_print_visitor as ast_printer
import sys
from io import StringIO
# install https://pypi.org/project/pynput/#files
# pynput is being frustrating so I may use something else
# from pynput import keyboard
# from pynput.keyboard import Key
# from pynput.keyboard import Key, Controller

value_table = sym_tbl.SymbolTable()
type_table = sym_tbl.SymbolTable()
repl_heap = {}
total_stmt = ast.StmtList()
cur_cmd = -1

def main():
    print('MyPL REPL Version 0.4')
    print('Use ":" for commands, :help for list of commands.')
    keepGoing = True
    '''listener = keyboard.Listener(on_press = on_press)
    listener.start()'''
    '''up_listener = keyboard.Listener(on_press = on_press(Key.up))
    down_listener = keyboard.Listener(on_press = on_press(Key.down))
    up_listener.start()
    down_listener.start()'''
    while(keepGoing):
        cur_stmt = input('>>> ')
        #See if the user just pressed enter
        if (len(cur_stmt) == 0):
            pass
        #Check if a function or struct was declared
        elif ('struct' in cur_stmt or 'fun' in cur_stmt or 'while' in cur_stmt or 'if' in cur_stmt):
            final_stmt = end_loop(cur_stmt)
            run_stmt(final_stmt)
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
                #Get the filename by seperating the statement on the space
                cur_stmt = cur_stmt[1:].split()
                #Make sure the stmt contained a file and that it's a .mypl file
                if(len(cur_stmt) != 2):
                    print('Improper usage of save')
                    print('use ":save filename"')
                elif(".mypl" not in cur_stmt[1]):
                    print('Improper usage of save')
                    print('Can only save ".mypl" files')
                else:
                    save(cur_stmt[1])
                
            elif ('exit' in cur_stmt):
                keepGoing=False
                print('Goodbye\n')
            else:
                cur_stmt = cur_stmt[1:].split()[0]
                print('Unrecognized command "%s", use ":help" to view all commands.' % (cur_stmt))
        #Not a command, run and evaluate the statement
        else:
            run_stmt(cur_stmt)
    #listener.stop()

'''
run_stmt()
this function takes a statement given by the user and attempts to evaluate it within MyPL
@param the current user defined statement
'''

def run_stmt(cur_stmt):
    try:
        the_lexer = lexer.Lexer(StringIO(cur_stmt))
        the_parser = parser.Parser(the_lexer)
        stmt_list = the_parser.parse()
        the_type_checker = type_checker.TypeChecker(type_table)
        stmt_list.accept(the_type_checker)
        the_interpreter = interpreter.Interpreter(value_table, repl_heap)
        the_interpreter.run(stmt_list)
        total_stmt.stmts.append(stmt_list)
        cur_cmd = len(total_stmt.stmts) + 1

        if('print(' not in cur_stmt and 'struct' not in cur_stmt and 'fun' not in cur_stmt and 'new' not in cur_stmt):
            print('the_interpreter.current_value')
            print(the_interpreter.current_value)

    except error.MyPLError as e:
        print('Error: %s' % e.message)
    except TypeError as e:
        if ('unhashable type' in str(e)):
            print('Error: Cannot access elements in undeclared struct')
        else:
            print('Error: %s' % str(e))

'''
commenting to come, deals with structs, functions, whiles and ifs
'''
def end_loop(cur_stmt):
    final_stmt = cur_stmt
    line = '\n' + input('... ')
    if ('struct' in line or 'fun' in line or 'while' in line or 'if' in line):
        final_stmt += end_loop(line)
        line = '\n' + input('... ')
    while 'end' not in line:
        final_stmt += line
        line = '\n' + input('... ')
    final_stmt += line

    return final_stmt

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
    #total_lexer = lexer.Lexer(StringIO(total_stmt))
    #total_parser = parser.Parser(total_lexer)
    #total_stmt_list = total_parser.parse()

    print('saving to "%s"' % filename)
    f = open(filename, "w")
    print_visitor = ast_printer.PrintVisitor(f)
    total_stmt.accept(print_visitor)

    '''for stmt in total_stmt.stmts:
        stmt.accept(print_visitor)

    total_stmt.stmts[3].accept(print_visitor)'''

    f.close()
    

'''
printAllCommands()
This function displays all commands that can be used on the repl
'''
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

'''def on_press(key):
    global cur_cmd
    try:
        #print(key)
        if cur_cmd > -1:
            total_stmt.stmts[cur_cmd].accept(sys.stdout)
            cur_cmd -= 1
            print('hi')
        if key == Key.up:
            if cur_cmd > -1:
                total_stmt.stmts[cur_cmd].accept(sys.stdout)
                print('test')
                cur_cmd -= 1
        elif key == Key.down:
            if cur_cmd > -1:
                total_stmt.stmts[cur_cmd].accept(sys.stdout)
                cur_cmd += 1
    except AttributeError as e:
        print('error')
    
    try:
        print('alphanumeric key {0} pressed'.format(key.char))
    except AttributeError:
        print('special key {0} pressed'.format(key))'''
        
'''def on_release(key):
    print('{0} released'.format(
        key))
    if key == keyboard.Key.esc:
        # Stop listener
        return False'''

main()