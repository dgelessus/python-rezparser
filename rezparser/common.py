import functools

import ply.lex

__all__ = [
	"RezParserError",
	"Token",
]


STRING_ENCODING = "macroman"


class RezParserError(Exception):
	__slots__ = ("message", "filename", "lineno")
	
	def __init__(self, message, *, filename=None, lineno=None):
		full_message = str(message)
		
		if filename is not None:
			full_message += f", in file {filename!r}"
		
		if lineno is not None:
			full_message += f", on line {lineno}"
		
		super().__init__(full_message)
		
		self.message = message
		self.filename = filename
		self.lineno = lineno


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
