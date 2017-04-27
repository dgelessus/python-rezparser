import functools
import sys

import ply.lex
import ply.yacc

__version__ = "0.0.0"


# NOTE: The meanings of the control characters "\r" and "\n" are reversed in Rez. For example, in $$read input and #printf output, all "\r" are replaced with "\n" and vice versa. This is because the line ending on classic Mac OS was "\r", and on Unix (including OS X) is "\n".

# NOTE: Rez files can also include "preprocessor" directives. The basic behavior is equivalent to standard cpp, but there are more advanced cases where the two are very different. The Rez "preprocessor directives" are actually closely integrated with the language, and can't easily be processed without understanding the language semantics. This requires some unusual parsing techniques below, and some very odd corner cases might not be handled correctly.
# #define macros can only be constants. Macro functions do not exist. Enum constants are implemented as macros (but unlike macros, their values are evaluated when they are defined, not when they are used). Preprocessor directives may be constructed from macros. The identifier directly after the hash symbol is *not* macro-expanded, but may come from a macro expansion that already includes the hash symbol. (Constructing preprocessor directives from macros is not supported by this parser.)
# #undef exists and does what you expect. It is not an error to re-#define an existing macro without an intermediate #undef, or to #undef nonexistant macros.
# Recursive macro expansions are not treated specially (unlike in C, where a macro is not expanded when it appears inside its own expansion, even indirectly). Nesting macros more than 100 levels deep is an error, which makes recursive macros completely useless.
# There are four predefined macros: true (1), false (0), rez (1 in Rez, 0 in DeRez), and derez (1 in DeRez, 0 in Rez). These are not keywords (unlike the resource attribute constants). They are normal macros that can be redefined or undefined (although the documentation recommends agianst doing so).
# Macro names are case-insensitive.
# There are #if, #ifdef, #ifndef, #elif, #else, #endif. The defined expression (with or without parens) is supported to check whether a macro is defined. Rez "functions" can be used in expressions. An empty expression evaluates to true, but also generates an error, so this is not useful in practice.
# #include and #import exist. Filenames may be angle-bracketed or quoted. Quoted filenames have some special features, see below. The path separator is "/" and not ":". In some examples, the filename is completely bare, but current Rez doesn't accept that.
# There is a #printf(format, ...) directive that is mostly equivalent to fprintf(stderr, format, ...) in C. At most 20 arguments can be used. Contrary to what the docs say, a terminating semicolon is allowed in practice.
# Most preprocessor directives are very lenient about text after their intended input.
# #if, #elif, #printf input can be terminated by a semicolon, anything after it is treated like normal source code. (In the case of #if and #elif, the code afterwards is only executed if the condition is true.)
# #else, #endif ignore any arguments.
# #include/#import (with angle brackets), #undef, #ifdef, #ifndef ignore anything after their intended argument (the following text doesn't need to be syntactically valid).
# The non-angle-bracket form of #include/#import accepts a sequence of string literals and string-producing Rez functions (like $$shell or $$format), which are concatenated to produce the final path. Macros are not expanded, any use of an identifier (even as an argument to a Rez function) is an error. A semicolon can be used to terminate this sequence, and anything after it is ignored (the text doesn't need to be syntactically valid). When terminating the sequence with some other symbol (doesn't need to be syntactically valid either), there is no error, but the include silently does nothing (which usually leads to an error later on in the file because of missing definitions).

class RezParserError(Exception):
	__slots__ = ()

class LexError(RezParserError):
	__slots__ = ()

class PreprocessError(RezParserError):
	__slots__ = ()

class ParseError(RezParserError):
	__slots__ = ()


class Token(ply.lex.LexToken):
	@classmethod
	def wrapper(cls, pattern):
		if callable(pattern):
			@functools.wraps(pattern)
			def _wrapper(t):
				return pattern(cls(t))
		else:
			def _wrapper(t):
				return cls(t)
		
		return ply.lex.TOKEN(pattern)(_wrapper)
	
	def __init__(self, type, value=None, lineno=None, lexpos=None, **kwargs):
		super().__init__()
		
		if isinstance(type, (Token, ply.lex.LexToken)):
			self.type = type.type
			self.value = type.value
			self.lineno = type.lineno
			self.lexpos = type.lexpos
		else:
			self.type = type
			self.value = value
			self.lineno = lineno
			self.lexpos = lexpos
		
		self.__dict__.update(kwargs)
	
	def __str__(self):
		return repr(self)
	
	def __repr__(self):
		extra = "".join(f", {k}={v!r}" for k, v in self.__dict__.items() if k not in {"type", "value", "lineno", "lexpos"})
		return f"{type(self).__module__}.{type(self).__qualname__}(type={self.type!r}, value={self.value!r}, lineno={self.lineno!r}, lexpos={self.lexpos!r}{extra})"


