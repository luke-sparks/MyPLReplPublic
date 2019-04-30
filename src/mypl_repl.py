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
# needed for load
import copy
from io import StringIO

# history
try:
    import readline
except ImportError:
    readline = None

value_table = sym_tbl.SymbolTable()
type_table = sym_tbl.SymbolTable()
repl_heap = {}
total_stmt = ast.StmtList()
cur_cmd = -1


def main():
    vocab = {'MyPL', 'bowers', 'repl', 'opl'}
    readline.parse_and_bind('tab: complete')
    readline.set_completer(make_completer(vocab))

    print('MyPL REPL Version 1.0')
    print('Use ":" for commands, :help for list of commands.')
    keepGoing = True
    while(keepGoing):
        cur_stmt = input('>>> ')
        # See if the user just pressed enter
        if (len(cur_stmt) == 0):
            pass
        # Check if a function or struct was declared
        elif ('struct' in cur_stmt or 'fun' in cur_stmt or 'while' in cur_stmt or 'if' in cur_stmt):
            final_stmt = end_loop(cur_stmt)
            run_stmt(final_stmt)
        # Check to see if the current statement is a command
        elif (cur_stmt[0] == ':'):
            if ('help' in cur_stmt):
                printAllCommands()
            elif ('load' in cur_stmt):
                # If the command is load, load whatever file the user gave
                # Get the filename by seperating the statement on the space
                cur_stmt = cur_stmt[1:].split()
                # Make sure the stmt contained a file and that it's a .mypl file
                if(len(cur_stmt) != 2):
                    print('Improper usage of load')
                    print('use ":load filename"')
                elif(".mypl" not in cur_stmt[1]):
                    print('Improper usage of load')
                    print('Can only load ".mypl" files')
                else:
                    load(cur_stmt[1])
            elif ('save' in cur_stmt):
                # If the command is save, save to given file or create new one
                # Get the filename by seperating the statement on the space
                cur_stmt = cur_stmt[1:].split()
                if cur_stmt == ["save"]:
                    cur_stmt = "repl_save.mypl"
                    save(cur_stmt)
                else:
                    save(cur_stmt[1])
            elif ('clear' in cur_stmt):
                clear()
                print('Cleared REPL')
            elif ('exit' in cur_stmt):
                keepGoing = False
                print('Goodbye\n')
            else:
                if(cur_stmt == ':'):
                    print('Missing command')
                else:
                    cur_stmt = cur_stmt[1:].split()[0]
                    print(
                        'Unrecognized command "%s", use ":help" to view all commands.' % (cur_stmt))
        # Not a command, run and evaluate the statement
        else:
            run_stmt(cur_stmt)
    # listener.stop()

def make_completer(vocab):
    def custom_complete(text, state):
        results = [x + ' ' for x in vocab if x.startswith(text)] + [None]
        return results[state]
    return custom_complete


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
        # Check to see if someone is trying to call a function w/o parameters
        # or a struct by name instead of a declared object
        struct_or_func_decl = the_interpreter.current_value
        if (isinstance(struct_or_func_decl, list)):
            if(isinstance(struct_or_func_decl[1], ast.FunDeclStmt)):
                print('Missing parentheses on function call "%s"' %
                      cur_stmt[:-1])
            elif(isinstance(struct_or_func_decl[1], ast.StructDeclStmt)):
                print('Attempting to call un-instantiated struct "%s"' %
                      cur_stmt[:-1])
            else:
                print('No one should be here')
                print(struct_or_func_decl)
        else:
            if('(' not in cur_stmt and 'struct' not in cur_stmt and 'new' not in cur_stmt):
                print(the_interpreter.current_value)
    except error.MyPLError as e:
        print('Error: %s' % e.message)
        if 'fun' in cur_stmt:
            funName = cur_stmt.split()[2]
            funName = funName.split('(')[0]
            if type_table.id_exists(funName):
                type_table.remove_id(funName)

    except TypeError as e:
        if ('unhashable type' in str(e)):
            print('Error: Cannot access elements in undeclared struct')
        else:
            print('Error: %s' % str(e))


'''
end_loop()
This function deals with multi-line structs, functions, whiles and ifs
Also checks for single-line declarations
@param current statement in the repl
'''
def end_loop(cur_stmt):
    final_stmt = cur_stmt
    # deals with 1-line declarations of structs, functions, while loops, and if statements
    # allows us to use a 'command history' in the future
    if ('struct' in final_stmt or 'fun' in final_stmt or 'while' in final_stmt or 'if' in final_stmt) and ('end' in final_stmt):
        pass
    else:
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
    try:
        f = open(filename, "r")
    except FileNotFoundError as e:
        print('Unable to find file "%s"' % filename)
        return

    print('loading "%s" into REPL' % filename)
    global type_table
    global value_table
    global repl_heap
    global total_stmt

    try:
        current_total_stmt = copy.deepcopy(total_stmt)

        file_lexer = lexer.Lexer(f)
        file_parser = parser.Parser(file_lexer)
        file_stmt_list = file_parser.parse()

        current_total_stmt.stmts.append(file_stmt_list)

        #cur_cmd = len(current_total_stmt.stmts) + 1

        # copy storage so as to not modify REPL if error
        file_type_table = type_table
        file_value_table = value_table
        file_repl_heap = repl_heap

        file_type_checker = type_checker.TypeChecker(file_type_table)
        file_stmt_list.accept(file_type_checker)
        file_interpreter = interpreter.Interpreter(
            file_value_table, file_repl_heap)
        file_interpreter.run(current_total_stmt)

        # set actual storage to the new ones if no error has been caught
        type_table = file_type_table
        value_table = file_value_table
        repl_heap = file_repl_heap
        total_stmt = copy.deepcopy(current_total_stmt)

    except error.MyPLError as e:
        print('Error: %s' % e.message)

    f.close()


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

    if filename == "":
        filename = "repl_save.mypl"

    print('saving to "%s"' % filename)
    f = open(filename, "w")
    print_visitor = ast_printer.PrintVisitor(f)
    total_stmt.accept(print_visitor)

    '''for stmt in total_stmt.stmts:
        stmt.accept(print_visitor)

    total_stmt.stmts[3].accept(print_visitor)'''

    f.close()


'''
clear()
This function clears the REPL.
'''
def clear():
    global value_table
    global type_table
    global repl_heap
    global total_stmt
    global cur_cmd

    value_table = sym_tbl.SymbolTable()
    type_table = sym_tbl.SymbolTable()
    repl_heap = {}
    total_stmt = ast.StmtList()
    cur_cmd = -1


'''
printAllCommands()
This function displays all commands that can be used on the repl
'''
def printAllCommands():
    print('~~~~~~~~~~~~~~~ REPL (Read Evaluate Print Loop) Commands ~~~~~~~~~~~~~~~~')
    print('Use ":" before your desired command to call a command. All commands are lower case')
    print('All files must be of ".mypl" extension to be loaded and saved')
    print('"help":  Prints out all commands and how to use them\n')
    print('"load":  Use load along with a filename to load a .mypl file into the REPL\n')
    print('"save":  Use save along with a filename to save all current variables, functions and structs')
    print('         If a filename is not specified, everything will be saved into a new file, repl_save.mypl\n')
    print('"clear": Clears all statements from REPL. Useful when saving and loading with files\n')
    print('"exit":  Use exit to quit out of the REPL loop')
    print()


main()
