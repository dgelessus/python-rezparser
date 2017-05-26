import collections.abc
import datetime
import typing

from . import ast
from . import __version__ as _rezparser_version

__all__ = [
	"REZ_VERSION",
	"ArrayState",
	"Evaluator",
	"ResourceState",
	"eval",
]

# Not a real Rez version number. Xcode 8.4's Rez and DeRez say "V3.7B1".
REZ_VERSION = b"python-rezparser version " + _rezparser_version.encode("ascii", errors="backslashreplace")

class ArrayState(object):
	name: typing.Optional[str]
	arrayindex: int
	countof: int
	parent: typing.Optional["ArrayState"]
	
	def __init__(self, *, name, arrayindex, countof, parent):
		super().__init__()
		
		self.name = name
		self.arrayindex = arrayindex
		self.countof = countof
		self.parent = parent

class ResourceState(object):
	type: int
	id: int
	name: bytes
	attributes: int
	data: bytes
	
	def __init__(self, *, type, id, name, attributes, data):
		super().__init__()
		
		self.type = type
		self.id = id
		self.name = name
		self.attributes = attributes
		self.data = data

class Evaluator(object):
	symbols: typing.Mapping[str, object]
	arrays: typing.Mapping[str, ArrayState]
	current_resource: typing.Optional[ResourceState]
	current_datetime: datetime.datetime
	rez_version: bytes
	
	def __init__(self, *, symbols=None, arrays=None, current_resource=None, current_datetime=None, rez_version=None):
		super().__init__()
		
		self.symbols = {} if symbols is None else symbols
		self.arrays = {} if arrays is None else arrays
		self.current_resource = current_resource
		self.current_datetime = datetime.datetime.utcfromtimestamp(0) if current_datetime is None else current_datetime
		self.rez_version = REZ_VERSION if rez_version is None else rez_version
	
	def eval_arrayindex(self, array_name):
		return self.arrays[array_name].arrayindex
	
	def eval_attributes(self):
		return 0 if self.current_resource is None else self.current_resource.attributes
	
	def eval_bitfield(self, start, offset, length):
		startbyte, startbit = divmod(start + offset, 8)
		endbyte, endbit = divmod(start + offset + length, 8)
		mask = (1 << length) - 1
		num = int.from_bytes(self.current_resource.data[startbyte:endbyte + 1], "big", signed=False) >> (8 - endbit) & mask
		
		if num > mask//2:
			num -= mask
		
		return num
	
	def eval_byte(self, start):
		return self.eval_bitfield(start, 0, 8)
	
	def eval_countof(self, array_name):
		return self.arrays[array_name].countof
	
	def eval_date(self):
		# This is not an accurate implementation.
		# The real $$Date internally calls the Toolbox IUDateString procedure (now the DateString function from CarbonCore/DateTimeUtils.h), which is locale-dependent and doesn't follow any standard that can be easily emulated.
		return f"{self.current_datetime.date()}"
	
	def eval_day(self):
		return self.current_datetime.day
	
	def eval_format(self, format, *args):
		raise NotImplementedError() # TODO
	
	def eval_hour(self):
		return self.current_datetime.hour
	
	def eval_id(self):
		return 0 if self.current_resource is None else self.current_resource.id
	
	def eval_long(self, start):
		return self.eval_bitfield(start, 0, 32)
	
	def eval_minute(self):
		return self.current_datetime.minute
	
	def eval_month(self):
		return self.current_datetime.month
	
	def eval_name(self):
		return b"" if self.current_resource is None else self.current_resource.name
	
	def eval_packedsize(self, start, row_bytes, row_count):
		raise NotImplementedError() # TODO
	
	def eval_read(self, path):
		# This is not implemented by default, to prevent Rez code from accessing arbitrary parts of the filesystem.
		raise NotImplementedError()
	
	def eval_resource(self, path, type, id, name):
		# This is not implemented by default, for the same reason as eval_read, and because it would require an understanding of the resource fork format. (See https://github.com/dgelessus/python-rsrcfork.)
		raise NotImplementedError()
	
	def eval_resourcesize(self):
		return 0 if self.current_resource is None else len(self.current_resource.data)
	
	def eval_second(self):
		return self.current_datetime.second
	
	def eval_shell(self, name):
		# This is not implemented by default, to prevent Rez code from accessing arbitrary environment variables.
		raise NotImplementedError()
	
	def eval_time(self):
		# This is not an accurate implementation.
		# The real $$Time internally calls the Toolbox IUTimeString procedure (now the TimeString function from CarbonCore/DateTimeUtils.h), which is locale-dependent and doesn't follow any standard that can be easily emulated.
		return f"{self.current_datetime.time()}"
	
	def eval_type(self):
		return 0 if self.current_resource is None else self.current_resource.type
	
	def eval_version(self):
		return self.rez_version
	
	def eval_weekday(self):
		# datetime.datetime.weekday() returns an integer between 0 and 6, where 0 is Monday and 6 is Sunday.
		# Rez $$Weekday returns an integer between 1 and 7, where 1 is Sunday and 6 is Saturday.
		# So we need to perform this ugly conversion here.
		return (self.current_datetime.weekday() + 1) % 7 + 1
	
	def eval_word(self, start):
		return self.eval_bitfield(start, 0, 16)
	
	def eval_year(self):
		return self.current_datetime.year
	
	def eval_label_subscript(self, name, subscripts):
		try:
			value = self.symbols[name]
		except KeyError:
			raise ValueError(f"Cannot evaluate subscript of unknown label {name!r}")
		
		for s in subscripts:
			try:
				value = value[s-1]
			except TypeError:
				raise ValueError(f"Too many subscripts for label {name!r}")
		
		if isinstance(value, collections.abc.Sequence):
			raise ValueError(f"Too few subscripts for label {name!r}")
		
		return value
	
	def eval(self, expr):
		if not isinstance(expr, ast.ResourceValue):
			raise TypeError(f"Expression must be an rezparser.ast.ResourceValue, not a {type(expr).__module__}.{type(expr).__qualname__}")
		
		if isinstance(expr, ast.Symbol):
			try:
				value = self.symbols[expr.name]
			except KeyError:
				raise ValueError(f"Cannot evaluate unknown symbol {expr.name!r}")
			
			if isinstance(value, collections.abc.Sequence) and not isinstance(value, bytes):
				raise ValueError(f"Missing subscript on label {expr.name!r}")
			
			return value
		elif isinstance(expr, ast.IntExpression):
			if isinstance(expr, ast.IntLiteral):
				return expr.value
			elif isinstance(expr, ast.ResourceAttribute):
				return expr.value.value
			elif isinstance(expr, ast.LabelSubscript):
				return self.eval_label_subscript(expr.name, expr.subscripts)
			elif isinstance(expr, ast.IntUnaryOp):
				value = self.eval(expr.value)
				if isinstance(expr, ast.Negative):
					return -value
				elif isinstance(expr, ast.BoolNot):
					return int(not value)
				elif isinstance(expr, ast.BitNot):
					return ~value
			elif isinstance(expr, ast.IntBinaryOp):
				left = self.eval(expr.left)
				# Check for && and || first, whose right side can be lazily evaluated.
				if isinstance(expr, ast.BoolAnd):
					return left and self.eval(expr.right)
				elif isinstance(expr, ast.BoolOr):
					return left or self.eval(expr.right)
				
				# Other operators cannot be evaluated lazily, so it's okay to evaluate the right side here.
				right = self.eval(expr.right)
				if isinstance(expr, ast.Multiply):
					return left * right
				elif isinstance(expr, ast.Divide):
					# Rez division rounds towards zero (unlike Python floor division).
					# The sign of the divisor is ignored.
					# Division by zero is an error in Rez and Python.
					return -(-left // abs(right)) if left < 0 else left // abs(right)
				elif isinstance(expr, ast.Modulo):
					# Rez modulo ignores both signs and then copies the left value's sign to the result.
					return -(-left % abs(right)) if left < 0 else left % abs(right)
				elif isinstance(expr, ast.Add):
					return left + right
				elif isinstance(expr, ast.Subtract):
					return left - right
				elif isinstance(expr, ast.BitShiftLeft):
					return 0 if right < 0 else left << right
				elif isinstance(expr, ast.BitShiftRight):
					return 0 if right < 0 else left >> right
				elif isinstance(expr, ast.LessThan):
					return int(left < right)
				elif isinstance(expr, ast.GreaterThan):
					return int(left > right)
				elif isinstance(expr, ast.LessThanEqual):
					return int(left <= right)
				elif isinstance(expr, ast.GreaterThanEqual):
					return int(left >= right)
				elif isinstance(expr, ast.Equal):
					return int(left == right)
				elif isinstance(expr, ast.NotEqual):
					return int(left != right)
				elif isinstance(expr, ast.BitAnd):
					return left & right
				elif isinstance(expr, ast.BitOr):
					return left | right
				elif isinstance(expr, ast.BitXor):
					return left ^ right
			elif isinstance(expr, ast.IntFunction):
				if isinstance(expr, ast.FunArrayIndex):
					return self.eval_arrayindex(expr.array_name)
				elif isinstance(expr, ast.FunAttributes):
					return self.eval_attributes()
				elif isinstance(expr, ast.FunBitField):
					return self.eval_bitfield(self.eval(expr.start), self.eval(expr.offset), self.eval(expr.length))
				elif isinstance(expr, ast.FunByte):
					return self.eval_byte(self.eval(expr.start))
				elif isinstance(expr, ast.FunCountOf):
					return self.eval_countof(expr.array_name)
				elif isinstance(expr, ast.FunDay):
					return self.eval_day()
				elif isinstance(expr, ast.FunHour):
					return self.eval_hour()
				elif isinstance(expr, ast.FunID):
					return self.eval_id()
				elif isinstance(expr, ast.FunLong):
					return self.eval_long(self.eval(expr.start))
				elif isinstance(expr, ast.FunMinute):
					return self.eval_minute()
				elif isinstance(expr, ast.FunMonth):
					return self.eval_month()
				elif isinstance(expr, ast.FunPackedSize):
					return self.eval_packedsize(self.eval(expr.start), self.eval(expr.row_bytes), self.eval(expr.row_count))
				elif isinstance(expr, ast.FunResourceSize):
					return self.eval_resourcesize()
				elif isinstance(expr, ast.FunSecond):
					return self.eval_second()
				elif isinstance(expr, ast.FunType):
					return self.eval_type()
				elif isinstance(expr, ast.FunWeekday):
					return self.eval_weekday()
				elif isinstance(expr, ast.FunWord):
					return self.eval_word(self.eval(expr.start))
				elif isinstance(expr, ast.FunYear):
					return self.eval_year()
		elif isinstance(expr, ast.StringExpression):
			if isinstance(expr, ast.StringLiteral):
				return expr.value
			elif isinstance(expr, ast.StringConcat):
				return b"".join(self.eval(value) for value in expr.values)
			elif isinstance(expr, ast.StringFunction):
				if isinstance(expr, ast.FunDate):
					return self.eval_date()
				elif isinstance(expr, ast.FunFormat):
					return self.eval_format(self.eval(expr.format), *(self.eval(arg) for arg in expr.args))
				elif isinstance(expr, ast.FunName):
					return self.eval_name()
				elif isinstance(expr, ast.FunRead):
					return self.eval_read(self.eval(expr.path))
				elif isinstance(expr, ast.FunResource):
					return self.eval_resource(self.eval(expr.path), self.eval(expr.type), self.eval(expr.id), self.eval(expr.name))
				elif isinstance(expr, ast.FunShell):
					return self.eval_shell(expr.name)
				elif isinstance(expr, ast.FunTime):
					return self.eval_time()
				elif isinstance(expr, ast.FunVersion):
					return self.eval_version()
		
		raise ValueError(f"Don't know how to evaluate: {expr}")
