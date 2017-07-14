import ply.yacc

from . import common
from . import lexer
from . import ast

__all__ = [
	"ParseError",
	"RezParser",
]


class ParseError(common.RezParserError):
	__slots__ = ()


def _unescape_string(s):
	ret = bytearray()
	lastpos = 0
	pos = s.find("\\")
	while pos != -1:
		ret.extend(s[lastpos:pos].encode(common.STRING_ENCODING))
		
		if pos+1 >= len(s):
			raise ValueError("Backslash at end of string")
		
		c = s[pos+1]
		if c == "0":
			if pos+2 >= len(s):
				raise ValueError("Incomplete numeric escape at end of string")
			
			c2 = s[pos+2]
			if c2 in "Bb":
				if pos+11 > len(s):
					raise ValueError("Incomplete binary escape at end of string")
				
				ret.append(int(s[pos+3:pos+11], 2))
				lastpos = pos+11
			elif c2 in "Dd":
				if pos+6 > len(s):
					raise ValueError("Incomplete decimal escape at end of string")
				
				ret.append(int(s[pos+3:pos+6], 10))
				lastpos = pos+6
			elif c2 in "Xx":
				if pos+5 > len(s):
					raise ValueError("Incomplete hexadecimal escape at end of string")
				
				ret.append(int(s[pos+3:pos+5], 16))
				lastpos = pos+5
			elif c2 in "0123456789":
				if pos+4 > len(s):
					raise ValueError("Incomplete octal escape at end of string")
				
				ret.append(int(s[pos+1:pos+4], 8))
				lastpos = pos+4
		elif c == "$":
			if pos+4 > len(s):
				raise ValueError("Incomplete hexadecimal escape at end of string")
			
			ret.append(int(s[pos+2:pos+4], 16))
			lastpos = pos+4
		elif c in "123":
			if pos+4 > len(s):
				raise ValueError("Incomplete octal escape at end of string")
			
			ret.append(int(s[pos+1:pos+4], 8))
			lastpos = pos+4
		else:
			ret.append({
				"t": 0x09,
				"b": 0x08,
				"r": 0x0a,
				"n": 0x0d,
				"f": 0x0c,
				"v": 0x0b,
				"?": 0x7f,
				"\\": 0x5c,
				"'": 0x27,
				'"': 0x22,
			}.get(c, ord(c)))
			lastpos = pos+2
		
		pos = s.find("\\", lastpos)
	
	ret.extend(s[lastpos:].encode(common.STRING_ENCODING))
	return bytes(ret)


