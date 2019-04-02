#Author: Zach McKee
#Course: CPSC 326, Spring 2019
import mypl_token as token
import mypl_ast as ast
import mypl_error as error
import mypl_symbol_table as symbol_table
class TypeChecker(ast.Visitor):
    """A MyPL type checker visitor implementation where struct types
    take the form: type_id -> {v1:t1, ..., vn:tn} and function types
    take the form: fun_id -> [[t1, t2, ..., tn,], return_type]
    """
    def __init__(self):
        # initialize the symbol table (for ids -> types)
        self.sym_table = symbol_table.SymbolTable()
        # current_type holds the type of the last expression type
        self.current_type = None
        # global env (for return)
        self.sym_table.push_environment()
        # set global return type to int
        self.sym_table.add_id('return')
        self.sym_table.set_info('return', token.INTTYPE)
        # load in built-in function types
        self.sym_table.add_id('print')
        self.sym_table.set_info('print', [[token.STRINGTYPE], token.NIL])
        self.sym_table.add_id('length')
        self.sym_table.set_info('length', [[token.STRINGTYPE], token.INTTYPE])
        self.sym_table.add_id('get')
        self.sym_table.set_info('get', [[token.INTTYPE, token.STRINGTYPE], token.STRINGTYPE])
        self.sym_table.add_id('reads')
        self.sym_table.set_info('reads', [[], token.STRINGTYPE])
        self.sym_table.add_id('readi')
        self.sym_table.set_info('readi', [[], token.INTTYPE])
        self.sym_table.add_id('readf')
        self.sym_table.set_info('readf', [[], token.FLOATTYPE])
        self.sym_table.add_id('itos')
        self.sym_table.set_info('itos', [[token.INTTYPE], token.STRINGTYPE])
        self.sym_table.add_id('itof')
        self.sym_table.set_info('itof', [[token.INTTYPE], token.FLOATTYPE])
        self.sym_table.add_id('ftos')
        self.sym_table.set_info('ftos', [[token.FLOATTYPE], token.STRINGTYPE])
        self.sym_table.add_id('stoi')
        self.sym_table.set_info('stoi', [[token.STRINGTYPE], token.INTTYPE])
        self.sym_table.add_id('stof')
        self.sym_table.set_info('stof', [[token.STRINGTYPE], token.FLOATTYPE])

    def __error(self, error_msg, error_token):
        s = error_msg
        l = error_token.line
        c = error_token.column
        raise error.MyPLError(s, l, c)

    def __convert_val_to_type(self, val_token):
        if val_token == token.INTVAL or val_token == 'int':
            return token.INTTYPE
        elif val_token == token.FLOATVAL or val_token == 'float':
            return token.FLOATTYPE
        elif val_token == token.BOOLVAL or val_token == 'bool':
            return token.BOOLTYPE
        elif val_token == token.STRINGVAL or val_token == 'string':
            return token.STRINGTYPE
        return val_token
  
    def visit_stmt_list(self, stmt_list):
        # add new block (scope)
        self.sym_table.push_environment()
        for stmt in stmt_list.stmts:
            stmt.accept(self)
        # remove new block
        self.sym_table.pop_environment()
    
    def visit_expr_stmt(self, expr_stmt):
        expr_stmt.expr.accept(self)
    
    def visit_var_decl_stmt(self, var_decl):
        cur_var_name = var_decl.var_id.lexeme
        cur_var_type = None
        #See if the type was explicity declared
        if var_decl.var_type != None:
            cur_var_type = var_decl.var_type.tokentype
            #If the var type is an ID, it's a struct. Get the struct type
            if cur_var_type == token.ID:
                cur_var_type = var_decl.var_type.lexeme
        var_decl.var_expr.accept(self)
        cur_expr_type = self.current_type
        #If the type was not expicitly declared, infere it
        if cur_var_type == None:
            cur_var_type = cur_expr_type
        curr_env = self.sym_table.get_env_id()
        if self.sym_table.id_exists_in_env(cur_var_name, curr_env):
            msg = 'variable "%s" already defined in current environment' % cur_var_name
            self.__error(msg, var_decl.var_id)
        #Make sure the type of the expression matches the variable type
        if cur_expr_type != token.NIL and cur_expr_type != cur_var_type:
            msg = 'Mismatch type in variable decleration'
            self.__error(msg, var_decl.var_id)
        elif cur_var_type == token.NIL:
            msg = 'Initializing variable to nil'
            self.__error(msg, var_decl.var_id)    
        else:
            self.sym_table.add_id(cur_var_name)
            self.sym_table.set_info(cur_var_name, cur_var_type)

    def visit_assign_stmt(self, assign_stmt):
        assign_stmt.rhs.accept(self)
        rhs_type = self.current_type
        assign_stmt.lhs.accept(self)
        lhs_type = self.current_type
        if rhs_type != token.NIL and rhs_type != lhs_type:
            msg = 'Mismatch type in assignment'
            self.__error(msg, assign_stmt.lhs.path[0])

    def visit_lvalue(self, lvalue):
        var_token = lvalue.path[0]
        if not self.sym_table.id_exists(var_token.lexeme):
            msg = 'Undefined variable "%s"' % var_token.lexeme
            self.__error(msg, var_token)
        type_token = var_token
        if len(lvalue.path) > 1:
            struct_types = self.sym_table.get_info(self.sym_table.get_info(type_token.lexeme))
            for i in range(1, len(lvalue.path)):
                cur_token = lvalue.path[i].lexeme
                if cur_token in struct_types:
                    type_token = struct_types[cur_token]
                else:
                    msg = 'Undefined variable "%s" in struct "%s"' %(cur_token,self.sym_table.get_info(lvalue.path[0].lexeme))
                    self.__error(msg, lvalue.path[0])
                non_structs = [token.STRINGTYPE, token.BOOLTYPE, token.FLOATTYPE, token.INTTYPE]
                if(type_token not in non_structs):
                    struct_types = self.sym_table.get_info(type_token)
            self.current_type = type_token
        else:
            self.current_type = self.sym_table.get_info(type_token.lexeme)

    def visit_struct_decl_stmt(self, struct_decl_stmt):
        self.sym_table.add_id(struct_decl_stmt.struct_id.lexeme)
        namesAndTypes = {}
        self.sym_table.push_environment()
        for vdecl in struct_decl_stmt.var_decls:
            vdecl.accept(self)
            namesAndTypes[vdecl.var_id.lexeme] = self.sym_table.get_info(vdecl.var_id.lexeme)
        self.sym_table.pop_environment()
        self.sym_table.set_info(struct_decl_stmt.struct_id.lexeme, namesAndTypes)

    def visit_fun_decl_stmt(self, fun_decl_stmt):
        if (self.sym_table.id_exists(fun_decl_stmt.fun_name.lexeme)):
            msg = 'Function "%s" already declared' % fun_decl_stmt.fun_name.lexeme
            self.__error(msg, fun_decl_stmt.fun_name)
        self.sym_table.add_id(fun_decl_stmt.fun_name.lexeme)
        fun_params = []
        self.sym_table.push_environment()
        pastParams = []
        return_type = fun_decl_stmt.return_type
        self.sym_table.add_id('return')
        self.sym_table.set_info('return', fun_decl_stmt.return_type)
        for param in fun_decl_stmt.params:
            param.accept(self)
            param_type = self.current_type
            fun_params.append(param_type)
            if(param.param_name.lexeme in pastParams):
                msg = 'Multiple occurances of "%s" in "%s" parameters' % (param.param_name.lexeme, fun_decl_stmt.fun_name.lexeme)
                self.__error(msg, fun_decl_stmt.fun_name)
            else:
                pastParams.append(param.param_name.lexeme)
            self.sym_table.add_id(param.param_name.lexeme)
            self.sym_table.set_info(param.param_name.lexeme, param_type)
        params_and_return = [fun_params,return_type] 
        self.sym_table.set_info(fun_decl_stmt.fun_name.lexeme, params_and_return)
        fun_decl_stmt.stmt_list.accept(self)
        #Make sure the return type was correct if there was one
        if return_type.tokentype != token.NIL and self.current_type != 'return_declared':
            msg = 'Missing return statement in function "%s"' % fun_decl_stmt.fun_name.lexeme
            self.__error(msg, fun_decl_stmt.fun_name)
        self.sym_table.pop_environment()

    def visit_fun_param(self, fun_param):
        self.current_type = self.__convert_val_to_type(fun_param.param_type.lexeme)

    def visit_return_stmt(self, return_stmt):
        if(return_stmt.return_expr != None):
            return_stmt.return_expr.accept(self)
            return_type = self.current_type
        else:
            return_type = token.NIL
        isZeroExpr = False
        if isinstance(return_stmt.return_expr, ast.SimpleExpr):
            if isinstance(return_stmt.return_expr.term, ast.SimpleRValue):
                if (return_stmt.return_expr.term.val.lexeme == '0'):
                    isZeroExpr = True
        fun_return_type = self.sym_table.get_info('return')
        if fun_return_type.tokentype != return_type and not isZeroExpr and return_type != token.NIL and not fun_return_type.lexeme == return_type:
            msg = 'Incorrect return type "%s", expecting "%s"' % (return_type, fun_return_type)
            self.__error(msg, return_stmt.return_token)
        self.current_type = 'return_declared'

    def visit_while_stmt(self, while_stmt):
        while_stmt.bool_expr.accept(self)
        while_stmt.stmt_list.accept(self)

    def visit_if_stmt(self, if_stmt):
        if_stmt.if_part.bool_expr.accept(self)
        bool_expr_type = self.current_type
        if(bool_expr_type != token.BOOLTYPE):
            msg = 'Non-boolean expression in if statement'
            self.__error(msg, token.Token(bool_expr_type, "", 0,0))
        if_stmt.if_part.stmt_list.accept(self)
        for elseif in if_stmt.elseifs:
            elseif.bool_expr.accept(self)
            bool_expr_type = self.current_type
            if(bool_expr_type != token.BOOLTYPE):
                msg = 'Non-boolean expression in elif statement'
                self.__error(msg, token.Token(bool_expr_type, "", 0,0))
            elseif.stmt_list.accept(self)
        if if_stmt.has_else:
            if_stmt.else_stmts.accept(self)

    def visit_simple_expr(self, simple_expr):
        simple_expr.term.accept(self)

    def visit_simple_rvalue(self, simple_rvalue):
        self.current_type = self.__convert_val_to_type(simple_rvalue.val.tokentype)

    def visit_new_rvalue(self, new_rvalue):
        self.current_type = new_rvalue.struct_type.lexeme

    def visit_call_rvalue(self, call_rvalue):
        if not self.sym_table.id_exists(call_rvalue.fun.lexeme):
            msg = 'Undeclared function "%s"' % call_rvalue.fun.lexeme
            self.__error(msg, call_rvalue.fun)
        types_of_fun = self.sym_table.get_info(call_rvalue.fun.lexeme)
        return_type  = types_of_fun[1]
        types_of_fun = types_of_fun[0]
        types_given = call_rvalue.args
        if len(types_given) < len(types_of_fun):
            msg = 'Too few arguments in function call "%s"' % call_rvalue.fun.lexeme
            self.__error(msg, call_rvalue.fun)
        elif len(types_given) > len(types_of_fun):
            msg = 'Too many arguments in function call "%s"' % call_rvalue.fun.lexeme
            self.__error(msg, call_rvalue.fun)
        else:
            for i in range(0, len(types_of_fun)):
                types_given[i].accept(self)
                cur_type = self.current_type
                if isinstance(cur_type, token.Token):
                    if(cur_type.tokentype == 'ID'):
                        cur_type = cur_type.lexeme
                    else:
                        cur_type = cur_type.tokentype
                if cur_type != types_of_fun[i] and cur_type != token.NIL and cur_type != types_of_fun[i]:
                    msg = 'Type mismatch in function call "%s", expecting "%s", received "%s"' % (call_rvalue.fun.lexeme, types_of_fun[i], cur_type)
                    self.__error(msg, call_rvalue.fun)
        self.current_type = return_type

    def visit_id_rvalue(self, id_rvalue):
        if not self.sym_table.id_exists(id_rvalue.path[0].lexeme):
            msg = 'Undeclared variable "%s"' % id_rvalue.path[0].lexeme
            self.__error(msg, id_rvalue.path[0])
        type_token = id_rvalue.path[0] 
        if len(id_rvalue.path) > 1:
            struct_types = self.sym_table.get_info(self.sym_table.get_info(type_token.lexeme))
            for i in range(1, len(id_rvalue.path)):
                cur_token = id_rvalue.path[i].lexeme
                if cur_token in struct_types:
                    type_token = struct_types[cur_token]
                else:
                    msg = 'Undefined variable "%s" in struct "%s"' %(cur_token,self.sym_table.get_info(id_rvalue.path[0].lexeme))
                    self.__error(msg, id_rvalue.path[0])
                non_structs = [token.STRINGTYPE, token.BOOLTYPE, token.FLOATTYPE, token.INTTYPE]
                if(type_token not in non_structs):
                    struct_types = self.sym_table.get_info(type_token)
            self.current_type = type_token
        else:
            self.current_type = self.sym_table.get_info(type_token.lexeme)

    def visit_complex_expr(self, complex_expr):
        complex_expr.first_operand.accept(self)
        first_type = self.current_type
        if isinstance(first_type, token.Token):
            first_type = first_type.tokentype
        operand_type = complex_expr.math_rel.tokentype
        complex_expr.rest.accept(self)
        second_type = self.current_type
        if isinstance(second_type, token.Token):
            second_type = second_type.tokentype
        first_type = self.__convert_val_to_type(first_type)
        second_type = self.__convert_val_to_type(second_type)
        sameType = (first_type == second_type)
        if not sameType:
            msg = "Mismatched type in complex expression"
            self.__error(msg,complex_expr.math_rel)
        elif first_type == token.STRINGTYPE and operand_type != token.PLUS:
            msg = "Invalid string operation"
            self.__error(msg, complex_expr.math_rel)
        elif first_type == token.BOOLTYPE:
            msg = "Invalid boolean operation"
            self.__error(msg, complex_expr.math_rel)
        elif first_type == token.NIL:
            msg = "Invalid nil operation"
            self.__error(msg, complex_expr.math_rel)
        else:
            self.current_type = first_type
        
    def visit_bool_expr(self, bool_expr):
        #Get the types of all the expressions in the boolean expression
        bool_expr.first_expr.accept(self)
        first_type = self.current_type
        if isinstance(first_type, token.Token):
            first_type = first_type.tokentype
        second_type = None
        rest_type = None
        if(bool_expr.second_expr != None):
            bool_expr.second_expr.accept(self)
            second_type = self.current_type
            if isinstance(second_type, token.Token):
                second_type = second_type.tokentype
            
        if(bool_expr.rest != None):
            bool_expr.rest.accept(self)
            rest_type = self.current_type
            if isinstance(rest_type, token.Token):
                rest_type = rest_type.tokentype
        #If there's only a first expression, that should be the current type
        if (bool_expr.second_expr == None and bool_expr.rest == None):
            self.current_type = first_type
        else:
            #If there's a second expression, make sure any operation is valid
            #according to the type inference rules
            if(bool_expr.second_expr != None):
                types_same = first_type == second_type
                one_is_nil = first_type == token.NIL or second_type == token.NIL
                non_structs = [token.STRINGTYPE, token.BOOLTYPE, token.FLOATTYPE, token.INTTYPE]
                one_is_struct = first_type not in non_structs or second_type not in non_structs
                if(not types_same and not one_is_nil and not one_is_struct):
                    msg = "Type mismatch in boolean expression, %s and %s" % (first_type, second_type)
                    self.__error(msg, bool_expr.bool_rel)
                bool_eqls_rels = [token.EQUAL, token.NOT_EQUAL]
                if (bool_expr.bool_rel.tokentype not in bool_eqls_rels and one_is_nil):
                    msg = "Invalid boolean operation with nil"
                    self.__error(msg, bool_expr.bool_rel)
                if (bool_expr.bool_rel.tokentype not in bool_eqls_rels and one_is_struct):
                    msg =  "Invalid boolean operation with structs"
                    self.__error(msg, bool_expr.bool_rel)
                first_type = token.BOOLTYPE
            #See if there's a rest, if there is, make sure the current
            #boolean expression and the rest are booleans.
            #Only booleans can be used with AND or OR
            if(bool_expr.rest != None):
                if first_type != token.BOOLTYPE or rest_type != token.BOOLTYPE:
                    msg = 'Invalid "%s" operation with non-booleans' % bool_expr.bool_connector.lexeme
                    self.__error(msg, bool_expr.bool_connector)
                else:
                    self.current_type = token.BOOLTYPE
            else:
                self.current_type = first_type