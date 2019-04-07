# Author: Zach McKee
# Course: CPSC 326, Spring 2019
import mypl_error as error
import mypl_lexer as lexer
import mypl_token as token
import mypl_ast as ast

class Parser(object):

    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = None

    def parse(self):
        """succeeds if program is syntatically well-formed"""
        stmt_list_node = ast.StmtList()
        self.__advance()
        self.__stmts(stmt_list_node)
        self.__eat(token.EOS, 'expecting end of file')
        return stmt_list_node

    def __advance(self):
        self.current_token = self.lexer.next_token()

    def __eat(self, tokentype, error_msg):
        if self.current_token.tokentype == tokentype:
            self.__advance()
        else:
            self.__error(error_msg)

    def __error(self, error_msg):
        s = error_msg + ', found "' + self.current_token.lexeme + '" in parser'
        l = self.current_token.line
        c = self.current_token.column
        raise error.MyPLError(s, l, c)

    #Begin of recursive decent functions
    def __stmts(self,stmt_list_node):
        """<stmts> ::= <stmt> <stmts> | e"""
        if self.current_token.tokentype != token.EOS:
            stmt_list_node.stmts.append(self.__stmt())
            self.__stmts(stmt_list_node)

    def __stmt(self):
        """<stmt> ::= <sdecl> | <fdecl> | <bstmt>"""
        if self.current_token.tokentype == token.STRUCTTYPE:
            return self.__sdecl()
        elif self.current_token.tokentype == token.FUN:
            return self.__fdecl()
        else:
            return self.__bstmt()
    
    def __bstmts(self, stmt_list_node):
        """<bstmts> ::= <bstmt> <bstmts> | e"""
        #Tokens that can start a bstmt
        types = [token.VAR, token.SET, token.IF, token.WHILE, token.LPAREN]
        types.extend([token.STRINGVAL, token.INTVAL, token.BOOLVAL,token.RETURN])
        types.extend([token.FLOATVAL, token.NIL, token.NEW, token.ID])
        if self.current_token.tokentype in types:
            stmt_list_node.stmts.append(self.__bstmt())
            self.__bstmts(stmt_list_node)

    def __bstmt(self):
        """<bstmt> ::= <vdecl> | <assign> | <cond> | <while> | <expr> SEMICOLON | <exit>"""
        if self.current_token.tokentype == token.VAR:
            return self.__vdecl()
        elif self.current_token.tokentype == token.SET:
            return self.__assign()
        elif self.current_token.tokentype == token.IF:
            return self.__cond()
        elif self.current_token.tokentype == token.WHILE:
            return self.__while()
        elif self.current_token.tokentype == token.RETURN:
            return self.__exit()
        else:
            temp_expr_node = ast.ExprStmt()
            temp_expr_node.expr = self.__expr()
            self.__eat(token.SEMICOLON, 'expecting a ";"')
            return temp_expr_node

    def __sdecl(self):
        """<sdecl> ::= STRUCT ID <vdecls> END"""
        struct_decl_node = ast.StructDeclStmt()
        self.__eat(token.STRUCTTYPE, "expecting a struct")
        struct_decl_node.struct_id = self.current_token
        self.__eat(token.ID, "expecting an identifier")
        vDeclsList = []
        self.__vdecls(vDeclsList)
        struct_decl_node.var_decls = vDeclsList
        self.__eat(token.END, "expecting end")
        return struct_decl_node

    def __vdecls(self, var_decls_list):
        """<vdecls> ::= <vdecl> <vdecls> | e"""
        if self.current_token.tokentype == token.VAR:
            var_decls_list.append(self.__vdecl())
            self.__vdecls(var_decls_list)

    def __fdecl(self):
        """<fdecl> ::= FUN (<type>|NIL) ID LPAREN <params> RPAREN <bstmts> END"""
        fun_decl_node = ast.FunDeclStmt()
        self.__eat(token.FUN, "expecting fun keyword")
        if self.current_token.tokentype == token.NIL:
            fun_decl_node.return_type = self.current_token
            self.__advance()
        else:
            fun_decl_node.return_type = self.__type()
        fun_decl_node.fun_name = self.current_token
        self.__eat(token.ID, "expecting an identifier")
        self.__eat(token.LPAREN, 'expecting a "("')
        fun_decl_node.params = self.__params()
        self.__eat(token.RPAREN, 'expecting a ")"')
        stmt_list_node = ast.StmtList()
        self.__bstmts(stmt_list_node)
        fun_decl_node.stmt_list = stmt_list_node
        self.__eat(token.END, "expecting end")
        return fun_decl_node
                       
    def __params(self):
        """<params> ::= ID COLON <type> (COMMA ID COLON <type>)* | e"""
        paramsList = []
        if self.current_token.tokentype == token.ID:
            param_node = ast.FunParam()
            param_node.param_name = self.current_token
            self.__advance()
            self.__eat(token.COLON, 'expecting a ":"')
            param_node.param_type = self.__type()
            paramsList.append(param_node)
            while self.current_token.tokentype == token.COMMA:
                self.__advance()
                param_node = ast.FunParam()
                param_node.param_name = self.current_token
                self.__eat(token.ID, "expecting an identifier")
                self.__eat(token.COLON, 'expecting a ":"')
                param_node.param_type = self.__type()
                paramsList.append(param_node)
        return paramsList

    def __type(self):
        """<type> ::= ID | INTTYPE | FLOATTYPE | BOOLTYPE | STRINGTYPE"""
        types = [token.ID, token.INTTYPE, token.FLOATTYPE, token.BOOLTYPE]
        types.append(token.STRINGTYPE)
        if self.current_token.tokentype in types:
            temp_token = self.current_token
            self.__advance()
            return temp_token
        else:
            s = 'expected a type, found"' + self.current_token.lexeme + '" in parser'
            l = self.current_token.line
            c = self.current_token.column
            raise error.MyPLError(s, l, c)


    def __exit(self):
        """<exit> ::= RETURN (<expr> | e) SEMICOLON"""
        return_stmt_node = ast.ReturnStmt()
        return_stmt_node.return_token = self.current_token
        self.__eat(token.RETURN, 'expecting a "return" keyword')
        types = [token.LPAREN,token.STRINGVAL, token.INTVAL, token.BOOLVAL]
        types.extend([token.FLOATVAL, token.NIL, token.NEW, token.ID])
        if self.current_token.tokentype in types:
            return_stmt_node.return_expr = self.__expr()
        self.__eat(token.SEMICOLON, 'expecting a ";"')
        return return_stmt_node

    def __vdecl(self):
        """<vdecl> ::= VAR ID <tdecl> ASSIGN <expr> SEMICOLON"""
        var_decl_node = ast.VarDeclStmt()
        self.__eat(token.VAR, "expecting var keyword")
        var_decl_node.var_id = self.current_token
        self.__eat(token.ID, "expecting an identifier")
        var_decl_node.var_type = self.__tdecl()
        self.__eat(token.ASSIGN, 'expectring a "="')
        var_decl_node.var_expr = self.__expr()
        self.__eat(token.SEMICOLON, 'expecting a ";"')
        return var_decl_node

    def __tdecl(self):
        """<tdecl> ::= COLON <type> | e"""
        if self.current_token.tokentype == token.COLON:
            self.__advance()
            return self.__type()

    
    def __assign(self):
        """<assign> ::= SET <lvalue> ASSIGN <expr> SEMICOLON"""
        assign_node = ast.AssignStmt()
        self.__eat(token.SET, 'expecting a "set" keyword')
        assign_node.lhs = self.__lvalue()
        self.__eat(token.ASSIGN, 'expectring a "="')
        assign_node.rhs = self.__expr()
        self.__eat(token.SEMICOLON, "Expecting a semicolon")
        return assign_node

    def __lvalue(self):
        """<lvalue> ::= ID (DOT ID)*"""
        lvalue_node = ast.LValue()
        lvalue_node.path.append(self.current_token)
        self.__eat(token.ID, "expecting an identifier")
        while self.current_token.tokentype == token.DOT:
            self.__eat(token.DOT, 'expecting a "."')
            lvalue_node.path.append(self.current_token)
            self.__eat(token.ID, "expecting an identifier")
        return lvalue_node

    def __cond(self):
        """<cond> ::= IF <bexpr> THEN <bstmts> <condt> END"""
        if_node = ast.IfStmt()
        if_part_node = ast.BasicIf()
        self.__eat(token.IF, 'expecting an "if" keyword')
        if_part_node.bool_expr = self.__bexpr()
        self.__eat(token.THEN, 'expecting a "then" keyword')
        stmt_list_node = ast.StmtList()
        self.__bstmts(stmt_list_node)
        if_part_node.stmt_list = stmt_list_node
        if_node.if_part = if_part_node
        self.__condt(if_node)
        self.__eat(token.END, 'expecting an "end" keyword')
        return if_node

    def __condt(self, if_node):
        """<condt> ::= ELIF <bexpr> THEN <bstmts> <condt> | ELSE <bstmts> | e"""
        if self.current_token.tokentype == token.ELIF:
            self.__advance()
            if_part_node = ast.BasicIf()
            if_part_node.bool_expr = self.__bexpr()
            self.__eat(token.THEN, 'expecting a "then" keyword')
            stmt_list_node = ast.StmtList()
            self.__bstmts(stmt_list_node)
            if_part_node.stmt_list = stmt_list_node
            if_node.elseifs.append(if_part_node)
            self.__condt(if_node)
        elif self.current_token.tokentype == token.ELSE:
            self.__advance()
            if_node.has_else = True
            stmt_list_node = ast.StmtList()
            self.__bstmts(stmt_list_node)
            if_node.else_stmts = stmt_list_node

    def __while(self):
        """<while> ::= WHILE <bexpr> DO <bstmts> END"""
        while_stmt_node = ast.WhileStmt()
        self.__eat(token.WHILE, 'expecting a "while" keyword')
        while_stmt_node.bool_expr = self.__bexpr()
        self.__eat(token.DO, 'expecting a "do" keyword')
        stmt_list_node = ast.StmtList()
        self.__bstmts(stmt_list_node)
        while_stmt_node.stmt_list = stmt_list_node
        self.__eat(token.END, 'expecting an "end" keyword')
        return while_stmt_node

    def __expr(self):
        """<expr> ::= (<rvalue> | LPAREN <expr> RPAREN) (<mathrel> <expr> | e)"""
        temp_expr = ast.SimpleExpr()
        if self.current_token.tokentype == token.LPAREN:
            self.__advance()
            temp_expr = self.__expr()
            self.__eat(token.RPAREN, 'expecting a ")"')
        else:
            temp_expr.term = self.__rvalue()
        types = [token.PLUS, token.MINUS, token.DIVIDE, token.MULTIPLY]
        types.append(token.MODULO)
        if self.current_token.tokentype in types:
            comp_expr_node = ast.ComplexExpr()
            comp_expr_node.first_operand = temp_expr
            comp_expr_node.math_rel = self.__mathrel()
            comp_expr_node.rest = self.__expr()
            return comp_expr_node
        else:
            return temp_expr
        

    def __mathrel(self):
        """<mathrel> ::= PLUS | MINUS | DIVIDE | MULTIPLY | MODULO"""
        types = [token.PLUS, token.MINUS, token.DIVIDE, token.MULTIPLY, token.MODULO]
        if self.current_token.tokentype in types:
            temp_token = self.current_token
            self.__advance()
            return temp_token
        else:
            s = 'expected a math operator, found "' + self.current_token.lexeme + '" in parser'
            l = self.current_token.line
            c = self.current_token.column
            raise error.MyPLError(s, l, c)

    def __rvalue(self):
        """<rvalue> ::= STRINGVAL | INTVAL | BOOLVAL | FLOATVAL | NIL | NEW ID | <idrval>"""
        types = [token.STRINGVAL, token.INTVAL, token.BOOLVAL]
        types.extend([token.FLOATVAL, token.NIL])
        if self.current_token.tokentype == token.NEW:
            new_r_value_node = ast.NewRValue()
            self.__advance()
            new_r_value_node.struct_type = self.current_token
            self.__eat(token.ID, "expecting an identifier")
            return new_r_value_node
        elif self.current_token.tokentype == token.ID:
            return self.__idrval()
        elif self.current_token.tokentype in types:
            simple_rvalue_node = ast.SimpleRValue()
            simple_rvalue_node.val = self.current_token
            self.__advance()
            return simple_rvalue_node
        else:
            s = 'expected a rvalue found"' + self.current_token.lexeme + '" in parser'
            l = self.current_token.line
            c = self.current_token.column
            raise error.MyPLError(s, l, c)

    def __idrval(self):
        """<idrval> ::= ID (DOT ID)* | ID LPAREN <exprlist> RPAREN"""
        idr_value_node = ast.IDRvalue()
        idr_value_node.path.append(self.current_token)
        self.__eat(token.ID, "expecting an identifier")
        if self.current_token.tokentype == token.LPAREN:
            call_rvalue_node = ast.CallRValue()
            call_rvalue_node.fun = idr_value_node.path[0]
            self.__advance()
            call_rvalue_node.args = self.__exprlist()
            self.__eat(token.RPAREN, 'expecting a ")"')
            return call_rvalue_node
        else:
            while self.current_token.tokentype == token.DOT:
                self.__advance()
                idr_value_node.path.append(self.current_token)
                self.__eat(token.ID, "expecting an identifier")
        return idr_value_node

    def __exprlist(self):
        """<exprlist> ::= <expr> (COMMA <expr>)* | e"""
        types = [token.LPAREN,token.STRINGVAL, token.INTVAL, token.BOOLVAL]
        types.extend([token.FLOATVAL, token.NIL, token.NEW, token.ID])
        exprs = []
        if self.current_token.tokentype in types:
            exprs.append(self.__expr())
            while self.current_token.tokentype == token.COMMA:
                self.__advance()
                exprs.append(self.__expr())
        return exprs

    def __bexpr(self):
        """<bexpt> ::= <expr> <bexprt> | NOT <bexpr> <bexprt> |"""
        """            LPAREN <bexpr> RPAREN <bconnct>"""
        bool_expr_node = ast.BoolExpr()
        if self.current_token.tokentype == token.LPAREN:
            self.__advance()
            bool_expr_node.first_expr = self.__bexpr()
            self.__eat(token.RPAREN, 'expecting a ")"')
            self.__bconnct(bool_expr_node)
        elif self.current_token.tokentype == token.NOT:
            self.__advance()
            bool_expr_node.first_expr = self.__bexpr()
            bool_expr_node.negated = True
            self.__bexprt(bool_expr_node)
        else:
            bool_expr_node.first_expr = self.__expr()
            self.__bexprt(bool_expr_node)
        return bool_expr_node

    def __bexprt(self, bool_expr_node):
        """<bexprt> ::= <boolrel> <expr> <bconnct> | <bconnct>"""
        types = [token.EQUAL, token.LESS_THAN, token.LESS_THAN_EQUAL]
        types.extend([token.GREATER_THAN_EQUAL, token.GREATER_THAN])
        types.append(token.NOT_EQUAL)
        if self.current_token.tokentype in types:
            bool_expr_node.bool_rel = self.__boolrel()
            bool_expr_node.second_expr = self.__expr()
            self.__bconnct(bool_expr_node)
        else:
            self.__bconnct(bool_expr_node)

    def __bconnct(self, bool_expr_node):
        """<bconnct> ::= AND <bexpr> | OR <bexpr> | e"""
        if self.current_token.tokentype == token.AND or self.current_token.tokentype == token.OR:
            bool_expr_node.bool_connector = self.current_token
            self.__advance()
            bool_expr_node.rest = self.__bexpr()

    def __boolrel(self):
        """<boolrel> ::= EQUAL | LESS_THAN | GREATER_THAN | LESS_THAN_EQUAL |"""
        """              GREATER_THAN_EQUAL | NOT_EQUAL"""
        types = [token.EQUAL, token.LESS_THAN, token.LESS_THAN_EQUAL]
        types.extend([token.GREATER_THAN_EQUAL, token.GREATER_THAN])
        types.append(token.NOT_EQUAL)
        if self.current_token.tokentype in types:
            temp_token = self.current_token
            self.__advance()
            return temp_token
        else:
            s = 'expected a conditional operator, found "' + self.current_token.lexeme + '" in parser'
            l = self.current_token.line
            c = self.current_token.column
            raise error.MyPLError(s, l, c)