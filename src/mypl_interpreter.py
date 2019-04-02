#Author: Zach McKee
#Course: CPSC 326, Spring 2019
import mypl_token as token
import mypl_ast as ast
import mypl_error as error
import mypl_symbol_table as sym_tbl
class ReturnException(Exception):pass

class Interpreter(ast.Visitor):
    """A MyPL interpret visitor implementation"""
    
    def __init__(self):
        # initialize the symbol table (for ids -> values)
        self.sym_table = sym_tbl.SymbolTable()
        # holds the type of last expression type
        self.current_value = None
        # the heap {oid:struct_obj}
        self.heap = {}
    
    def __error(self, msg, the_token):
        raise error.MyPLError(msg, the_token.line, the_token.column)
    
    def __built_in_fun_helper(self, call_rvalue):
        fun_name = call_rvalue.fun.lexeme
        arg_vals = []
        for arg in call_rvalue.args:
            arg.accept(self)
            arg_vals.append(self.current_value)
        #check for nil values
        for i,arg in enumerate(arg_vals):
            if arg is None:
                self.__error("Nil value error", call_rvalue.fun)
        #peform each function
        if fun_name == 'print':
            arg_vals[0] = arg_vals[0].replace(r'\n', '\n')
            print(arg_vals[0], end='')
        elif fun_name == 'length':
            self.current_value = len(arg_vals[0])
        elif fun_name == 'get':
            if 0 <= arg_vals[0] < len(arg_vals[1]):
                self.current_value = arg_vals[1][arg_vals[0]]
            else:
                self.__error('Index out of range', call_rvalue.fun)
        elif fun_name == 'reads':
            self.current_value = input()
        elif fun_name == 'readi':
            try:
                self.current_value = int(input())
            except ValueError:
                self.__error('bad int value', call_rvalue.fun)
        elif fun_name == 'readf':
            try:
                self.current_value = float(input())
            except ValueError:
                self.__error('bad float value', call_rvalue.fun)
        elif fun_name == 'itos':
            self.current_value = str(arg_vals[0])
        elif fun_name == 'itof':
            self.current_value = float(arg_vals[0])
        elif fun_name == 'ftos':
            self.current_value = str(arg_vals[0])
        elif fun_name == 'itos':
            self.current_value = str(arg_vals[0])
        elif fun_name == 'stoi':
            self.current_value = int(arg_vals[0])
        elif fun_name == 'stof':
            self.current_value = float(arg_vals[0])

    def run(self, stmt_list):
        try:
            stmt_list.accept(self)
        except ReturnException:
            pass
    
    def visit_stmt_list(self, stmt_list):
        self.sym_table.push_environment()
        for stmt in stmt_list.stmts:
            stmt.accept(self)
        self.sym_table.pop_environment()

    def visit_expr_stmt(self, expr_stmt):
        expr_stmt.expr.accept(self)
    
    def visit_var_decl_stmt(self, var_decl):
        var_decl.var_expr.accept(self)
        exp_value = self.current_value
        self.sym_table.add_id(var_decl.var_id.lexeme)
        self.sym_table.set_info(var_decl.var_id.lexeme, exp_value)

    def visit_assign_stmt(self, assign_stmt):
        assign_stmt.rhs.accept(self)
        assign_stmt.lhs.accept(self)

    def visit_lvalue(self, lvalue):
        identifier = lvalue.path[0].lexeme
        if len(lvalue.path) == 1:
            self.sym_table.set_info(identifier, self.current_value)
        else:
            identifier = self.sym_table.get_info(identifier)
            struct_vals = self.heap[identifier]
            cur_oid = identifier
            final_id = None
            for cur_id in lvalue.path[1:]:
                id_val = struct_vals[cur_id.lexeme]
                if id_val in self.heap:
                    struct_vals = self.heap[id_val]
                    cur_oid = id_val
                final_id = cur_id.lexeme
            self.heap[cur_oid][final_id] = self.current_value

    def visit_struct_decl_stmt(self, struct_decl_stmt):
        struct_name = struct_decl_stmt.struct_id.lexeme
        cur_env = self.sym_table.get_env_id()
        self.sym_table.add_id(struct_name)
        self.sym_table.set_info(struct_name, [cur_env, struct_decl_stmt])
        
    def visit_fun_decl_stmt(self, fun_decl_stmt):
        func_name = fun_decl_stmt.fun_name.lexeme
        cur_env = self.sym_table.get_env_id()
        self.sym_table.add_id(func_name)
        self.sym_table.set_info(func_name, [cur_env, fun_decl_stmt])

    def visit_fun_param(self, fun_param):
        param_name = fun_param.param_name.lexeme
        self.sym_table.add_id(param_name)
        self.sym_table.set_info(param_name, self.current_value)

    def visit_return_stmt(self, return_stmt):
        return_stmt.return_expr.accept(self)

    def visit_while_stmt(self, while_stmt):
        while_stmt.bool_expr.accept(self)
        keep_going = self.current_value
        while(keep_going):
            while_stmt.stmt_list.accept(self)
            while_stmt.bool_expr.accept(self)
            keep_going = self.current_value

    def visit_if_stmt(self, if_stmt):
        if_stmt.if_part.bool_expr.accept(self)
        if self.current_value:
            if_stmt.if_part.stmt_list.accept(self)
        else:
            found_true = False
            for a_elif in if_stmt.elseifs:
                a_elif.bool_expr.accept(self)
                if self.current_value:
                    a_elif.stmt_list.accept(self)
                    found_true = True
                    break
            if if_stmt.has_else and not found_true:
                if_stmt.else_stmts.accept(self)

    def visit_simple_expr(self, simple_expr):
        simple_expr.term.accept(self)

    def visit_simple_rvalue(self, simple_rvalue):
        if simple_rvalue.val.tokentype == token.INTVAL:
            self.current_value = int(simple_rvalue.val.lexeme)
        elif simple_rvalue.val.tokentype == token.FLOATVAL:
            self.current_value = float(simple_rvalue.val.lexeme)
        elif simple_rvalue.val.tokentype == token.BOOLVAL:
            self.current_value = True
        if simple_rvalue.val.lexeme == 'false':
            self.current_value = False
        elif simple_rvalue.val.tokentype == token.STRINGVAL:
            self.current_value = simple_rvalue.val.lexeme
        elif simple_rvalue.val.tokentype == token.NIL:
            self.current_value = None

    def visit_new_rvalue(self, new_rvalue):
        struct_info = self.sym_table.get_info(new_rvalue.struct_type.lexeme)
        cur_env = self.sym_table.get_env_id()
        self.sym_table.set_env_id(struct_info[0])
        struct_obj = {}
        self.sym_table.push_environment()
        for var_decl in struct_info[1].var_decls:
            var_decl.var_expr.accept(self)
            expr_val = self.current_value
            struct_obj[var_decl.var_id.lexeme] = expr_val
        self.sym_table.pop_environment()
        self.sym_table.set_env_id(cur_env) 
        oid = id(struct_obj)
        self.heap[oid] = struct_obj
        self.current_value = oid

    def visit_call_rvalue(self, call_rvalue):
        # handle built in functions first
        built_ins = ['print', 'length', 'get', 'readi', 'reads',
        'readf', 'itof', 'itos', 'ftos', 'stoi', 'stof']
        if call_rvalue.fun.lexeme in built_ins:
            self.__built_in_fun_helper(call_rvalue)
        else:
            func_info = self.sym_table.get_info(call_rvalue.fun.lexeme)
            cur_env = self.sym_table.get_env_id()
            arg_vals = []
            for arg in call_rvalue.args:
                arg.accept(self)
                arg_vals.append(self.current_value)
            self.sym_table.set_env_id(func_info[0])
            self.sym_table.push_environment()
            for i in range(0, len(arg_vals)):
                self.current_value = arg_vals[i]
                func_info[1].params[i].accept(self)
            func_info[1].stmt_list.accept(self)
            self.sym_table.pop_environment()
            self.sym_table.set_env_id(cur_env)

    def visit_id_rvalue(self, id_rvalue):
        var_name = id_rvalue.path[0].lexeme
        var_val = self.sym_table.get_info(var_name)
        if len(id_rvalue.path) > 1:
            struct_vals = self.heap[var_val]
            for cur_id in id_rvalue.path[1:]:
                id_val = struct_vals[cur_id.lexeme]
                if id_val in self.heap:
                    struct_vals = self.heap[id_val]
                    var_val = id_val
                else:
                    final_id = cur_id.lexeme
                    var_val = struct_vals[final_id]
        self.current_value = var_val

    def visit_complex_expr(self, complex_expr):
        complex_expr.first_operand.accept(self)
        first_val = self.current_value
        complex_expr.rest.accept(self)
        rest_val = self.current_value
        math_rel = complex_expr.math_rel.lexeme
        try:
            if math_rel == '+':
                self.current_value = first_val + rest_val
            elif math_rel == '-':
                self.current_value = first_val - rest_val
            elif math_rel == '*':
                self.current_value = first_val * rest_val
            elif math_rel == '/':
                if isinstance(first_val, int):
                    self.current_value = first_val // rest_val
                else:
                    self.current_value = first_val / rest_val
            elif math_rel == '%':
                self.current_value = first_val % rest_val
        except TypeError:
            self.__error('nil values in complex expression', complex_expr.math_rel)

    def visit_bool_expr(self, bool_expr):
        bool_expr.first_expr.accept(self)
        first_val = self.current_value
        second_val = None
        rest_val = None
        if(bool_expr.second_expr != None):
            bool_expr.second_expr.accept(self)
            second_val = self.current_value
        if(bool_expr.rest != None):
            bool_expr.rest.accept(self)
            rest_val = self.current_value
        if bool_expr.bool_rel == None and bool_expr.bool_connector == None:
            if bool_expr.negated:
                self.current_value = not first_val
            else:
                self.current_value = first_val
        else:
            if bool_expr.bool_rel != None:
                bool_rel = bool_expr.bool_rel.lexeme
                if bool_rel == '>':
                    first_val = first_val > second_val
                elif bool_rel == '<':
                    first_val = first_val < second_val
                elif bool_rel == '>=':
                    first_val = first_val >= second_val
                elif bool_rel == '<=':
                    first_val = first_val <= second_val
                elif bool_rel == '==':
                    first_val = first_val == second_val
                elif bool_rel == '!=':
                    first_val = first_val != second_val
            if bool_expr.bool_connector != None:
                bool_connector = bool_expr.bool_connector.lexeme
                if bool_expr.negated:
                    first_val = not first_val
                if bool_connector == 'and':
                    self.current_value = first_val and rest_val
                else:
                    self.current_value = first_val or rest_val
            else:
                if bool_expr.negated:
                    self.current_value = not first_val
                else:
                    self.current_value = first_val