# noinspection PyMethodMayBeStatic, PyPep8Naming
class RezParser(object):
	"""Rez preprocessor and parser, based on the description and syntax given in Appendix C, "The Rez Language", in "Building and Managing Programs in MPW, 2nd Edition". A copy of this file can be found in the "docs" folder in this repo.
	This file can also be found on Max1zzz's server "www.max1zzz.co.uk", at location "/%2BMac OS Classic/Programming/Macintosh Programmers Workshop/MPW (2001)/Documentation/MPW_Reference/Building_Progs_in_MPW.sit".
	The server can be accessed via a web interface ("http://www.max1zzz.co.uk:8000", username "mg", password "mg"), or via FTP ("ftp://www.max1zzz.co.uk:21", username "mg", password "mg"), or via one of the other methods listed at "http://max1zzz.co.uk/servers.html".
	"""
	
	tokens = lexer.RezLexer.tokens
	
	start = "Start symbol must be set manually"
	
	def p_error(self, t):
		raise ParseError(t, filename=t.lexer.filename, lineno=t.lineno)
	
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
		
		if p[1].startswith("'"):
			try:
				unescaped = _unescape_string(p[1][1:-1])
			except ValueError as e:
				raise ParseError(str(e), filename=p[-1].lexer.filename, lineno=p[-1].lineno)
			value = int.from_bytes(unescaped, "big")
		elif p[1].startswith("$"):
			value = int(p[1][1:], 16)
		elif p[1].startswith("0X") or p[1].startswith("0x"):
			value = int(p[1][2:], 16)
		elif p[1].startswith("0B") or p[1].startswith("0b"):
			value = int(p[1][2:], 2)
		elif p[1].startswith("0"):
			value = int(p[1], 8)
		else:
			value = int(p[1], 10)
		
		p[0] = ast.IntLiteral(value=value)
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
		
		p[0] = ast.ResourceAttribute(value=ast.ResourceAttribute.Value[p[1].lower()])
		return p
	
	def p_int_function_call(self, p):
		"""int_function_call : FUN_ARRAYINDEX LPAREN IDENTIFIER comma_opt RPAREN
		| FUN_ATTRIBUTES
		| FUN_BITFIELD LPAREN int_expression COMMA int_expression COMMA int_expression comma_opt RPAREN
		| FUN_BYTE LPAREN int_expression comma_opt RPAREN
		| FUN_COUNTOF LPAREN IDENTIFIER comma_opt RPAREN
		| FUN_DAY
		| FUN_HOUR
		| FUN_ID
		| FUN_LONG LPAREN int_expression comma_opt RPAREN
		| FUN_MINUTE
		| FUN_MONTH
		| FUN_PACKEDSIZE LPAREN int_expression COMMA int_expression COMMA int_expression comma_opt RPAREN
		| FUN_RESOURCESIZE
		| FUN_SECOND
		| FUN_TYPE
		| FUN_WEEKDAY
		| FUN_WORD LPAREN int_expression comma_opt RPAREN
		| FUN_YEAR
		"""
		
		name = p[1].lower()[2:]
		if name == "arrayindex":
			p[0] = ast.FunArrayIndex(array_name=p[3])
		elif name == "attributes":
			p[0] = ast.FunAttributes()
		elif name == "bitfield":
			p[0] = ast.FunBitField(start=p[3], offset=p[5], length=p[7])
		elif name == "byte":
			p[0] = ast.FunByte(start=p[3])
		elif name == "countof":
			p[0] = ast.FunCountOf(array_name=p[3])
		elif name == "day":
			p[0] = ast.FunDay()
		elif name == "hour":
			p[0] = ast.FunHour()
		elif name == "id":
			p[0] = ast.FunID()
		elif name == "long":
			p[0] = ast.FunLong(start=p[3])
		elif name == "minute":
			p[0] = ast.FunMinute()
		elif name == "month":
			p[0] = ast.FunMonth()
		elif name == "packedsize":
			p[0] = ast.FunPackedSize(start=p[3], row_bytes=p[5], row_count=p[7])
		elif name == "resourcesize":
			p[0] = ast.FunResourceSize()
		elif name == "second":
			p[0] = ast.FunSecond()
		elif name == "type":
			p[0] = ast.FunType()
		elif name == "weekday":
			p[0] = ast.FunWeekday()
		elif name == "word":
			p[0] = ast.FunWord(start=p[3])
		elif name == "year":
			p[0] = ast.FunYear()
		else:
			raise NotImplementedError(f"Unhandled int function: {name}")
		
		return p
	
	def p_label_subscript_indices(self, p):
		"""label_subscript_indices : int_expression
		| label_subscript_indices COMMA int_expression
		"""
		
		if len(p) == 2:
			p[0] = [p[1]]
		else:
			p[0] = p[1] + [p[3]]
		
		return p
	
	def p_int_expression_simple(self, p):
		"""int_expression_simple : intlit
		| resource_attribute
		| int_function_call
		| IDENTIFIER
		| IDENTIFIER LBRACKET label_subscript_indices RBRACKET
		| LPAREN int_expression RPAREN
		"""
		
		if isinstance(p[1], str):
			if len(p) > 2:
				p[0] = ast.LabelSubscript(name=p[1], subscripts=p[3])
			else:
				p[0] = ast.IntSymbol(name=p[1])
		elif len(p) > 2:
			p[0] = p[2]
		else:
			p[0] = p[1]
		
		return p
	
	def p_int_expression_unaryop(self, p):
		"""int_expression_unaryop : int_expression_simple
		| MINUS int_expression_unaryop
		| BOOLNOT int_expression_unaryop
		| BITNOT int_expression_unaryop
		"""
		
		if len(p) > 2:
			if p[1] == "-":
				p[0] = ast.Negative(value=p[2])
			elif p[1] == "!":
				p[0] = ast.BoolNot(value=p[2])
			elif p[1] == "~":
				p[0] = ast.BitNot(value=p[2])
			else:
				raise NotImplementedError(f"Unhandled unary operator: {p[1]}")
		else:
			p[0] = p[1]
		
		return p
	
	def p_int_expression_muldiv(self, p):
		"""int_expression_muldiv : int_expression_unaryop
		| int_expression_muldiv MULTIPLY int_expression_unaryop
		| int_expression_muldiv DIVIDE int_expression_unaryop
		| int_expression_muldiv MODULO int_expression_unaryop
		"""
		
		if len(p) > 2:
			if p[2] == "*":
				p[0] = ast.Multiply(left=p[1], right=p[3])
			elif p[2] == "/":
				p[0] = ast.Divide(left=p[1], right=p[3])
			elif p[2] == "%":
				p[0] = ast.Modulo(left=p[1], right=p[3])
			else:
				raise NotImplementedError(f"Unhandled binary operator: {p[2]}")
		else:
			p[0] = p[1]
		
		return p
	
	def p_int_expression_plusminus(self, p):
		"""int_expression_plusminus : int_expression_muldiv
		| int_expression_plusminus PLUS int_expression_muldiv
		| int_expression_plusminus MINUS int_expression_muldiv
		"""
		
		if len(p) > 2:
			if p[2] == "+":
				p[0] = ast.Add(left=p[1], right=p[3])
			elif p[2] == "-":
				p[0] = ast.Subtract(left=p[1], right=p[3])
			else:
				raise NotImplementedError(f"Unhandled binary operator: {p[2]}")
		else:
			p[0] = p[1]
		
		return p
	
	def p_int_expression_bitshift(self, p):
		"""int_expression_bitshift : int_expression_plusminus
		| int_expression_bitshift SHIFTLEFT int_expression_plusminus
		| int_expression_bitshift SHIFTRIGHT int_expression_plusminus
		"""
		
		if len(p) > 2:
			if p[2] == "<<":
				p[0] = ast.BitShiftLeft(left=p[1], right=p[3])
			elif p[2] == ">>":
				p[0] = ast.BitShiftRight(left=p[1], right=p[3])
			else:
				raise NotImplementedError(f"Unhandled binary operator: {p[2]}")
		else:
			p[0] = p[1]
		
		return p
	
	def p_int_expression_relational(self, p):
		"""int_expression_relational : int_expression_bitshift
		| int_expression_relational LESS int_expression_bitshift
		| int_expression_relational GREATER int_expression_bitshift
		| int_expression_relational LESSEQUAL int_expression_bitshift
		| int_expression_relational GREATEREQUAL int_expression_bitshift
		"""
		
		if len(p) > 2:
			if p[2] == "<":
				p[0] = ast.LessThan(left=p[1], right=p[3])
			elif p[2] == ">":
				p[0] = ast.GreaterThan(left=p[1], right=p[3])
			elif p[2] == "<=":
				p[0] = ast.LessThanEqual(left=p[1], right=p[3])
			elif p[2] == ">=":
				p[0] = ast.GreaterThanEqual(left=p[1], right=p[3])
			else:
				raise NotImplementedError(f"Unhandled binary operator: {p[2]}")
		else:
			p[0] = p[1]
		
		return p
	
	def p_int_expression_equal(self, p):
		"""int_expression_equal : int_expression_relational
		| int_expression_equal EQUAL int_expression_relational
		| int_expression_equal NOTEQUAL int_expression_relational
		"""
		
		if len(p) > 2:
			if p[2] == "==":
				p[0] = ast.Equal(left=p[1], right=p[3])
			elif p[2] == "!=":
				p[0] = ast.NotEqual(left=p[1], right=p[3])
			else:
				raise NotImplementedError(f"Unhandled binary operator: {p[2]}")
		else:
			p[0] = p[1]
		
		return p
	
	def p_int_expression_bitand(self, p):
		"""int_expression_bitand : int_expression_equal
		| int_expression_bitand BITAND int_expression_equal
		"""
		
		if len(p) > 2:
			p[0] = ast.BitAnd(left=p[1], right=p[3])
		else:
			p[0] = p[1]
		
		return p
	
	def p_int_expression_bitxor(self, p):
		"""int_expression_bitxor : int_expression_bitand
		| int_expression_bitxor BITXOR int_expression_bitand
		"""
		
		if len(p) > 2:
			p[0] = ast.BitXor(left=p[1], right=p[3])
		else:
			p[0] = p[1]
		
		return p
	
	def p_int_expression_bitor(self, p):
		"""int_expression_bitor : int_expression_bitxor
		| int_expression_bitor BITOR int_expression_bitxor
		"""
		
		if len(p) > 2:
			p[0] = ast.BitOr(left=p[1], right=p[3])
		else:
			p[0] = p[1]
		
		return p
	
	def p_int_expression_booland(self, p):
		"""int_expression_booland : int_expression_bitor
		| int_expression_booland BOOLAND int_expression_bitor
		"""
		
		if len(p) > 2:
			p[0] = ast.BoolAnd(left=p[1], right=p[3])
		else:
			p[0] = p[1]
		
		return p
	
	def p_int_expression_boolor(self, p):
		"""int_expression_boolor : int_expression_booland
		| int_expression_boolor BOOLOR int_expression_booland
		"""
		
		if len(p) > 2:
			p[0] = ast.BoolOr(left=p[1], right=p[3])
		else:
			p[0] = p[1]
		
		return p
	
	def p_int_expression(self, p):
		"""int_expression : int_expression_boolor"""
		
		p[0] = p[1]
		return p
	
	def p_expression(self, p):
		"""expression : int_expression
		| string_expression
		"""
		
		p[0] = p[1]
		return p
	
	def p_varargs_part(self, p):
		"""varargs_part : empty
		| varargs_part COMMA expression
		"""
		
		p[0] = p[1] + p[3:]
		return p
	
	def p_varargs_opt(self, p):
		"""varargs_opt : varargs_part comma_opt"""
		
		p[0] = p[1]
		return p
	
	def p_string_function_call(self, p):
		"""string_function_call : FUN_DATE
		| FUN_FORMAT LPAREN string_expression varargs_opt RPAREN
		| FUN_NAME
		| FUN_READ LPAREN string_expression comma_opt RPAREN
		| FUN_RESOURCE LPAREN string_expression COMMA int_expression COMMA int_expression COMMA string_expression comma_opt RPAREN
		| FUN_SHELL LPAREN string_expression comma_opt RPAREN
		| FUN_TIME
		| FUN_VERSION
		"""
		
		name = p[1].lower()[2:]
		if name == "date":
			p[0] = ast.FunDate()
		elif name == "format":
			p[0] = ast.FunFormat(format=p[3], args=p[4])
		elif name == "name":
			p[0] = ast.FunName()
		elif name == "read":
			p[0] = ast.FunRead(path=p[3])
		elif name == "resource":
			p[0] = ast.FunResource(path=p[3], type=p[5], id=p[7], name=p[9])
		elif name == "shell":
			p[0] = ast.FunShell(name=p[3])
		elif name == "time":
			p[0] = ast.FunTime()
		elif name == "version":
			p[0] = ast.FunVersion()
		else:
			raise NotImplementedError(f"Unhandled string function: {name}")
		
		return p
	
	def p_single_string(self, p):
		"""single_string : STRINGLIT_TEXT
		| STRINGLIT_HEX
		| string_function_call
		"""
		
		if isinstance(p[1], str):
			if p[1].startswith("$"):
				p[0] = ast.StringLiteral(value=bytes.fromhex(p[1][2:-1]))
			else:
				try:
					unescaped = _unescape_string(p[1][1:-1])
				except ValueError as e:
					raise ParseError(str(e), filename=p[-1].lexer.filename, lineno=p[-1].lineno)
				p[0] = ast.StringLiteral(value=unescaped)
		else:
			p[0] = p[1]
		
		return p
	
	def p_string_expression_part(self, p):
		"""string_expression_part : single_string
		| string_expression_part single_string
		"""
		
		if len(p) > 2:
			p[0] = p[1] + [p[2]]
		else:
			p[0] = [p[1]]
		
		return p
	
	def p_string_expression(self, p):
		"""string_expression : string_expression_part"""
		
		if len(p[1]) == 1:
			p[0] = p[1][0]
		else:
			p[0] = ast.StringConcat(values=p[1])
		
		return p
	
	def p_string_expression_opt(self, p):
		"""string_expression_opt : empty
		| string_expression
		"""
		
		p[0] = p[1] or None
		return p
	
	def p_resource_name_opt(self, p):
		"""resource_name_opt : empty
		| COMMA string_expression
		"""
		
		if len(p) > 2:
			p[0] = p[2]
		else:
			p[0] = None
		
		return p
	
	def p_resource_attributes_named(self, p):
		"""resource_attributes_named : resource_attribute
		| resource_attributes_named COMMA resource_attribute
		"""
		
		p[0] = [p[1]] if len(p) == 2 else p[1] + p[3:]
		return p
	
	def p_resource_attributes(self, p):
		"""resource_attributes : resource_attributes_named
		| int_expression
		"""
		
		p[0] = p[1]
		return p
	
	def p_resource_attributes_opt(self, p):
		"""resource_attributes_opt : empty
		| COMMA resource_attributes
		"""
		
		if len(p) > 2:
			p[0] = p[2]
		else:
			p[0] = []
		
		return p
	
	def p_resource_id_range(self, p):
		"""resource_id_range : int_expression COLON int_expression"""
		
		p[0] = ast.IDRange(begin=p[1], end=p[3])
		return p
	
	def p_resource_spec_typedef(self, p):
		"""resource_spec_typedef : int_expression
		| int_expression LPAREN int_expression RPAREN
		| int_expression LPAREN resource_id_range RPAREN
		"""
		
		if len(p) > 2:
			p[0] = ast.ResourceSpecTypeDef(type=p[1], id=p[3])
		else:
			p[0] = ast.ResourceSpecTypeDef(type=p[1], id=None)
		
		return p
	
	def p_resource_spec_typeuse(self, p):
		"""resource_spec_typeuse : int_expression
		| int_expression LPAREN int_expression RPAREN
		"""
		
		if len(p) > 2:
			p[0] = ast.ResourceSpecTypeUse(type=p[1], id=p[3])
		else:
			p[0] = ast.ResourceSpecTypeUse(type=p[1], id=None)
		
		return p
	
	def p_resource_spec_def(self, p):
		"""resource_spec_def : int_expression LPAREN int_expression resource_name_opt resource_attributes_opt RPAREN"""
		
		p[0] = ast.ResourceSpecDef(type=p[1], id=p[3], name=p[4], attributes=p[5])
		return p
	
	def p_resource_spec_use(self, p):
		"""resource_spec_use : int_expression
		| int_expression LPAREN int_expression RPAREN
		| int_expression LPAREN resource_id_range RPAREN
		| int_expression LPAREN string_expression RPAREN
		"""
		
		if len(p) > 2:
			p[0] = ast.ResourceSpecUse(type=p[1], id_or_name=p[3])
		else:
			p[0] = ast.ResourceSpecUse(type=p[1], id_or_name=None)
		
		return p
	
	def p_change_statement(self, p):
		"""change_statement : CHANGE resource_spec_use TO resource_spec_def SEMICOLON"""
		
		p[0] = ast.Change(from_spec=p[2], to_spec=p[4])
		return p
	
	def p_data_statement(self, p):
		"""data_statement : DATA resource_spec_def LBRACE string_expression_opt semicolon_opt RBRACE SEMICOLON"""
		
		p[0] = ast.Data(spec=p[2], value=p[4])
		return p
	
	def p_delete_statement(self, p):
		"""delete_statement : DELETE resource_spec_use SEMICOLON"""
		
		p[0] = ast.Delete(spec=p[2])
		return p
	
	def p_enum_constant(self, p):
		"""enum_constant : IDENTIFIER
		| IDENTIFIER ASSIGN int_expression
		"""
		
		if len(p) > 2:
			p[0] = ast.EnumConstant(name=p[1], value=p[3])
		else:
			p[0] = ast.EnumConstant(name=p[1], value=None)
		
		return p
	
	def p_enum_constants(self, p):
		"""enum_constants : enum_constant
		| enum_constants COMMA enum_constant
		"""
		
		if len(p) > 3:
			p[0] = p[1] + [p[3]]
		else:
			p[0] = [p[1]]
		
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
		
		if len(p) > 6:
			p[0] = ast.Enum(name=p[2], constants=p[4])
		else:
			p[0] = ast.Enum(name=None, constants=p[3])
		
		return p
	
	def p_include_statement(self, p):
		"""include_statement : INCLUDE string_expression SEMICOLON
		| INCLUDE string_expression resource_spec_use SEMICOLON
		| INCLUDE string_expression NOT int_expression SEMICOLON
		| INCLUDE string_expression int_expression AS int_expression SEMICOLON
		| INCLUDE string_expression resource_spec_use AS resource_spec_def SEMICOLON
		"""
		
		if len(p) > 6:
			p[0] = ast.Include(path=p[2], from_spec=p[3], to_spec=p[5])
		elif len(p) > 5:
			p[0] = ast.Include(path=p[2], from_spec=ast.InvertedType(type=p[4]), to_spec=None)
		elif len(p) > 4:
			p[0] = ast.Include(path=p[2], from_spec=p[3], to_spec=None)
		else:
			p[0] = ast.Include(path=p[2], from_spec=None, to_spec=None)
		
		return p
	
	def p_read_statement(self, p):
		"""read_statement : READ resource_spec_def string_expression SEMICOLON"""
		
		p[0] = ast.Read(spec=p[2], path=p[3])
		return p
	
	def p_resource_value(self, p):
		"""resource_value : IDENTIFIER
		| expression
		| LBRACE array_values RBRACE
		| IDENTIFIER LBRACE resource_values semicolon_opt RBRACE
		"""
		
		if len(p) > 4:
			p[0] = ast.SwitchValue(label=p[1], values=p[3])
		elif len(p) > 3:
			p[0] = ast.ArrayValue(values=p[2])
		elif isinstance(p[1], str):
			p[0] = ast.Symbol(name=p[1])
		else:
			p[0] = p[1]
		
		return p
	
	def p_resource_values_part(self, p):
		"""resource_values_part : resource_value
		| resource_values_part COMMA resource_value
		"""
		
		if len(p) > 3:
			p[0] = p[1] + [p[3]]
		else:
			p[0] = [p[1]]
		
		return p
	
	def p_resource_values(self, p):
		"""resource_values : empty
		| resource_values_part comma_opt
		"""
		
		p[0] = p[1]
		return p
	
	def p_array_values_part(self, p):
		"""array_values_part : resource_values
		| array_values_part SEMICOLON resource_values
		"""
		
		if len(p) > 2:
			p[0] = p[1] + [p[3]]
		else:
			p[0] = [p[1]]
		
		return p
	
	def p_array_values(self, p):
		"""array_values : empty
		| array_values_part semicolon_opt
		"""
		
		p[0] = p[1]
		return p
	
	def p_resource_statement(self, p):
		"""resource_statement : RESOURCE resource_spec_def LBRACE resource_values semicolon_opt RBRACE SEMICOLON"""
		
		p[0] = ast.Resource(spec=p[2], values=p[4])
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
		"""numeric_type : BITSTRING LBRACKET int_expression RBRACKET
		| BYTE
		| INT
		| INTEGER
		| LONGINT
		"""
		
		if len(p) > 4:
			p[0] = (p[1], p[3])
		else:
			p[0] = (p[1], None)
		
		return p
	
	def p_string_type_name(self, p):
		"""string_type_name : STRING
		| CSTRING
		| PSTRING
		| WSTRING
		"""
		
		p[0] = p[1]
		return p
	
	def p_string_type(self, p):
		"""string_type : string_type_name
		| string_type_name LBRACKET int_expression RBRACKET
		"""
		
		if len(p) > 4:
			p[0] = (p[1], p[3])
		else:
			p[0] = (p[1], None)
		
		return p
	
	def p_simple_type(self, p):
		"""simple_type : BOOLEAN
		| numeric_type
		| CHAR
		| string_type
		| POINT
		| RECT
		"""
		
		if isinstance(p[1], str):
			p[0] = (p[1], None)
		else:
			p[0] = p[1]
		
		return p
	
	def p_symbolic_constant(self, p):
		"""symbolic_constant : IDENTIFIER
		| IDENTIFIER ASSIGN resource_value
		"""
		
		if len(p) > 2:
			p[0] = ast.SymbolicConstant(name=p[1], value=p[3])
		else:
			p[0] = ast.SymbolicConstant(name=p[1], value=None)
		
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
		
		if len(p) > 4:
			p[0] = (p[1], p[3])
		elif len(p) > 3:
			p[0] = (p[1], p[2])
		else:
			p[0] = (p[1], None)
		
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
		| FILL fill_field_size LBRACKET int_expression RBRACKET SEMICOLON
		"""
		
		if len(p) > 5:
			p[0] = ast.FillField(type=ast.FillField.Type[p[2].lower()], count=p[4])
		else:
			p[0] = ast.FillField(type=ast.FillField.Type[p[2].lower()], count=None)
		
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
		
		p[0] = ast.AlignField(type=ast.AlignField.Type[p[2].lower()])
		
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
		| array_modifiers_opt ARRAY LBRACKET int_expression RBRACKET LBRACE fields RBRACE SEMICOLON
		"""
		
		wide = False
		seen = set()
		for mod in p[1]:
			mod = mod.lower()
			if mod in seen:
				raise ParseError(f"Duplicate attribute {mod!r}", filename=p[-1].lexer.filename, lineno=p[-1].lineno)
			seen.add(mod)
			
			if mod == "wide":
				wide = True
			else:
				raise ParseError(f"Unsupported modifier {mod!r} for type array", filename=p[-1].lexer.filename, lineno=p[-1].lineno)
		
		if len(p) > 9:
			p[0] = ast.ArrayField(wide=wide, label=None, count=p[4], fields=p[7])
		elif len(p) > 7:
			p[0] = ast.ArrayField(wide=wide, label=p[3], count=None, fields=p[5])
		else:
			p[0] = ast.ArrayField(wide=wide, label=None, count=None, fields=p[4])
		
		return p
	
	def p_switch_field_case(self, p):
		"""switch_field_case : CASE IDENTIFIER COLON fields"""
		
		p[0] = ast.SwitchCase(label=p[2], fields=p[4])
		return p
	
	def p_switch_field_cases(self, p):
		"""switch_field_cases : empty
		| switch_field_cases switch_field_case
		"""
		
		p[0] = p[1] + p[2:]
		return p
	
	def p_switch_field(self, p):
		"""switch_field : SWITCH LBRACE switch_field_cases RBRACE SEMICOLON"""
		
		p[0] = ast.Switch(cases=p[3])
		return p
	
	def p_field(self, p):
		"""field : SEMICOLON
		| IDENTIFIER COLON
		| simple_field_modifiers_opt simple_field
		| fill_field
		| align_field
		| array_field
		| switch_field
		"""
		
		if len(p) > 2:
			if isinstance(p[1], str):
				# A label.
				p[0] = ast.Label(name=p[1])
			else:
				# Simple fields (boolean, numbers, char, strings) and their modifiers are parsed separately up until here.
				# This complicates the handling here, but is required because of parsing ambiguities (the hex modifier can appear on numbers and strings).
				
				modifiers = p[1]
				(typename, size), value_or_symconsts = p[2]
				typename = typename.lower()
				
				is_key = False
				signed = True
				base = None
				seen = set()
				for mod in modifiers:
					mod = mod.lower()
					if mod in seen:
						raise ParseError(f"Duplicate attribute {mod!r}", filename=p[-1].lexer.filename, lineno=p[-1].lineno)
					seen.add(mod)
					
					if mod == "key":
						is_key = True
					elif mod == "unsigned":
						if typename not in ("bitstring", "byte", "integer", "longint"):
							raise ParseError(f"Unsupported modifier {mod!r} for type {typename!r}", filename=p[-1].lexer.filename, lineno=p[-1].lineno)
						
						signed = False
					elif mod in ("binary", "octal", "decimal", "hex", "literal"):
						if mod == "hex" and typename == "string":
							# Special case: hex is allowed on string
							pass
						elif typename not in ("bitstring", "byte", "integer", "longint"):
							raise ParseError(f"Unsupported modifier {mod!r} for type {typename!r}", filename=p[-1].lexer.filename, lineno=p[-1].lineno)
						
						if base is None:
							base = mod
						else:
							raise ParseError(f"Duplicate base modifier {mod!r} (base was previously set to {base!r}", filename=p[-1].lexer.filename, lineno=p[-1].lineno)
					else:
						raise ParseError(f"Invalid modifier: {mod!r}", filename=p[-1].lexer.filename, lineno=p[-1].lineno)
				
				if typename == "int":
					typename = "integer"
				
				if typename == "boolean":
					fieldtype = ast.BooleanFieldType()
				elif typename in ("bitstring", "byte", "integer", "longint"):
					fieldtype = ast.NumericFieldType(
						signed=signed,
						base=ast.NumericFieldType.Base[base or "decimal"],
						type=ast.NumericFieldType.Type[typename],
						size=size,
					)
				elif typename == "char":
					fieldtype = ast.CharFieldType()
				elif typename in ("string", "cstring", "pstring", "wstring"):
					fieldtype = ast.StringFieldType(
						format=ast.StringFieldType.Format[base or "literal"],
						type=ast.StringFieldType.Type[typename],
						length=size,
					)
				elif typename == "point":
					fieldtype = ast.PointFieldType()
				elif typename == "rect":
					fieldtype = ast.RectFieldType()
				else:
					raise ParseError(f"Unknown field type {typename!r}", filename=p[-1].lexer.filename, lineno=p[-1].lineno)
				
				if value_or_symconsts is None:
					value = None
					symconsts = []
				elif isinstance(value_or_symconsts, ast.ResourceValue):
					value = value_or_symconsts
					symconsts = []
				else:
					value = None
					symconsts = value_or_symconsts
				
				p[0] = ast.SimpleField(
					type=fieldtype,
					value=value,
					symbolic_constants=symconsts,
					is_key=is_key,
				)
		elif p[1] == ";":
			# Remove semicolons
			p[0] = None
		else:
			# Anything else (fill, align, array, switch) can be passed through as-is.
			p[0] = p[1]
		
		return p
	
	def p_fields(self, p):
		"""fields : empty
		| fields field
		"""
		
		if len(p) > 2 and p[2]:
			p[0] = p[1] + [p[2]]
		else:
			p[0] = p[1]
		
		return p
	
	def p_type_statement(self, p):
		"""type_statement : TYPE resource_spec_typedef LBRACE fields RBRACE SEMICOLON
		| TYPE resource_spec_typedef AS resource_spec_typeuse SEMICOLON
		"""
		
		if len(p) > 6:
			p[0] = ast.Type(spec=p[2], fields=p[4], from_spec=None)
		else:
			p[0] = ast.Type(spec=p[2], fields=None, from_spec=p[4])
		
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
		
		if p[1] == ";":
			p[0] = None
		else:
			p[0] = p[1]
		
		return p
	
	def p_file_part(self, p):
		"""file_part : empty
		| file_part statement
		"""
		
		if len(p) > 2 and p[2]:
			p[0] = p[1] + [p[2]]
		else:
			p[0] = p[1]
		
		return p
	
	def p_start_file(self, p):
		"""start_file : file_part"""
		
		p[0] = ast.File(statements=p[1])
		return p
	
	def p_start_expr(self, p):
		"""start_expr : expression"""
		
		p[0] = p[1]
		return p
	
	def __init__(self, **kwargs):
		super().__init__()
		
		self.parser_file = ply.yacc.yacc(module=self, start="start_file", tabmodule="_table_parser_file", debugfile="_debug_parser_file.out", **kwargs)
		self.parser_expr = ply.yacc.yacc(module=self, start="start_expr", tabmodule="_table_parser_expr", debugfile="_debug_parser_expr.out", **kwargs)
		self.parser_file.parse("", lexer.RezLexer())
		self.parser_expr.parse("0", lexer.RezLexer())
	
	def parse_file(self, inp, lexer, **kwargs):
		self.parser_file.restart()
		return self.parser_file.parse(inp, lexer, **kwargs)
	
	def parse_expr(self, inp, lexer, **kwargs):
		self.parser_expr.restart()
		return self.parser_expr.parse(inp, lexer, **kwargs)
