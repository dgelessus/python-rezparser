import ply.yacc

from . import common
from . import lexer
from . import preprocessor

__all__ = [
	"ParseError",
	"NoOpLexer",
	"RezParser",
]

class ParseError(common.RezParserError):
	__slots__ = ()


class NoOpLexer(object):
	@property
	def lineno(self):
		return self.lexer.lineno
	
	@lineno.setter
	def lineno(self, lineno):
		self.lexer.lineno = lineno
	
	@property
	def lexpos(self):
		return self.lexer.lexpos
	
	@lexpos.setter
	def lexpos(self, lexpos):
		self.lexer.lexpos = lexpos
	
	def __init__(self, lexer=None):
		super().__init__()
		
		self.lexer = lexer
		self.tokens = []
	
	def __iter__(self):
		return iter(self.token, None)
	
	def input(self, inp):
		if isinstance(inp, str):
			self.lexer.input(inp)
		else:
			self.tokens = list(inp)
	
	def token(self):
		try:
			return self.tokens.pop(0)
		except IndexError:
			return self.lexer.token()


# noinspection PyMethodMayBeStatic, PyPep8Naming
class RezParser(object):
	"""Rez preprocessor and parser, based on the description and syntax given in Appendix C, "The Rez Language", in "Building and Managing Programs in MPW, 2nd Edition".
	This file can for example be found on Max1zzz's server "www.max1zzz.co.uk", at location "/%2BMac OS Classic/Programming/Macintosh Programmers Workshop/MPW (2001)/Documentation/MPW_Reference/Building_Progs_in_MPW.sit".
	The server can be accessed via a web interface ("http://www.max1zzz.co.uk:8000", username "mg", password "mg"), or via FTP ("ftp://www.max1zzz.co.uk:21", username "mg", password "mg"), or via one of the other methods listed at "http://max1zzz.co.uk/servers.html".
	"""
	
	tokens = lexer.RezLexer.tokens
	
	start = "Start symbol must be set manually"
	
	def p_error(self, p):
		raise ParseError(p)
	
	def p_empty(self, p):
		"""empty : """
		
		p[0] = []
		return p
	
	def p_comma_opt(self, p):
		"""comma_opt : empty
		| COMMA
		"""
		
		p[0] = p[1]
		return p
	
	def p_semicolon_opt(self, p):
		"""semicolon_opt : empty
		| SEMICOLON
		"""
		
		p[0] = p[1]
		return p
	
	def p_intlit(self, p):
		"""intlit : INTLIT_DEC
		| INTLIT_HEX
		| INTLIT_OCT
		| INTLIT_BIN
		| INTLIT_CHAR
		"""
		
		p[0] = p[1]
		return p
	
	def p_resource_attribute(self, p):
		"""resource_attribute : COMPRESSED
		| UNCOMPRESSED
		| CHANGED
		| UNCHANGED
		| PRELOAD
		| NONPRELOAD
		| PROTECTED
		| UNPROTECTED
		| LOCKED
		| UNLOCKED
		| PURGEABLE
		| NONPURGEABLE
		| SYSHEAP
		| APPHEAP
		"""
		
		p[0] = p[1]
		return p
	
	def p_int_function_call(self, p):
		"""int_function_call : FUN_ARRAYINDEX LPAREN IDENTIFIER comma_opt RPAREN
		| FUN_ATTRIBUTES
		| FUN_BITFIELD LPAREN expression COMMA expression COMMA expression comma_opt RPAREN
		| FUN_BYTE LPAREN expression comma_opt RPAREN
		| FUN_COUNTOF LPAREN IDENTIFIER comma_opt RPAREN
		| FUN_DAY
		| FUN_HOUR
		| FUN_ID
		| FUN_LONG LPAREN expression comma_opt RPAREN
		| FUN_MINUTE
		| FUN_MONTH
		| FUN_PACKEDSIZE LPAREN expression COMMA expression COMMA expression comma_opt RPAREN
		| FUN_RESOURCESIZE
		| FUN_SECOND
		| FUN_TYPE
		| FUN_WEEKDAY
		| FUN_WORD LPAREN expression comma_opt RPAREN
		| FUN_YEAR
		"""
		
		p[0] = p[1:]
		return p
	
	def p_label_subscript_indices(self, p):
		"""label_subscript_indices : expression
		| label_subscript_indices COMMA expression
		"""
		
		p[0] = [p[1]] if len(p) == 2 else p[1] + p[3:]
		return p
	
	def p_expression_simple(self, p):
		"""expression_simple : intlit
		| resource_attribute
		| int_function_call
		| IDENTIFIER
		| IDENTIFIER LBRACKET label_subscript_indices RBRACKET
		| LPAREN expression RPAREN
		"""
		
		p[0] = p[2] if len(p) > 2 else p[1]
		return p
	
	def p_expression_unaryop(self, p):
		"""expression_unaryop : expression_simple
		| MINUS expression_unaryop
		| BOOLNOT expression_unaryop
		| BITNOT expression_unaryop
		"""
		
		p[0] = p[1:] if len(p) > 2 else p[1]
		return p
	
	def p_expression_muldiv(self, p):
		"""expression_muldiv : expression_unaryop
		| expression_muldiv MULTIPLY expression_unaryop
		| expression_muldiv DIVIDE expression_unaryop
		| expression_muldiv MODULO expression_unaryop
		"""
		
		p[0] = p[1:] if len(p) > 2 else p[1]
		return p
	
	def p_expression_plusminus(self, p):
		"""expression_plusminus : expression_muldiv
		| expression_plusminus PLUS expression_muldiv
		| expression_plusminus MINUS expression_muldiv
		"""
		
		p[0] = p[1:] if len(p) > 2 else p[1]
		return p
	
	def p_expression_bitshift(self, p):
		"""expression_bitshift : expression_plusminus
		| expression_bitshift SHIFTLEFT expression_plusminus
		| expression_bitshift SHIFTRIGHT expression_plusminus
		"""
		
		p[0] = p[1:] if len(p) > 2 else p[1]
		return p
	
	def p_expression_relational(self, p):
		"""expression_relational : expression_bitshift
		| expression_relational LESS expression_bitshift
		| expression_relational GREATER expression_bitshift
		| expression_relational LESSEQUAL expression_bitshift
		| expression_relational GREATEREQUAL expression_bitshift
		"""
		
		p[0] = p[1:] if len(p) > 2 else p[1]
		return p
	
	def p_expression_equal(self, p):
		"""expression_equal : expression_relational
		| expression_equal EQUAL expression_relational
		| expression_equal NOTEQUAL expression_relational
		"""
		
		p[0] = p[1:] if len(p) > 2 else p[1]
		return p
	
	def p_expression_bitand(self, p):
		"""expression_bitand : expression_equal
		| expression_bitand BITAND expression_equal
		"""
		
		p[0] = p[1:] if len(p) > 2 else p[1]
		return p
	
	def p_expression_bitxor(self, p):
		"""expression_bitxor : expression_bitand
		| expression_bitxor BITXOR expression_bitand
		"""
		
		p[0] = p[1:] if len(p) > 2 else p[1]
		return p
	
	def p_expression_bitor(self, p):
		"""expression_bitor : expression_bitxor
		| expression_bitor BITOR expression_bitxor
		"""
		
		p[0] = p[1:] if len(p) > 2 else p[1]
		return p
	
	def p_expression_booland(self, p):
		"""expression_booland : expression_bitor
		| expression_booland BOOLAND expression_bitor
		"""
		
		p[0] = p[1:] if len(p) > 2 else p[1]
		return p
	
	def p_expression_boolor(self, p):
		"""expression_boolor : expression_booland
		| expression_boolor BOOLOR expression_booland
		"""
		
		p[0] = p[1:] if len(p) > 2 else p[1]
		return p
	
	def p_expression(self, p):
		"""expression : expression_boolor"""
		
		p[0] = p[1]
		return p
	
	def p_varargs_part(self, p):
		"""varargs_part : empty
		| varargs_part COMMA expression
		| varargs_part COMMA string_expression
		"""
		
		p[0] = p[1] + p[2:]
		return p
	
	def p_varargs_opt(self, p):
		"""varargs_opt : varargs_part comma_opt"""
		
		p[0] = p[1] + p[2]
		return p
	
	def p_string_function_call(self, p):
		"""string_function_call : FUN_DATE
		| FUN_FORMAT LPAREN string_expression varargs_opt RPAREN
		| FUN_NAME
		| FUN_READ LPAREN string_expression comma_opt RPAREN
		| FUN_RESOURCE LPAREN string_expression COMMA expression COMMA expression COMMA string_expression comma_opt RPAREN
		| FUN_SHELL LPAREN string_expression comma_opt RPAREN
		| FUN_TIME
		| FUN_VERSION
		"""
		
		p[0] = p[1:]
		return p
	
	def p_single_string(self, p):
		"""single_string : STRINGLIT_TEXT
		| STRINGLIT_HEX
		| string_function_call
		"""
		
		p[0] = p[1]
		return p
	
	def p_string_expression(self, p):
		"""string_expression : empty single_string
		| string_expression single_string
		"""
		
		p[0] = p[1] + p[2:]
		return p
	
	def p_string_expression_opt(self, p):
		"""string_expression_opt : empty
		| string_expression
		"""
		
		p[0] = p[1]
		return p
	
	def p_resource_name_opt(self, p):
		"""resource_name_opt : empty
		| COMMA string_expression
		"""
		
		p[0] = p[1:]
		return p
	
	def p_resource_attributes_named(self, p):
		"""resource_attributes_named : resource_attribute
		| resource_attributes_named COMMA resource_attribute
		"""
		
		p[0] = [p[1]] if len(p) == 2 else p[1] + p[3:]
		return p
	
	def p_resource_attributes(self, p):
		"""resource_attributes : resource_attributes_named
		| expression
		"""
		
		p[0] = p[1]
		return p
	
	def p_resource_attributes_opt(self, p):
		"""resource_attributes_opt : empty
		| COMMA resource_attributes
		"""
		
		p[0] = p[1:]
		return p
	
	def p_resource_spec_typedef(self, p):
		"""resource_spec_typedef : expression
		| expression LPAREN expression RPAREN
		| expression LPAREN expression COLON expression RPAREN
		"""
		
		p[0] = p[1:]
		return p
	
	def p_resource_spec_def(self, p):
		"""resource_spec_def : expression LPAREN expression resource_name_opt resource_attributes_opt RPAREN"""
		
		p[0] = p[1:]
		return p
	
	def p_resource_spec_use(self, p):
		"""resource_spec_use : expression
		| expression LPAREN expression RPAREN
		| expression LPAREN expression COLON expression RPAREN
		| expression LPAREN string_expression RPAREN
		"""
		
		p[0] = p[1:]
		return p
	
	def p_change_statement(self, p):
		"""change_statement : CHANGE resource_spec_use TO resource_spec_def SEMICOLON"""
		
		p[0] = p[1:]
		return p
	
	def p_data_statement(self, p):
		"""data_statement : DATA resource_spec_def LBRACE string_expression_opt semicolon_opt RBRACE SEMICOLON"""
		
		p[0] = p[1:]
		return p
	
	def p_delete_statement(self, p):
		"""delete_statement : DELETE resource_spec_use SEMICOLON"""
		
		p[0] = p[1:]
		return p
	
	def p_enum_constant(self, p):
		"""enum_constant : IDENTIFIER
		| IDENTIFIER ASSIGN expression
		"""
		
		p[0] = p[1:]
		return p
	
	def p_enum_constants(self, p):
		"""enum_constants : empty enum_constant
		| enum_constants COMMA enum_constant
		"""
		
		p[0] = p[1] + p[2:]
		return p
	
	def p_enum_body(self, p):
		"""enum_body : empty
		| enum_constants comma_opt
		"""
		
		p[0] = p[1]
		return p
	
	def p_enum_statement(self, p):
		"""enum_statement : ENUM LBRACE enum_body RBRACE SEMICOLON
		| ENUM IDENTIFIER LBRACE enum_body RBRACE SEMICOLON
		"""
		
		p[0] = p[1:]
		return p
	
	def p_include_statement(self, p):
		"""include_statement : INCLUDE string_expression SEMICOLON
		| INCLUDE string_expression resource_spec_use SEMICOLON
		| INCLUDE string_expression NOT expression SEMICOLON
		| INCLUDE string_expression expression AS expression SEMICOLON
		| INCLUDE string_expression resource_spec_use AS resource_spec_def SEMICOLON
		"""
		
		p[0] = p[1:]
		return p
	
	def p_read_statement(self, p):
		"""read_statement : READ resource_spec_def string_expression SEMICOLON"""
		
		p[0] = p[1:]
		return p
	
	def p_resource_value(self, p):
		"""resource_value : IDENTIFIER
		| expression
		| string_expression
		| LBRACE array_values RBRACE
		| IDENTIFIER LBRACE resource_values semicolon_opt RBRACE
		"""
		
		p[0] = p[1:]
		return p
	
	def p_resource_values_part(self, p):
		"""resource_values_part : empty resource_value
		| resource_values_part COMMA resource_value
		"""
		
		p[0] = p[1] + p[2:]
		return p
	
	def p_resource_values(self, p):
		"""resource_values : empty
		| resource_values_part comma_opt
		"""
		
		p[0] = p[1]
		return p
	
	def p_array_values_part(self, p):
		"""array_values_part : empty resource_values
		| array_values_part SEMICOLON resource_values
		"""
		
		p[0] = p[1] + p[2:]
		return p
	
	def p_array_values(self, p):
		"""array_values : empty
		| array_values_part semicolon_opt
		"""
		
		p[0] = p[1:]
		return p
	
	def p_resource_statement(self, p):
		"""resource_statement : RESOURCE resource_spec_def LBRACE resource_values semicolon_opt RBRACE SEMICOLON"""
		
		p[0] = p[1:]
		return p
	
	def p_simple_field_modifier(self, p):
		"""simple_field_modifier : KEY
		| UNSIGNED
		| BINARY
		| OCTAL
		| DECIMAL
		| HEX
		| LITERAL
		"""
		
		p[0] = p[1]
		return p
	
	def p_simple_field_modifiers_opt(self, p):
		"""simple_field_modifiers_opt : empty
		| simple_field_modifiers_opt simple_field_modifier
		"""
		
		p[0] = p[1] + p[2:]
		return p
	
	def p_numeric_type(self, p):
		"""numeric_type : BITSTRING LBRACKET expression RBRACKET
		| BYTE
		| INTEGER
		| LONGINT
		"""
		
		p[0] = p[1:]
		return p
	
	def p_string_type_name(self, p):
		"""string_type_name : STRING
		| CSTRING
		| PSTRING
		| WSTRING
		"""
		
		p[0] = p[1:]
		return p
	
	def p_string_type(self, p):
		"""string_type : string_type_name
		| string_type_name LBRACKET expression RBRACKET
		"""
		
		p[0] = p[1:]
		return p
	
	def p_simple_type(self, p):
		"""simple_type : BOOLEAN
		| numeric_type
		| CHAR
		| string_type
		| POINT
		| RECT
		"""
		
		p[0] = p[1]
		return p
	
	def p_symbolic_constant(self, p):
		"""symbolic_constant : IDENTIFIER
		| IDENTIFIER ASSIGN resource_value
		"""
		
		p[0] = p[1:]
		return p
	
	def p_symbolic_constants_part(self, p):
		"""symbolic_constants_part : empty symbolic_constant
		| symbolic_constants_part COMMA symbolic_constant
		"""
		
		p[0] = p[1] + p[3:]
		return p
	
	def p_symbolic_constants(self, p):
		"""symbolic_constants : symbolic_constants_part comma_opt"""
		
		p[0] = p[1]
		return p
	
	def p_simple_field(self, p):
		"""simple_field : simple_type SEMICOLON
		| simple_type symbolic_constants SEMICOLON
		| simple_type ASSIGN resource_value SEMICOLON
		"""
		
		p[0] = p[1:]
		return p
	
	def p_fill_field_size(self, p):
		"""fill_field_size : BIT
		| NIBBLE
		| BYTE
		| WORD
		| LONG
		"""
		
		p[0] = p[1]
		return p
	
	def p_fill_field(self, p):
		"""fill_field : FILL fill_field_size SEMICOLON
		| FILL fill_field_size LBRACKET expression RBRACKET SEMICOLON
		"""
		
		p[0] = p[1:]
		return p
	
	def p_align_field_size(self, p):
		"""align_field_size : NIBBLE
		| BYTE
		| WORD
		| LONG
		"""
		
		p[0] = p[1]
		return p
	
	def p_align_field(self, p):
		"""align_field : ALIGN align_field_size SEMICOLON"""
		
		p[0] = p[1:]
		return p
	
	def p_array_modifier(self, p):
		"""array_modifier : WIDE"""
		
		p[0] = p[1]
		return p
	
	def p_array_modifiers_opt(self, p):
		"""array_modifiers_opt : empty
		| array_modifiers_opt array_modifier
		"""
		
		p[0] = p[1] + p[2:]
		return p
	
	def p_array_field(self, p):
		"""array_field : array_modifiers_opt ARRAY LBRACE fields RBRACE SEMICOLON
		| array_modifiers_opt ARRAY IDENTIFIER LBRACE fields RBRACE SEMICOLON
		"""
		
		p[0] = p[1:]
		return p
	
	def p_switch_field_case(self, p):
		"""switch_field_case : CASE IDENTIFIER COLON fields"""
		
		p[0] = p[1:]
		return p
	
	def p_switch_field_cases(self, p):
		"""switch_field_cases : empty
		| switch_field_cases switch_field_case
		"""
		
		p[0] = p[1] + p[2:]
		return p
	
	def p_switch_field(self, p):
		"""switch_field : SWITCH LBRACE switch_field_cases RBRACE SEMICOLON"""
		
		p[0] = p[1:]
		return p
	
	def p_field(self, p):
		"""field : IDENTIFIER COLON
		| simple_field_modifiers_opt simple_field
		| fill_field
		| align_field
		| array_field
		| switch_field
		"""
		
		p[0] = p[1:]
		return p
	
	def p_fields(self, p):
		"""fields : empty
		| fields field
		"""
		
		p[0] = p[1] + p[2:]
		return p
	
	def p_type_statement(self, p):
		"""type_statement : TYPE resource_spec_typedef LBRACE fields RBRACE SEMICOLON
		| TYPE resource_spec_typedef AS expression SEMICOLON
		| TYPE resource_spec_typedef AS expression LPAREN expression RPAREN SEMICOLON
		"""
		
		p[0] = p[1:]
		return p
	
	def p_statement(self, p):
		"""statement : SEMICOLON
		| change_statement
		| data_statement
		| delete_statement
		| enum_statement
		| include_statement
		| read_statement
		| resource_statement
		| type_statement
		"""
		
		p[0] = p[1]
		return p
	
	def p_start_file(self, p):
		"""start_file : empty
		| start_file statement
		"""
		
		p[0] = p[1] + p[2:]
		return p
	
	def p_start_expr(self, p):
		"""start_expr : expression"""
		
		p[0] = p[1]
		return p
	
	def __init__(self, lexer=None, preprocess=True, **kwargs):
		super().__init__()
		
		if lexer is None:
			lexer = lexer.RezLexer()
		
		lexer = self.manual_lexer = NoOpLexer(lexer)
		
		if preprocess:
			lexer = preprocessor.RezPreprocessor(lexer, parser=self)
		
		self.lexer = lexer
		self.parser_file = ply.yacc.yacc(module=self, start="start_file", tabmodule="_table_parser_file", debugfile="_debug_parser_file.out", **kwargs)
		self.parser_expr = ply.yacc.yacc(module=self, start="start_expr", tabmodule="_table_parser_expr", debugfile="_debug_parser_expr.out", **kwargs)
		self.parser_file.parse("", self.lexer)
		self.parser_expr.parse("0", self.lexer)
	
	def parse_file(self, inp, **kwargs):
		self.parser_file.restart()
		return self.parser_file.parse(inp, self.lexer, **kwargs)
	
	def parse_expr(self, inp, **kwargs):
		self.parser_expr.restart()
		return self.parser_expr.parse(inp, self.lexer, **kwargs)
