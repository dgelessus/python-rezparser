import ply.lex

from . import common

__all__ = [
	"LexError",
	"NoOpLexer",
	"RezLexer",
]

class LexError(common.RezParserError):
	__slots__ = ()


class NoOpLexer(object):
	@property
	def lineno(self):
		if self.lexer is None:
			return self._lineno
		else:
			return self.lexer.lineno
	
	@lineno.setter
	def lineno(self, lineno):
		if self.lexer is None:
			self._lineno = lineno
		else:
			self.lexer.lineno = lineno
	
	@property
	def lexpos(self):
		if self.lexer is None:
			return self._lexpos
		else:
			return self.lexer.lexpos
	
	@lexpos.setter
	def lexpos(self, lexpos):
		if self.lexer is None:
			self._lexpos = lexpos
		else:
			self.lexer.lexpos = lexpos
	
	@property
	def filename(self):
		if self.lexer is None:
			return self._filename
		else:
			return self.lexer.filename
	
	@filename.setter
	def filename(self, filename):
		if self.lexer is None:
			self._filename = filename
		else:
			self.lexer.filename = filename
	
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
			if self.lexer is None:
				return None
			else:
				return self.lexer.token()
	
	def clone(self):
		cloned = NoOpLexer(None if self.lexer is None else self.lexer.clone())
		for attr in ("_lineno", "_lexpos", "_filename"):
			try:
				setattr(cloned, attr, getattr(self, attr))
			except AttributeError:
				pass
		cloned.input(self.tokens)
		return cloned


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
		"int",
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
		try:
			newline_pos = t.value.index("\n", 1)
		except ValueError:
			newline_pos = len(t.value)
		
		raise LexError(repr(t.value[:newline_pos]), filename=self.filename, lineno=self.lineno)
	
	_pp = r"(?m:^)[ \t]*\#[ \t]*"
	_id = r"[A-Za-z_][A-Za-z0-9_]*"
	_filename = r"(?:\"(?:[^\\\"\n]|\\.)*\"[ \t]*|[^\";\n])+"
	
	t_ignore_COMMENT_SINGLE = r"//[^\n]*"
	t_ignore_COMMENT_MULTI = r"(?s:/\*.*?\*/)"
	
	# NOTE: Some of the patterns for preprocessor directives are a bit unusual, because of certain quirks in the Rez "preprocessor" language. See the comments in preprocessor.py for details.
	
	@ply.lex.TOKEN(_pp+r"(?:include|import)[ \t]*"+_filename+r";?.*")
	def t_PP_INCLUDE(self, t):
		t = common.Token(t)
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
		t = common.Token(t)
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
		t = common.Token(t)
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
		t = common.Token(t)
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
	
	t_PP_ELSE = _pp+r"else[^A-Za-z_\n]?.*"
	t_PP_ENDIF = _pp+r"endif[^A-Za-z_\n]?.*"
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
			raise LexError("Unknown Rez function: " + t.value, filename=self.filename, lineno=self.lineno)
		
		t.type = "FUN_" + t.value[2:].upper()
		
		return t
	
	t_STRINGLIT_TEXT = r"\"(?:[^\\\"\n]|\\.)*\""
	t_STRINGLIT_HEX = r"\$\"[ \t]*(?:[0-9A-Fa-f][ \t]*[0-9A-Fa-f][ \t]*)*\""
	
	# These tokens are defined using methods instead of plain strings to enforce precedence.
	# The decimal int literal MUST come last, to prevent the leading zeros of the other int literals from being considered a separate decimal literal.
	
	@ply.lex.TOKEN(r"(?:\$|0[Xx])[0-9A-Fa-f]+")
	def t_INTLIT_HEX(self, t):
		return t
	
	@ply.lex.TOKEN(r"0[Bb][01]+")
	def t_INTLIT_BIN(self, t):
		return t
	
	@ply.lex.TOKEN(r"0[0-7]+")
	def t_INTLIT_OCT(self, t):
		return t
	
	@ply.lex.TOKEN(r"0|[1-9][0-9]*")
	def t_INTLIT_DEC(self, t):
		return t
	
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
	
	@property
	def filename(self):
		try:
			return self.lexer.filename
		except AttributeError:
			return None
	
	@filename.setter
	def filename(self, filename):
		self.lexer.filename = filename
	
	def __init__(self, *, filename="<input>", _lexer=None, **kwargs):
		super().__init__()
		
		if _lexer is None:
			self.lexer = ply.lex.lex(module=self, lextab="_table_lexer", **kwargs)
			self.filename = filename
		else:
			self.lexer = _lexer
	
	def __iter__(self):
		return iter(self.token, None)
	
	def input(self, s):
		self.lexer.input(s.replace("\\\n", ""))
		return iter(self)
	
	def token(self):
		return self.lexer.token()
	
	def clone(self):
		new_lexer = RezLexer(_lexer=self.lexer.clone())
		new_lexer.filename = self.filename
		return new_lexer
