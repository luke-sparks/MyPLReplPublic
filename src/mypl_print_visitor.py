#Author Zach McKee
#Couse: CPSC 326, Spring 2019
import mypl_token as token
import mypl_ast as ast
class PrintVisitor(ast.Visitor):
    """An AST pretty printer"""
    def __init__(self, output_stream):
        self.indent = 0                    # to increase/decrease indent level
        self.output_stream = output_stream # where printing to
    
    def __indent(self):
        """Get default indent of four spaces"""
        return ' ' * self.indent
    
    def __write(self, msg):
        self.output_stream.write(msg)
    
    def visit_stmt_list(self, stmt_list):
        for stmt in stmt_list.stmts:
            stmt.accept(self)
    
    def visit_expr_stmt(self, expr_stmt):
        self.__write(self.__indent())
        expr_stmt.expr.accept(self)
        self.__write(';\n')

    def visit_var_decl_stmt(self, var_decl_stmt):
        self.__write(self.__indent())
        self.__write('var ' + var_decl_stmt.var_id.lexeme)
        if var_decl_stmt.var_type is not None:
            self.__write(': ' + var_decl_stmt.var_type.lexeme)
        self.__write(' = ')
        var_decl_stmt.var_expr.accept(self)
        self.__write(';\n')

    def visit_assign_stmt(self, assign_stmt):
        self.__write(self.__indent())
        self.__write('set ')
        assign_stmt.lhs.accept(self)
        self.__write(' = ')
        assign_stmt.rhs.accept(self)
        self.__write(';\n')

    def visit_lvalue(self, lvalue):
        pathLength = len(lvalue.path)
        if pathLength == 1:
            self.__write(lvalue.path[0].lexeme)
        else:
            self.__write(lvalue.path[0].lexeme)
            for token in lvalue.path[1:]:
                self.__write('.')
                self.__write(token.lexeme)
    
    def visit_struct_decl_stmt(self, struct_decl_stmt):
        self.__write('\nstruct ' + struct_decl_stmt.struct_id.lexeme + '\n')
        self.indent += 4
        for stmt in struct_decl_stmt.var_decls:
            stmt.accept(self)
        self.indent -= 4
        self.__write('end\n\n')
    
    def visit_fun_decl_stmt(self, fun_decl_stmt):
        self.__write('\nfun ')
        if fun_decl_stmt.return_type is not None:
             self.__write(fun_decl_stmt.return_type.lexeme + ' ')
        self.__write(fun_decl_stmt.fun_name.lexeme +'(')
        numParams = len(fun_decl_stmt.params)
        if numParams >= 1:
            fun_decl_stmt.params[0].accept(self)
            if numParams > 1:
                for stmt in fun_decl_stmt.params[1:]:
                    self.__write(', ')
                    stmt.accept(self)
        self.__write(')\n')
        self.indent += 4
        fun_decl_stmt.stmt_list.accept(self)
        self.indent -= 4
        self.__write('end\n\n')

    def visit_fun_param(self, fun_param):
        self.__write(fun_param.param_name.lexeme + ': ')
        self.__write(fun_param.param_type.lexeme)

    def visit_return_stmt(self, return_stmt):
        self.__write(self.__indent())
        self.__write('return')
        if return_stmt.return_expr is not None:
            self.__write(' ')
            return_stmt.return_expr.accept(self)
        self.__write(';\n')

    def visit_while_stmt(self, while_stmt):
        self.__write(self.__indent())
        self.__write('while ')
        while_stmt.bool_expr.accept(self)
        self.__write(' do\n')
        self.indent += 4
        while_stmt.stmt_list.accept(self)
        self.indent -= 4
        self.__write(self.__indent())
        self.__write('end\n')

    def visit_if_stmt(self, if_stmt):
        self.__write(self.__indent())
        self.__write('if ')
        if_stmt.if_part.bool_expr.accept(self)
        self.__write(' then\n')
        self.indent += 4
        if_stmt.if_part.stmt_list.accept(self)
        self.indent -= 4
        for basicIf in if_stmt.elseifs:
            self.__write(self.__indent())
            self.__write('elif ')
            basicIf.bool_expr.accept(self)
            self.__write(' then\n')
            self.indent += 4
            basicIf.stmt_list.accept(self)
            self.indent -= 4
        if if_stmt.has_else:
            self.__write(self.__indent())
            self.__write('else\n')
            self.indent += 4
            if_stmt.else_stmts.accept(self)
            self.indent -= 4
        self.__write(self.__indent())
        self.__write('end\n')

    def visit_simple_expr(self, simple_expr):
        simple_expr.term.accept(self)

    def visit_simple_rvalue(self, simple_rvalue):
        if simple_rvalue.val.tokentype == token.STRINGVAL:
            self.__write('"' + simple_rvalue.val.lexeme + '"')
        else:
            self.__write(simple_rvalue.val.lexeme)

    def visit_new_rvalue(self, new_rvalue):
        self.__write('new ')
        self.__write(new_rvalue.struct_type.lexeme)

    def visit_call_rvalue(self, call_rvalue):
        self.__write(call_rvalue.fun.lexeme + '(')
        numParams = len(call_rvalue.args)
        if numParams >= 1:
            call_rvalue.args[0].accept(self)
            if numParams > 1:
                for param in call_rvalue.args[1:]:
                    self.__write(', ')
                    param.accept(self)
        self.__write(')')

    def visit_id_rvalue(self, id_rvalue):
        path = id_rvalue.path
        numInPath = len(path)
        self.__write(path[0].lexeme)
        if numInPath > 1:
            for ID in path[1:]:
                self.__write('.' + ID.lexeme)

    def visit_complex_expr(self, complex_expr):
        self.__write('(')
        complex_expr.first_operand.accept(self)
        self.__write(' ' + complex_expr.math_rel.lexeme + ' ')
        complex_expr.rest.accept(self)
        self.__write(')')

    def visit_bool_expr(self, bool_expr):
        if bool_expr.rest is not None:
            self.__write('(')
        if bool_expr.negated:
            self.__write("not ")
        if bool_expr.second_expr is not None:
            self.__write('(')
            bool_expr.first_expr.accept(self)
            self.__write(" " + bool_expr.bool_rel.lexeme + " ")
            bool_expr.second_expr.accept(self)
            self.__write(')')
        else:
            bool_expr.first_expr.accept(self)
        if bool_expr.rest is not None:
            self.__write(" " + bool_expr.bool_connector.lexeme + " ")
            bool_expr.rest.accept(self)
            self.__write(')')