# noinspection PyMethodMayBeStatic, PyPep8Naming
class RezLexer(object):
	tokens = (
		"PP_INCLUDE",
		"PP_DEFINE",
		"PP_UNDEF",
		"PP_IF",
		"PP_ELIF",
		"PP_IFDEF",
		"PP_IFNDEF",
		"PP_ELSE",
		"PP_ENDIF",
		"PP_PRINTF",
		"PP_EMPTY",
		"NEWLINE",
		"IDENTIFIER",
		"STRINGLIT_TEXT",
		"STRINGLIT_HEX",
		"INTLIT_DEC",
		"INTLIT_HEX",
		"INTLIT_OCT",
		"INTLIT_BIN",
		"INTLIT_CHAR",
		"SHIFTLEFT",
		"SHIFTRIGHT",
		"EQUAL",
		"NOTEQUAL",
		"LESSEQUAL",
		"GREATEREQUAL",
		"BOOLAND",
		"BOOLOR",
		"LBRACE",
		"RBRACE",
		"LBRACKET",
		"RBRACKET",
		"LPAREN",
		"RPAREN",
		"SEMICOLON",
		"COLON",
		"COMMA",
		"ASSIGN",
		"PLUS",
		"MINUS",
		"MULTIPLY",
		"DIVIDE",
		"MODULO",
		"BITAND",
		"BITOR",
		"BITXOR",
		"BITNOT",
		"LESS",
		"GREATER",
		"BOOLNOT",
	)
	
	# NOTE: Keywords are completely case-insensitive.
	# By convention, most are usually lower-cased.
	# Top-level structures are sometimes cased like English sentences - first keyword title-cased, further keywords (if any) lower-cased.
	keywords = (
		# Top-level structures
		"as",
		"change",
		"data",
		"delete",
		"enum",
		"include",
		"not",
		"type",
		"read",
		"resource",
		"to",
		
		# "Primitive" types
		"bit",
		"bitstring",
		"boolean",
		"byte",
		"char",
		"cstring",
		"nibble",
		"integer",
		"long",
		"longint",
		"point",
		"pstring",
		"rect",
		"string",
		"word",
		"wstring",
		
		# Type modifiers
		"binary",
		"decimal",
		"hex",
		"key",
		"literal",
		"octal",
		"unsigned",
		
		# Type-ish things
		"align",
		"array",
		"case",
		"fill",
		"switch",
		"wide",
		
		# Named resource attributes
		"appheap", # 0
		"changed", # 2
		"compressed", # 1
		"locked", # 16
		"nonpreload", # 0
		"nonpurgeable", # 0
		"preload", # 4
		"protected", # 8
		"purgeable", # 32
		"sysheap", # 64
		"unchanged", # 0
		"uncompressed", # 0
		"unlocked", # 0
		"unprotected", # 0
		
		# Only usable in preprocessor conditions, but not allowed as an identifier elsewhere
		"defined",
	)
	
	# Rez "functions" are also case-insensitive, but they are usually camel-cased in whatever way the author found natural (for example, both $$Countof and $$CountOf are common).
	rez_functions = (
		"$$arrayindex", # (array-name) Current index (1-based) in array-name
		"$$attributes", # Attributes of current resource
		"$$bitfield", # (label, offset, length) Bitstring of length bits at offset bits after label
		"$$byte", # (label) Byte at label
		"$$countof", # (array-name) Number of elements in array-name
		"$$date", # Current date, format like "Wednesday, August 30, 1995", generated using IUDateString
		"$$day", # Current day (1 - 31)
		"$$format", # (fmtstring, arguments...) Format a string, basically like C sprintf
		"$$hour", # Current hour (0 - 23)
		"$$id", # ID of current resource
		"$$long", # (label) Longword at label
		"$$minute", # Current minute (0 - 59)
		"$$month", # Current month (1 - 12)
		"$$name", # Name of current resource
		"$$packedsize", # (start, RB, RC) Call UnpackBits RC times and return unpacked size of data at start
		"$$read", # ("filename") Read data fork of filename, searches through current directory and Rez -s path
		"$$resource", # ("filename", 'type', ID, "resource-name") Read resource 'type' (ID, "resource-name") from resource fork of filename
		"$$resourcesize", # Size of current resource (in bytes)
		"$$second", # Current second (0 - 59)
		"$$shell", # ("string-expression") Value of MPW Shell variable {string-expression}
		"$$time", # Current time, format like "23:45:35", generated using IUTimeString
		"$$type", # Type code of current resource
		"$$version", # String version of the Rez compiler
		"$$weekday", # Current weekday (1 - 7, 1 is Sunday)
		"$$word", # (label) Word at label
		"$$year", # Current year
	)
	
	tokens += tuple(keyword.upper() for keyword in keywords)
	tokens += tuple("FUN_" + fun[2:].upper() for fun in rez_functions)
	
	def t_error(self, t):
		raise LexError(t)
	
	_pp = r"(?m:^)[ \t]*\#[ \t]*"
	_id = r"[A-Za-z_][A-Za-z0-9_]*"
	_filename = r"(?:\"(?:[^\\\"\n]|\\.)*\"[ \t]*|[^\";\n])+"
	
	t_ignore_COMMENT_SINGLE = r"//[^\n]*"
	t_ignore_COMMENT_MULTI = r"(?s:/\*.*?\*/)"
	
	@ply.lex.TOKEN(_pp+r"(?:include|import)[ \t]*"+_filename+r";?.*")
	def t_PP_INCLUDE(self, t):
		t = Token(t)
		# Strip leading hash sign and any whitespace.
		text = t.value.lstrip()[1:].lstrip()
		
		# Differentiate between import and include.
		if text.startswith("import"):
			t.pp_include_type = "import"
			text = text[len("import"):].lstrip()
		else:
			t.pp_include_type = "include"
			text = text[len("include"):].lstrip()
		
		if text.startswith("<"):
			# Angle-quoted filename - no lexing needed, simply split filename from tail and store as-is.
			filename_end = text.index(">") + 1
			t.pp_include_filename = text[:filename_end]
			##t.pp_include_tail = text[filename_end:]
		else:
			# String expression filename - lexing needed.
			sublexer = self.lexer.clone()
			sublexer.input(text)
			
			t.pp_include_filename = []
			for tok in sublexer:
				if tok.type == "SEMICOLON":
					# A semicolon indicates the end of the filename, anything after it is the tail.
					##t.pp_include_tail = text[t.lexpos:]
					break
				
				t.pp_include_filename.append(tok)
			else:
				# Ensure that pp_include_tail is initialized even if there is no semicolon.
				pass##t.pp_include_tail = ""
		
		return t
	
	@ply.lex.TOKEN(_pp+r"define[ \t]+"+_id+r".*")
	def t_PP_DEFINE(self, t):
		t = Token(t)
		# Strip leading hash sign, define, and any whitespace.
		text = t.value.lstrip()[1:].lstrip()[len("define"):].lstrip()
		
		# Lex the macro identifier and expansion value.
		sublexer = self.lexer.clone()
		sublexer.input(text)
		t.pp_define_name = sublexer.token().value
		t.pp_define_value = list(sublexer)
		
		return t
	
	@ply.lex.TOKEN(_pp+r"undef[ \t]+"+_id+r".*")
	def t_PP_UNDEF(self, t):
		t = Token(t)
		# Strip leading hash sign, undef, and any whitespace.
		text = t.value.lstrip()[1:].lstrip()[len("undef"):].lstrip()
		
		# Lex the macro identifier and tail.
		sublexer = self.lexer.clone()
		sublexer.input(text)
		tok = sublexer.token()
		t.pp_undef_name = tok.value
		##t.pp_undef_tail = text[tok.lexpos:]
		
		return t
	
	t_PP_IF = _pp+r"if"
	t_PP_ELIF = _pp+r"elif"
	
	@ply.lex.TOKEN(_pp+r"ifn?def[ \t]+"+_id+r".*")
	def t_PP_IFDEF(self, t):
		t = Token(t)
		# Strip leading hash sign and any whitespace.
		text = t.value.lstrip()[1:].lstrip()
		
		# Differentiate between ifdef and ifndef.
		if text.startswith("ifndef"):
			t.pp_ifdef_type = "ifndef"
			text = text[len("ifndef"):].lstrip()
		else:
			t.pp_ifdef_type = "ifdef"
			text = text[len("ifdef"):].lstrip()
		
		# Lex the macro identifier and tail.
		sublexer = self.lexer.clone()
		sublexer.input(text)
		tok = sublexer.token()
		t.pp_ifdef_name = tok.value
		##t.pp_ifdef_tail = text[tok.lexpos:]
		return t
	
	t_PP_ELSE = _pp+r"else[^A-Za-z_]?.*"
	t_PP_ENDIF = _pp+r"endif[^A-Za-z_]?.*"
	t_PP_PRINTF = _pp+r"printf"
	t_PP_EMPTY = _pp
	
	@ply.lex.TOKEN(r"\n")
	def t_NEWLINE(self, t):
		self.lexer.lineno += 1
		return t
	
	t_ignore_WHITESPACE = r"[ \t]+"
	
	@ply.lex.TOKEN(_id)
	def t_IDENTIFIER(self, t):
		if t.value.lower() in RezLexer.keywords:
			t.type = t.value.upper()
		else:
			t.type = "IDENTIFIER"
		
		return t
	
	@ply.lex.TOKEN(r"\$\$"+_id)
	def t_REZ_FUNCTION(self, t):
		if t.value.lower() not in RezLexer.rez_functions:
			raise RezParserError("Unknown Rez function: " + t.value)
		
		t.type = "FUN_" + t.value[2:].upper()
		
		return t
	
	t_STRINGLIT_TEXT = r"\"(?:[^\\\"\n]|\\.)*\""
	t_STRINGLIT_HEX = r"\$\"[ \t]*(?:[0-9A-Fa-f][ \t]*[0-9A-Fa-f][ \t]*)*\""
	t_INTLIT_DEC = r"0|[1-9][0-9]*"
	t_INTLIT_HEX = r"\$|0[Xx][0-9A-Fa-f]+"
	t_INTLIT_OCT = r"0[0-7]+"
	t_INTLIT_BIN = r"0[Bb][01]+"
	t_INTLIT_CHAR = r"\'(?:[^\\\'\n]|\\.)*\'"
	
	t_SHIFTLEFT = r"<<"
	t_SHIFTRIGHT = r">>"
	t_EQUAL = r"=="
	t_NOTEQUAL = r"!="
	t_LESSEQUAL = r"<="
	t_GREATEREQUAL = r">="
	t_BOOLAND = r"&&"
	t_BOOLOR = r"\|\|"
	t_LBRACE = r"\{"
	t_RBRACE = r"\}"
	t_LBRACKET = r"\["
	t_RBRACKET = r"\]"
	t_LPAREN = r"\("
	t_RPAREN = r"\)"
	t_SEMICOLON = r";"
	t_COLON = r":"
	t_COMMA = r","
	t_ASSIGN = r"="
	t_PLUS = r"\+"
	t_MINUS = r"\-"
	t_MULTIPLY = r"\*"
	t_DIVIDE = r"/"
	t_MODULO = r"%"
	t_BITAND = r"&"
	t_BITOR = r"\|"
	t_BITXOR = r"\^"
	t_BITNOT = r"~"
	t_LESS = r"<"
	t_GREATER = r">"
	t_BOOLNOT = r"!"
	
	@property
	def lineno(self):
		try:
			return self.lexer.lineno
		except AttributeError:
			return 0
	
	@lineno.setter
	def lineno(self, lineno):
		self.lexer.lineno = lineno
	
	@property
	def lexpos(self):
		try:
			return self.lexer.lexpos
		except AttributeError:
			return 0
	
	@lexpos.setter
	def lexpos(self, lexpos):
		self.lexer.lexpos = lexpos
	
	def __init__(self, **kwargs):
		super().__init__()
		
		self.lexer = ply.lex.lex(module=self, **kwargs)
	
	def __iter__(self):
		return iter(self.token, None)
	
	def input(self, s):
		self.lexer.input(s.replace("\\\n", ""))
		return iter(self)
	
	def token(self):
		return self.lexer.token()


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


