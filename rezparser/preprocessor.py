from . import common
from . import lexer

__all__ = [
	"PreprocessError",
	"RezPreprocessor",
]


# NOTE: The meanings of the control characters "\r" and "\n" are reversed in Rez. For example, in $$read input and #printf output, all "\r" are replaced with "\n" and vice versa. This is because the line ending on classic Mac OS was "\r", and on Unix (including OS X) is "\n".

# NOTE: Rez "preprocessor" directives may look similar to the standard C preprocessor, but there are more advanced cases where the two are very different. The Rez "preprocessor directives" are actually closely integrated with the language, and can't easily be processed without understanding the language semantics. This requires some unusual parsing techniques below, and some very odd corner cases might not be handled correctly.
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

class PreprocessError(common.RezParserError):
	__slots__ = ()


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
			"true": [common.Token("INTLIT_DEC", "1")],
			"false": [common.Token("INTLIT_DEC", "0")],
			"rez": [common.Token("INTLIT_DEC", "0" if derez else "1")],
			"derez": [common.Token("INTLIT_DEC", "1" if derez else "0")],
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
							if cond_token.type == "IDENTIFIER" or cond_token.type.lower() in lexer.RezLexer.keywords:
								macro = cond_token.value
							else:
								raise PreprocessError(f"Expected identifier in defined expression parentheses, not {cond_token}")
							cond_token = self._token_internal(expand=False)
							if cond_token.type != "RPAREN":
								raise PreprocessError(f"Expected ')' after defined expression identifier, not {cond_token}")
						elif cond_token.type == "IDENTIFIER" or cond_token.type.lower() in lexer.RezLexer.keywords:
							macro = cond_token.value
						else:
							raise PreprocessError(f"Expected '(' or identifier after defined, not {cond_token}")
						
						cond_token = common.Token("INTLIT_DEC", str(int(macro.casefold() in self.macros)), cond_token.lineno, cond_token.lexpos)
					
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
						self.macros[self.enum_constant_name] = [common.Token("INTLIT_DEC", str(self.enum_counter), tok.lineno, tok.lexpos)]
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
						self.macros[self.enum_constant_name] = [common.Token("INTLIT_DEC", str(self.enum_counter), tok.lineno, tok.lexpos)]
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