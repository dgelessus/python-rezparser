import ply.lex

from . import common

__all__ = [
	"LexError",
	"RezLexer",
]

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


class LexError(common.RezParserError):
	__slots__ = ()


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
			raise LexError("Unknown Rez function: " + t.value)
		
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
		
		self.lexer = ply.lex.lex(module=self, lextab="_table_lexer", **kwargs)
	
	def __iter__(self):
		return iter(self.token, None)
	
	def input(self, s):
		self.lexer.input(s.replace("\\\n", ""))
		return iter(self)
	
	def token(self):
		return self.lexer.token()