class RezPreprocessor(object):
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
	
	def __init__(self, lexer, *, parser=None, macros=None, derez=False, include_path=None):
		super().__init__()
		
		self.lexer = lexer
		self.parser = parser
		
		# Mapping of macro names (case-insensitive, all names must be passed through str.casefold) to lists of expansion tokens.
		self.macros = {
			"true": [Token("INTLIT_DEC", "1")],
			"false": [Token("INTLIT_DEC", "0")],
			"rez": [Token("INTLIT_DEC", "0" if derez else "1")],
			"derez": [Token("INTLIT_DEC", "1" if derez else "0")],
		}
		if macros is not None:
			self.macros.update(macros)
		
		# Sequence of directories to search for include files.
		self.include_path = include_path
		
		# Sequence of tokens that were produced by a macro expansion and not yet consumed.
		# Can also contain the string "expansion_end" to mark the end of a macro expansion, these markers are only used internally to track macro expansion depth and are otherwise ignored.
		self.expansion_queue = []
		
		# Current macro expansion depth. Is increased when a macro is expanded, and decreased when the corresponding "expansion_end" marker is hit. If this number grows too high, the preprocessor errors out.
		self.expansion_depth = 0
		
		# Sequence (stack) of strings representing the state of all conditional blocks enclosing the current block. Valid values are:
		# * "waiting": An inactive block in a chain where no active block has been found yet.
		# * "active": An active block, whose contents are processed.
		# * "done": A block in a chain where an active block has been found already.
		# * "outer_inactive": A block inside an inactive block.
		self.if_stack = []
		
		# The state of the current conditional block. Values are the same as for if_stack. Top-level code is considered to be in an "active" block.
		self.if_state = "active"
		
		# Set of include file names (unprocessed, including angle brackets or quotes, not full filesystem paths) that were previously used in an #import or #include directive and should not be included again when used as an argument to #import.
		self.included_files = set()
		
		# Current state of the enum declaration mini-parser. Valid values are:
		# * "inactive": Not inside any enum declaration.
		# * "enum": After the enum keyword.
		# * "type_name": After the (optional) enum type name.
		# * "next": At the start of the next enum constant declaration.
		# * "name": After the current enum constant name.
		# * "equals": After the equals sign preceding the explicit enum constant value (both optional).
		# * "value": After the explicit enum constant value.
		# * "end": After the closing enum declaration brace.
		self.enum_state = "inactive"
		
		# The value of the next enum constant in this declaration.
		self.enum_counter = 0
		
		# The name of the current enum constant.
		self.enum_constant_name = None
		
		# The tokens making up the explicit value of the current enum constant, if any.
		self.enum_constant_tokens = []
		
		# The parentesis nesting depth in the explicit value of the current enum constant, if any. (The value is terminated by a comma outside of any parentheses.)
		self.enum_constant_depth = 0
	
	def __iter__(self):
		return iter(self.token, None)
	
	def input(self, *args, **kwargs):
		self.lexer.input(*args, **kwargs)
	
	def _eval_expression(self, tokens):
		print(tokens)
		while True:
			try:
				return int(input("Please evaluate the above expression: "), base=0)
			except ValueError as err:
				print(err)
	
	def _token_internal(self, *, expand=True):
		while True:
			try:
				tok = self.expansion_queue.pop(0)
			except IndexError:
				tok = self.lexer.token()
			
			if tok is None:
				return tok
			elif tok == "expansion_end":
				self.expansion_depth -= 1
				continue
			elif tok.type == "IDENTIFIER" and self.if_state == "active" and expand:
				name = tok.value.casefold()
				try:
					self.expansion_depth += 1
					if self.expansion_depth > 100:
						raise PreprocessError("Maximum macro expansion depth exceeded (> 100)")
					self.expansion_queue += self.macros[name]
					self.expansion_queue.append("expansion_end")
				except KeyError:
					return tok
			else:
				return tok
	
	def token(self):
		while True:
			tok = self._token_internal()
			
			if tok is None:
				return None
			elif tok.type in ("PP_IF", "PP_ELIF"):
				if tok.type == "PP_ELIF" and not self.if_stack:
					raise PreprocessError(f"#elif outside of a conditional block: {tok}")
				
				if self.if_state == "outer_inactive":
					if tok.type == "PP_IF":
						self.if_stack.append("outer_inactive")
					continue
				
				cond_tokens = []
				cond_token = self._token_internal()
				while cond_token.type not in ("NEWLINE", "SEMICOLON"):
					if cond_token.type == "DEFINED":
						cond_token = self._token_internal(expand=False)
						if cond_token.type == "LPAREN":
							cond_token = self._token_internal(expand=False)
							if cond_token.type == "IDENTIFIER" or cond_token.type.lower() in RezLexer.keywords:
								macro = cond_token.value
							else:
								raise PreprocessError(f"Expected identifier in defined expression parentheses, not {cond_token}")
							cond_token = self._token_internal(expand=False)
							if cond_token.type != "RPAREN":
								raise PreprocessError(f"Expected ')' after defined expression identifier, not {cond_token}")
						elif cond_token.type == "IDENTIFIER" or cond_token.type.lower() in RezLexer.keywords:
							macro = cond_token.value
						else:
							raise PreprocessError(f"Expected '(' or identifier after defined, not {cond_token}")
						
						cond_token = Token("INTLIT_DEC", str(int(macro.casefold() in self.macros)), cond_token.lineno, cond_token.lexpos)
					
					cond_tokens.append(cond_token)
					cond_token = self._token_internal()
				
				cond = bool(self._eval_expression(cond_tokens))
				
				if tok.type == "PP_IF":
					self.if_stack.append(self.if_state)
					self.if_state = "active" if cond else "waiting"
				elif self.if_state == "waiting" and cond:
					self.if_state = "active"
			elif tok.type == "PP_IFDEF":
				cond = (tok.pp_ifdef_name.casefold() in self.macros) ^ (tok.pp_ifdef_type == "ifndef")
				self.if_stack.append(self.if_state)
				if self.if_stack[-1] != "active":
					self.if_state = "outer_inactive"
				elif cond:
					self.if_state = "active"
				else:
					self.if_state = "waiting"
			elif tok.type == "PP_ELSE":
				if not self.if_stack:
					raise PreprocessError(f"#else outside of a conditional block: {tok}")
				
				if self.if_state == "outer_inactive":
					pass
				elif self.if_state == "waiting":
					self.if_state = "active"
				else:
					self.if_state = "done"
			elif tok.type == "PP_ENDIF":
				if not self.if_stack:
					raise PreprocessError(f"#endif outside of a conditional block: {tok}")
				
				self.if_state = self.if_stack.pop()
			elif self.if_state != "active" or tok.type in ("NEWLINE", "PP_EMPTY"):
				continue
			elif tok.type == "PP_DEFINE":
				self.macros[tok.pp_define_name.casefold()] = tok.pp_define_value
			elif tok.type == "PP_UNDEF":
				self.macros.pop(tok.pp_undef_name.casefold(), None)
			elif tok.type == "PP_INCLUDE":
				#TODO
				print(f"Warning: #include and #import are not yet implemented, ignoring: {tok}")
			elif tok.type == "PP_PRINTF":
				#TODO
				print(f"Warning: #printf is not yet implemented, ignoring: {tok}")
				while tok.type not in ("NEWLINE", "SEMICOLON"):
					tok = self._token_internal()
			elif tok.type == "ENUM":
				if self.enum_state != "inactive":
					raise PreprocessError(f"Invalid nested enum: {tok}")
				
				self.enum_state = "enum"
				self.enum_counter = 0
				return tok
			elif self.enum_state != "inactive":
				if self.enum_state == "enum":
					if tok.type == "IDENTIFIER":
						self.enum_state = "type_name"
					elif tok.type == "LBRACE":
						self.enum_state = "next"
					else:
						raise PreprocessError(f"Expected identifier or '{{', not {tok}")
				elif self.enum_state == "type_name":
					if tok.type == "LBRACE":
						self.enum_state = "next"
					else:
						raise PreprocessError(f"Expected '{{', not {tok}")
				elif self.enum_state == "next":
					if tok.type == "IDENTIFIER":
						self.enum_constant_name = tok.value.casefold()
						self.enum_state = "name"
					elif tok.type == "RBRACE":
						self.enum_state = "end"
					else:
						raise PreprocessError(f"Expected identifier or '{{', not {tok}")
				elif self.enum_state == "name":
					if tok.type == "ASSIGN":
						self.enum_state = "equals"
						self.enum_constant_tokens = []
						self.enum_constant_depth = 0
					elif tok.type in ("COMMA", "RBRACE"):
						self.macros[self.enum_constant_name] = [Token("INTLIT_DEC", str(self.enum_counter), tok.lineno, tok.lexpos)]
						if tok.type == "COMMA":
							self.enum_counter += 1
							self.enum_state = "next"
						else:
							self.enum_state = "end"
					else:
						raise PreprocessError(f"Expected '=', ',' or '}}', not {tok}")
				elif self.enum_state == "equals":
					if tok.type == "COMMA" and self.enum_constant_depth == 0:
						self.enum_counter = self._eval_expression(self.enum_constant_tokens)
						self.macros[self.enum_constant_name] = [Token("INTLIT_DEC", str(self.enum_counter), tok.lineno, tok.lexpos)]
						self.enum_counter += 1
						self.enum_state = "next"
					else:
						self.enum_constant_tokens.append(tok)
						if tok.type in ("LPAREN", "LBRACKET", "LBRACE"):
							self.enum_constant_depth += 1
						elif tok.type in ("RPAREN", "RBRACKET", "RBRACE"):
							self.enum_constant_depth -= 1
				elif self.enum_state == "value":
					if tok.type == "COMMA":
						self.enum_counter += 1
						self.enum_state = "next"
					elif tok.type == "RBRACE":
						self.enum_state = "end"
					else:
						raise PreprocessError(f"Expected ',' or '}}', not {tok}")
				elif self.enum_state == "end":
					if tok.type == "SEMICOLON":
						self.enum_state = "inactive"
						self.enum_counter = 0
						self.enum_constant_name = None
						self.enum_constant_tokens = []
						self.enum_constant_depth = 0
					else:
						raise PreprocessError(f"Expected ';', not {tok}")
				return tok
			else:
				return tok


