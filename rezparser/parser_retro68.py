import ply.yacc

from . import lexer
from . import parser


# noinspection PyMethodMayBeStatic, PyPep8Naming
class RezParserRetro68(object):
	"""(Not fully functional) Rez parser, using rules based on the Retro68 Rez tool's Yacc source:
	https://github.com/autc04/Retro68/blob/master/Rez/RezParser.yy
	"""
	
	tokens = lexer.RezLexer.tokens
	
	start = "rez"
	
	def p_error(self, p):
		raise parser.ParseError(p)
	
	def p_empty(self, p):
		"""empty : """
		
		p[0] = []
		return p
	
	def p_rez(self, p):
		"""rez : empty
		| rez type_definition SEMICOLON
		| rez resource SEMICOLON
		| rez data SEMICOLON
		"""
		
		p[0] = p[1] + p[2:-1]
		return p
	
	def p_type_definition(self, p):
		"""type_definition : TYPE type_spec LBRACE field_definitions RBRACE
		| TYPE type_spec AS type_spec
		"""
		
		p[0] = p[2], p[4]
		return p
	
	def p_res_type(self, p):
		"""res_type : INTLIT"""
		
		p[0] = p[1]
		return p
	
	def p_type_spec(self, p):
		"""type_spec : res_type
		| res_type LPAREN INTLIT RPAREN
		"""
		
		p[0] = p[1], (None if len(p) <= 3 else p[3])
		return p
	
	def p_field_definitions(self, p):
		"""field_definitions : empty
		| field_definitions IDENTIFIER COLON
		| field_definitions SEMICOLON
		| field_definitions field_definition SEMICOLON
		"""
		
		p[0] = p[1] + p[2:-1]
		return p
	
	def p_field_definition(self, p):
		"""field_definition : simple_field_definition
		| array_definition
		| switch_definition
		| fill_statement
		| align_statement
		"""
		
		p[0] = p[1]
		return p
	
	def p_simple_field_definition(self, p):
		"""simple_field_definition : field_attributes simpletype array_count_opt value_spec_opt
		| simple_field_definition IDENTIFIER
		| simple_field_definition IDENTIFIER ASSIGN value
		| simple_field_definition COMMA IDENTIFIER
		| simple_field_definition COMMA IDENTIFIER ASSIGN value
		"""
		
		p[0] = p[1:]
		return p
	
	def p_value_spec_opt(self, p):
		"""value_spec_opt : empty
		| ASSIGN value
		"""
		
		p[0] = p[1:]
		return p
	
	def p_simpletype(self, p):
		"""simpletype : BOOLEAN
		| BYTE
		| INTEGER
		| LONGINT
		| RECT
		| POINT
		| CHAR
		| PSTRING
		| WSTRING
		| STRING
		| BITSTRING
		"""
		
		p[0] = p[1]
		return p
	
	def p_fill_statement(self, p):
		"""fill_statement : FILL fill_unit array_count_opt"""
		
		p[0] = p[1:]
		return p
	
	def p_align_statement(self, p):
		"""align_statement : ALIGN fill_unit"""
		
		p[0] = p[1:]
		return p
	
	def p_fill_unit(self, p):
		"""fill_unit : BIT
		| NIBBLE
		| BYTE
		| WORD
		| LONG
		"""
		
		p[0] = p[1]
		return p
	
	def p_array_definition(self, p):
		"""array_definition : array_attributes ARRAY array_name_opt array_count_opt LBRACE field_definitions RBRACE"""
		
		p[0] = p[1:]
		return p
	
	def p_array_count(self, p):
		"""array_count : LBRACKET expression RBRACKET"""
		
		p[0] = p[2]
		return p
	
	def p_array_count_opt(self, p):
		"""array_count_opt : empty
		| array_count
		"""
		
		p[0] = p[1]
		return p
	
	def p_array_name_opt(self, p):
		"""array_name_opt : empty
		| IDENTIFIER
		"""
		
		p[0] = p[1]
		return p
	
	def p_array_attributes(self, p):
		"""array_attributes : empty
		| WIDE
		"""
		
		p[0] = p[1]
		return p
	
	def p_field_attributes(self, p):
		"""field_attributes : empty
		| field_attributes field_attribute
		"""
		
		p[0] = p[1] + p[2:]
		return p
	
	def p_field_attribute(self, p):
		"""field_attribute : HEX
		| DECIMAL
		| OCTAL
		| BINARY
		| KEY
		| UNSIGNED
		| LITERAL
		"""
		
		p[0] = p[1]
		return p
	
	def p_switch_definition(self, p):
		"""switch_definition : SWITCH LBRACE switch_cases RBRACE"""
		
		p[0] = p[1:]
		return p
	
	def p_switch_cases(self, p):
		"""switch_cases : empty
		| switch_cases switch_case
		"""
		
		p[0] = p[1] + p[2:]
		return p
	
	def p_switch_case(self, p):
		"""switch_case : CASE IDENTIFIER COLON"""
		
		p[0] = p[1:]
		return p
	
	def p_value(self, p):
		"""value : expression
		| LBRACE resource_body RBRACE
		| string_expression
		"""
		
		p[0] = p[1:]
		return p
	
	def p_expression(self, p):
		"""expression : expression1
		| expression BITXOR expression1
		"""
		
		p[0] = p[1:]
		return p
	
	def p_expression1(self, p):
		"""expression1 : expression2
		| expression1 BITAND expression2
		"""
		
		p[0] = p[1:]
		return p
	
	def p_expression2(self, p):
		"""expression2 : expression3
		| expression2 BITOR expression3
		"""
		
		p[0] = p[1:]
		return p
	
	def p_expression3(self, p):
		"""expression3 : expression4
		| expression3 EQUAL expression4
		| expression3 NOTEQUAL expression4
		"""
		
		p[0] = p[1:]
		return p
	
	def p_expression4(self, p):
		"""expression4 : expression5
		| expression4 SHIFTLEFT expression5
		| expression4 SHIFTRIGHT expression5
		"""
		
		p[0] = p[1:]
		return p
	
	def p_expression5(self, p):
		"""expression5 : expression6
		| expression5 PLUS expression6
		| expression5 MINUS expression6
		"""
		
		p[0] = p[1:]
		return p
	
	def p_expression6(self, p):
		"""expression6 : expression7
		| expression6 MULTIPLY expression7
		| expression6 DIVIDE expression7
		"""
		
		p[0] = p[1:]
		return p
	
	def p_expression7(self, p):
		"""expression7 : expression8
		| MINUS expression7
		| PLUS expression7
		| BITCOMPL expression7
		"""
		
		p[0] = p[1:]
		return p
	
	def p_expression8(self, p):
		"""expression8 : INTLIT
		| identifier_expression
		| LPAREN expression RPAREN
		| FUN_COUNTOF LPAREN identifier_expression RPAREN
		| FUN_ARRAYINDEX LPAREN identifier_expression RPAREN
		| FUN_BITFIELD LPAREN expression COMMA expression COMMA expression RPAREN
		| FUN_WORD LPAREN expression RPAREN
		| FUN_BYTE LPAREN expression RPAREN
		| FUN_LONG LPAREN expression RPAREN
		"""
		
		p[0] = p[1:]
		return p
	
	def p_identifier_expression(self, p):
		"""identifier_expression : IDENTIFIER
		| IDENTIFIER LBRACKET function_argument_list1 RBRACKET
		"""
		
		p[0] = p[1:]
		return p
	
	def p_function_argument_list(self, p):
		"""function_argument_list : empty
		| function_argument_list1
		"""
		
		p[0] = p[1]
		return p
	
	def p_function_argument_list1(self, p):
		"""function_argument_list1 : expression
		| function_argument_list COMMA expression
		"""
		
		p[0] = p[1:]
		return p
	
	def p_string_expression(self, p):
		"""string_expression : string_expression1
		| string_expression string_expression1
		"""
		
		p[0] = p[1:]
		return p
	
	def p_string_expression1(self, p):
		"""string_expression1 : STRINGLIT
		| FUN_READ LPAREN string_expression RPAREN
		"""
		
		p[0] = p[1:]
		return p
	
	def p_resource(self, p):
		"""resource : RESOURCE res_spec LBRACE resource_body RBRACE"""
		
		p[0] = p[1:]
		return p
	
	def p_res_spec(self, p):
		"""res_spec : res_type LPAREN expression resource_name_opt resource_attributes RPAREN"""
		
		p[0] = p[1:]
		return p
	
	def p_resource_name_opt(self, p):
		"""resource_name_opt : empty
		| COMMA string_expression
		"""
		
		p[0] = p[1:]
		return p
	
	def p_resource_attributes(self, p):
		"""resource_attributes : expression
		| resource_attributes_named
		"""
		
		p[0] = p[1]
		return p
	
	def p_resource_attributes_named(self, p):
		"""resource_attributes_named : empty
		| resource_attributes_named resource_attribute_named
		"""
		
		p[0] = p[1] + p[2:]
		return p
	
	def p_resource_attribute_named(self, p):
		"""resource_attribute_named : COMPRESSED
		| UNCOMPRESSED
		| CHANGED
		| UNCHANGED
		| PRELOAD
		| NONPRELOAD
		| LOCKED
		| UNLOCKED
		| PURGEABLE
		| NONPURGEABLE
		| SYSHEAP
		| APPHEAP
		"""
		
		p[0] = p[1]
		return p
	
	def p_resource_body(self, p):
		"""resource_body : empty
		| SEMICOLON
		| resource_body1
		| resource_body1 SEMICOLON
		"""
		
		p[0] = p[1]
		return p
	
	def p_resource_body1(self, p):
		"""resource_body1 : resource_item
		| resource_body1 COMMA resource_item
		| resource_body1 COMMA
		"""
		
		p[0] = p[1:]
		return p
	
	def p_resource_item(self, p):
		"""resource_item : value
		| IDENTIFIER LBRACE resource_body RBRACE
		"""
		
		p[0] = p[1:]
		return p
	
	def p_data(self, p):
		"""data : DATA res_spec LBRACE string_expression RBRACE
		| DATA res_spec LBRACE string_expression SEMICOLON RBRACE
		"""
		
		p[0] = p[1:]
		return p
	
	def p_STRINGLIT(self, p):
		"""STRINGLIT : STRINGLIT_TEXT
		| STRINGLIT_HEX
		"""
		
		p[0] = p[1]
		return p
	
	def p_INTLIT(self, p):
		"""INTLIT : INTLIT_DEC
		| INTLIT_HEX
		| INTLIT_OCT
		| INTLIT_BIN
		| INTLIT_CHAR
		"""
		
		p[0] = p[1]
		return p
	
	def __init__(self, lexer=None, **kwargs):
		super().__init__()
		
		self.lexer = lexer.RezLexer().lexer if lexer is None else lexer
		self.parser = ply.yacc.yacc(module=self, tabmodule="_table_parser_retro68", debugfile="_debug_parser_retro68.out", **kwargs)
	
	def parse(self, inp, **kwargs):
		return self.parser.parse(inp, self.lexer, **kwargs)