# noinspection PyMethodMayBeStatic, PyPep8Naming
class RezParser(object):
	"""Rez preprocessor and parser, based on the description and syntax given in Appendix C, "The Rez Language", in "Building and Managing Programs in MPW, 2nd Edition".
	This file can for example be found on Max1zzz's server "www.max1zzz.co.uk", at location "/%2BMac OS Classic/Programming/Macintosh Programmers Workshop/MPW (2001)/Documentation/MPW_Reference/Building_Progs_in_MPW.sit".
	The server can be accessed via a web interface ("http://www.max1zzz.co.uk:8000", username "mg", password "mg"), or via FTP ("ftp://www.max1zzz.co.uk:21", username "mg", password "mg"), or via one of the other methods listed at "http://max1zzz.co.uk/servers.html".
	"""
	
	def __init__(self, lexer=None, preprocess=True, **kwargs):
		super().__init__()
		
		if lexer is None:
			lexer = RezLexer()
		
		lexer = self.manual_lexer = NoOpLexer(lexer)
		
		if preprocess:
			lexer = RezPreprocessor(lexer, parser=self)
		
		self.lexer = lexer
		self.parser_file = ply.yacc.yacc(module=self, start="start_file", tabmodule="parsetab_file", debugfile="parser_file.out", **kwargs)
		self.parser_expr = ply.yacc.yacc(module=self, start="start_expr", tabmodule="parsetab_expr", debugfile="parser_expr.out", **kwargs)
		self.parser_file.parse("", self.lexer)
		self.parser_expr.parse("0", self.lexer)
	
	def parse_file(self, inp, **kwargs):
		self.parser_file.restart()
		return self.parser_file.parse(inp, self.lexer, **kwargs)
	
	def parse_expr(self, inp, **kwargs):
		self.parser_expr.restart()
		return self.parser_expr.parse(inp, self.lexer, **kwargs)
	
	tokens = RezLexer.tokens
	
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


def main():
	with open(sys.argv[1], "r") as f:
		text = f.read()
	
	lexer = RezLexer(debug=True)
	parser = RezParser(lexer, debug=True)
	
	print(parser.parse_file(text, debug=True, tracking=True))

if __name__ == "__main__":
	main()
