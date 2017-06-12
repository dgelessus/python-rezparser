import enum
import typing

class Node(object):
	"""Base class of all AST nodes. Provides a convenient __init__ and __repr__."""
	
	def __init__(self, **kwargs):
		"""Create a node and set all keyword arguments as attributes."""
		
		super().__init__()
		
		for name, value in kwargs.items():
			setattr(self, name, value)
	
	def __repr__(self):
		names = []
		for tp in reversed(type(self).__mro__):
			try:
				anns = tp.__dict__["__annotations__"]
			except KeyError:
				pass
			else:
				names.extend(anns)
		
		attrs = []
		for name in names:
			try:
				attrs.append(f"{name}={getattr(self, name)!r}")
			except AttributeError:
				pass
		
		return f"{type(self).__qualname__}({', '.join(attrs)})"

class ResourceValue(Node):
	"""Base class of all resource values, i. e. anything that can appear as a field value within a resource statement."""

class Symbol(ResourceValue):
	"""A symbol use whose type is not known."""
	
	name: str

class Expression(ResourceValue):
	"""Base class of all "simple" expressions (ints or strings)."""

class IntExpression(Expression):
	"""Base class of all int expressions."""

class IntLiteral(IntExpression):
	"""An int literal, including numeric literals of any base, and character literals.
	The boolean "literals" true and false are standard macros defined to 1 and 0, so they are also considered int literals.
	"""
	
	value: int

class ResourceAttribute(IntExpression):
	"""A resource attribute.
	May appear in a ResourceSpecDef, or standalone as an IntExpression.
	"""
	
	class Value(enum.Enum):
		none = 0
		compressed = 1
		uncompressed = 0
		changed = 2
		unchanged = 0
		preload = 4
		nonpreload = 0
		protected = 8
		unprotected = 0
		locked = 16
		unlocked = 0
		purgeable = 32
		nonpurgeable = 0
		sysheap = 64
		appheap = 0
	
	value: Value

class IntSymbol(IntExpression, Symbol):
	"""A symbol use that is known to be an int, based on its context."""

class LabelSubscript(IntExpression):
	"""A label with one or more subscripts, as used with labels defined inside one or more arrays.
	Note that a label without any subscripts is represented as an IntSymbol, and not as a LabelSubscript.
	"""
	
	name: str
	subscripts: typing.Sequence[IntExpression]

class IntFunction(IntExpression):
	"""Base class for all Rez functions that return an int."""

class FunArrayIndex(IntFunction):
	"""An $$ArrayIndex(array_name) function call."""
	
	array_name: str

class FunAttributes(IntFunction):
	"""An $$Attributes function call."""

class FunBitField(IntFunction):
	"""A $$BitField(start, offset, length) function call."""
	
	start: int
	offset: int
	length: int

class FunByte(IntFunction):
	"""A $$Byte(start) function call."""
	
	start: int

class FunCountOf(IntFunction):
	"""A $$CountOf(array_name) function call."""
	
	array_name: str

class FunDay(IntFunction):
	"""A $$Day function call."""

class FunHour(IntFunction):
	"""A $$Hour function call."""

class FunID(IntFunction):
	"""An $$ID function call."""

class FunLong(IntFunction):
	"""A $$Long(start) function call."""
	
	start: int

class FunMinute(IntFunction):
	"""A $$Minute function call."""

class FunMonth(IntFunction):
	"""A $$Month function call."""

class FunPackedSize(IntFunction):
	"""A $$PackedSize(start, row_bytes, row_count) function call."""
	
	start: int
	row_bytes: int
	row_count: int

class FunResourceSize(IntFunction):
	"""A $$ResourceSize function call."""

class FunSecond(IntFunction):
	"""A $$Second function call."""

class FunType(IntFunction):
	"""A $$Type function call."""

class FunWeekday(IntFunction):
	"""A $$Weekday function call."""

class FunWord(IntFunction):
	"""A $$Word(start) function call."""
	
	start: int

class FunYear(IntFunction):
	"""A $$Year function call."""

class IntUnaryOp(IntExpression):
	"""Base class for all unary int operators."""
	
	value: IntExpression

class Negative(IntUnaryOp):
	"""A negation (-value)."""

class BoolNot(IntUnaryOp):
	"""A boolean not operation (!value)."""

class BitNot(IntUnaryOp):
	"""A bitwise not operation (~value)."""

class IntBinaryOp(IntExpression):
	"""Base class for all binary int operators."""
	
	left: IntExpression
	right: IntExpression

class Multiply(IntBinaryOp):
	"""A multiplication (left * right)."""

class Divide(IntBinaryOp):
	"""A division (left / right)."""

class Modulo(IntBinaryOp):
	"""A modulo operation (left % right)."""

class Add(IntBinaryOp):
	"""An addition (left + right)."""

class Subtract(IntBinaryOp):
	"""A subtraction (left - right)."""

class BitShiftLeft(IntBinaryOp):
	"""A left bit shift (left << right)."""

class BitShiftRight(IntBinaryOp):
	"""A right bit shift (left >> right)."""

class LessThan(IntBinaryOp):
	"""A less than comparison (left < right)."""

class GreaterThan(IntBinaryOp):
	"""A greater than comparison (left > right)."""

class LessThanEqual(IntBinaryOp):
	"""A less than or equal comparison (left <= right)."""

class GreaterThanEqual(IntBinaryOp):
	"""A greater than or equal comparison (left >= right)."""

class Equal(IntBinaryOp):
	"""An equality comparison (left == right)."""

class NotEqual(IntBinaryOp):
	"""An inequality comparison (left != right)."""

class BitAnd(IntBinaryOp):
	"""A bitwise and operation (left & right)."""

class BitXor(IntBinaryOp):
	"""A bitwise exclusive or operation (left ^ right)."""

class BitOr(IntBinaryOp):
	"""A bitwise or operation (left | right)."""

class BoolAnd(IntBinaryOp):
	"""A boolean and operation (left && right)."""

class BoolOr(IntBinaryOp):
	"""A boolean or operation (left || right)."""

class StringExpression(Expression):
	"""Base class for all string expressions."""

class StringLiteral(StringExpression):
	"""A string literal, in text or hexadecimal form.
	Note that adjacent string literals are not joined automatically, they are instead represented as a StringConcat operation.
	"""
	
	value: bytes

class StringSymbol(StringExpression, Symbol):
	"""A symbol use that is known to be a string, based on its context."""

class StringConcat(StringExpression):
	"""A concatenation of multiple string expressions."""
	
	values: typing.Sequence[StringExpression]

class StringFunction(StringExpression):
	"""Base class for all Rez functions that return a string."""

class FunDate(StringFunction):
	"""A $$Date function call."""

class FunFormat(StringFunction):
	"""A $$Format(format, ...args) function call."""
	
	format: StringExpression
	args: typing.Sequence[Expression]

class FunName(StringFunction):
	"""A $$Name function call."""

class FunRead(StringFunction):
	"""A $$Read(path) function call."""
	
	path: StringExpression

class FunResource(StringFunction):
	"""A $$Resource(path, type, id, name) function call."""
	
	path: StringExpression
	type: IntExpression
	id: IntExpression
	name: StringExpression

class FunShell(StringFunction):
	"""A $$Shell(name) function call."""
	
	name: StringExpression

class FunTime(StringFunction):
	"""A $$Time function call."""

class FunVersion(StringFunction):
	"""A $$Version function call."""

class ArrayValue(ResourceValue):
	"""An array value.
	The values are a two-dimensional sequence. The outer sequence contains groups of values (separated by semicolons), and the inner sequences contain the values in each group (separated by commas).
	These groups do not always correspond exactly to array iterations. One group may contain one or more array iterations, but an array iteration must not be split over multiple groups.
	That is, a semicolon may be added at most once at the end of an array iteration (and nowhere else), but is not required in most cases.
	"""
	
	values: typing.Sequence[typing.Sequence[ResourceValue]]

class SwitchValue(ResourceValue):
	"""A switch value."""
	
	label: str
	values: typing.Sequence[ResourceValue]

class IDRange(Node):
	"""A resource ID range from begin to end (both inclusive)."""
	
	begin: IntExpression
	end: IntExpression

class ResourceSpecTypeDef(Node):
	"""A resource spec used when defining a resource type.
	The type is required.
	The ID is optional and may be a single ID (as an int expression) or an ID range. If present, the type definition only applies to resources with a matching ID. Otherwise the type definition applies to all resources with the given type.
	"""
	
	type: IntExpression
	id: typing.Optional[typing.Union[IntExpression, IDRange]]

class ResourceSpecTypeUse(Node):
	"""A resource spec used when referring to an existing resource type declaration.
	The type is required.
	The ID is optional. If present, the type definition restricted to this ID (or a range containing it) is used. Otherwise, the unrestricted type definition is used.
	"""
	
	type: IntExpression
	id: typing.Optional[IntExpression]

class ResourceSpecDef(Node):
	"""A resource spec used when defining a resource.
	The type and ID are required.
	The name is optional, if omitted it defaults to an empty string.
	The attributes are required and may be a (possibly empty) sequence of resource attributes or any int expression. If a sequence of attributes is given, they are combined using bitwise or. If an int expression is given, it is used literally.
	"""
	
	type: IntExpression
	id: IntExpression
	name: typing.Optional[StringExpression]
	attributes: typing.Union[typing.Sequence[ResourceAttribute], IntExpression]

class ResourceSpecUse(Node):
	"""A resource spec used when referring to one or more existing resources.
	The type is required.
	id_or_name is optional and may be a single ID (as an int expression), an ID range, or a name. If present, only the resources with a matching ID or name are used. Otherwise all resources with the given type are used.
	"""
	
	type: IntExpression
	id_or_name: typing.Optional[typing.Union[IntExpression, IDRange, StringExpression]]

class Statement(Node):
	"""Base class for all top-level statements in a file."""

class Change(Statement):
	"""A change statement.
	The from_spec is required and specifies the resources to change.
	The to_spec is required and specifies what type, ID, name and attributes the resources should be changed to.
	"""
	
	from_spec: ResourceSpecUse
	to_spec: ResourceSpecDef

class Data(Statement):
	"""A data statement.
	The spec is required and specifies the type, ID, name and attributes of the resource.
	The value is optional and specifies the raw data for the resource. It defaults to an empty string (i. e. no data).
	"""
	
	spec: ResourceSpecDef
	value: typing.Optional[StringExpression]

class Delete(Statement):
	"""A delete statement.
	The spec is required and specifies the resources to delete.
	"""
	
	spec: ResourceSpecUse

class EnumConstant(Node):
	"""An enum constant definition in an Enum.
	The name is required and specifies the macro name of this enum constant. (These names are provided for information only and may not be accurate. Because preprocessing happens before parsing, all uses of enum constants have already been replaced with literal values, and the enum constant definitions might have been redefined or undefined later.)
	The value is optional. If present, it specifies an explicit value for the enum constant. Otherwise, the value is that of the previous enum constant plus 1, or if this is the first enum constant, 0.
	"""
	
	name: str
	value: typing.Optional[IntExpression]

class Enum(Statement):
	"""An enum statement.
	The name is optional and is ignored completely. It has no fixed meaning or use and is only allowed for syntactical compatibility with C.
	The constants are required, but may be empty.
	"""
	
	name: typing.Optional[str]
	constants: typing.Sequence[EnumConstant]

class InvertedType(Node):
	"""An inverted type expression, representing the pseudo-operator "not" inside an Include's from_spec.
	"""
	
	type: IntExpression

class Include(Statement):
	"""An include statement.
	The path is required and specifies the file from whose resource fork resources should be included.
	from_spec is optional and may be a type, an inverted type, or a spec. If a type is given, all resources of that type are included. If an inverted type is given, all resources except those of that type are included. If a spec is given, all resources matching that spec are included. If omitted, all resources are included.
	to_spec is optional and may be a type, or a spec. If a type is given, from_spec must also be a type (not a spec) and all included resources' type is changed to the given type. If a spec is given, all included resources are changed according to the spec. If omitted, the included resources are not changed.
	"""
	
	path: StringExpression
	from_spec: typing.Optional[typing.Union[IntExpression, InvertedType, ResourceSpecUse]]
	to_spec: typing.Optional[typing.Union[IntExpression, ResourceSpecUse]]

class Read(Statement):
	"""A read statement.
	The spec is required and specifies the type, ID, name and attributes to be given to the data.
	The path is required and specifies the file from whose data fork the data should be read.
	"""
	
	spec: ResourceSpecDef
	path: StringExpression

class Resource(Statement):
	"""A resource statement.
	The spec is required and specifies the type, ID, name and attributes of the new resource.
	The values are required and must match the applicable type declaration. (This means that they may be empty.)
	"""
	
	spec: ResourceSpecDef
	values: typing.Sequence[ResourceValue]

class SimpleFieldType(Node):
	"""Base class for all "simple" (non-compound) field types."""

class BooleanFieldType(SimpleFieldType):
	"""A boolean field type."""

class NumericFieldType(SimpleFieldType):
	"""A numeric field type.
	signed marks whether the field should be treated as signed or unsigned when decompiled.
	base specifies what base the field value should be displayed as when decompiled.
	type is the type that the field was declared as.
	For bitfields, size is an IntExpression specifying the bitfield's size, in bits. For other types, it is None.
	"""
	
	class Base(enum.Enum):
		literal = -1
		binary = 2
		octal = 8
		decimal = 10
		hex = 16
	
	class Type(enum.Enum):
		bitstring = -1
		byte = 8
		integer = 16
		longint = 32
	
	signed: bool
	base: Base
	type: Type
	size: typing.Optional[IntExpression]

class CharFieldType(SimpleFieldType):
	"""A char field type.
	The char type is semantically equivalent to string[1].
	"""

class StringFieldType(SimpleFieldType):
	"""A string field type.
	The format specifies how the string should be displayed when decompiled. (The hex modifier is only allowed on the regular string type, not cstring, pstring or wstring.)
	The type specifies how the string is stored. string is bare string data, without any length or terminator. cstring is a C string, terminated by a null byte. pstring is a Pascal string, prefixed by an 8-bit length. wstring is a wide Pascal string, prefixed by a 16-bit length.
	The length is an optional IntExpression specifying the length of the string's contents, in bytes. (A cstring's terminating null counts towards the string length, but a pstring's or wstring's length prefix does not.) When compiling, the input string is padded with nulls or truncated to match the length. When decompiling, the length determines how many bytes are part of the string. If omitted, the length is variable. When compiling, the length is that of the input string. When decompiling, the length is inferred (from the length prefix for pstring and wstring, from the position of the first null byte for cstring, or until end of data for string).
	"""
	
	class Format(enum.Enum):
		literal = 0
		hex = 1
	
	class Type(enum.Enum):
		string = 0
		cstring = 1
		pstring = 2
		wstring = 3
	
	format: Format
	type: Type
	length: typing.Optional[IntExpression]

class PointFieldType(SimpleFieldType):
	"""A point field type."""

class RectFieldType(SimpleFieldType):
	"""A rect field type."""

class Field(Node):
	"""Base class for all field-like declarations."""

class Label(Field):
	"""A label declaration."""
	
	name: str

class SymbolicConstant(Node):
	"""A symbolic constant declaration.
	The name is required, and must be unique among all symbolic constants of the field.
	The value is optional. If present, its type must match that of the field.
	"""
	
	name: str
	value: typing.Optional[ResourceValue]

class SimpleField(Field):
	"""A "simple" (non-compound) field declaration.
	The type is required and may be any SimpleFieldType.
	The value is optional. If present, its type must match the field type. Must be omitted if symbolic constants are given.
	The symbolic constants are required, but may be empty. Must be empty if a value is given.
	is_key specifies whether the field is a switch case key. If true, a value must be given.
	"""
	
	type: SimpleFieldType
	value: typing.Optional[ResourceValue]
	symbolic_constants: typing.Sequence[SymbolicConstant]
	is_key: bool

class FillField(Field):
	"""A fill field.
	The type is required and specifies the base size of the fill field.
	The count is an optional multiplier to the base size. If omitted, defaults to 1.
	"""
	
	class Type(enum.Enum):
		bit = 1
		nibble = 4
		byte = 8
		word = 16
		long = 32
	
	type: Type
	count: typing.Optional[IntExpression]

class AlignField(Field):
	"""An align field.
	The type is required and specifies the unit up to which padding is added.
	"""
	
	class Type(enum.Enum):
		nibble = 4
		byte = 8
		word = 16
		long = 32
	
	type: Type

class ArrayField(Field):
	"""An array field.
	wide specifies whether this array's contents should be written "wide" (all iterations in one line) rather than "narrow" (one line per iteration).
	The label is optional. If present, it can be used to refer to this array in an $$ArrayIndex or $$CountOf Rez function call. Must be omitted if count is given.
	The count is optional. If present, it specifies the number of elements in the array. Must be omitted if label is given.
	The fields are required, but may be empty.
	"""
	
	wide: bool
	label: typing.Optional[str]
	count: typing.Optional[int]
	fields: typing.Sequence[Field]

class SwitchCase(Node):
	"""A switch statement case.
	The label is required, and is used to select the desired switch case when defining a resource.
	The fields are required and must contain one or more fields, of which exactly one must have the is_key flag set.
	"""
	
	label: str
	fields: typing.Sequence[Field]

class Switch(Statement):
	"""A switch statement.
	The cases are required and must not be empty.
	"""
	
	cases: typing.Sequence[SwitchCase]

class Type(Statement):
	"""A type statement.
	The spec is required.
	The fields are optional, and may be empty if present. They specify which fields are in the newly declared type. Must be omitted if from_spec is given.
	The from_spec is optional. It specifies another type (and optionally an ID) from which to copy the definition to this type. Must be omitted if fields are given.
	"""
	
	spec: ResourceSpecTypeDef
	fields: typing.Optional[typing.Sequence[Field]]
	from_spec: typing.Optional[ResourceSpecTypeUse]

class File(Node):
	"""A Rez source file, containing a sequence of zero or more top-level statements.
	This is the root node of an AST created by parsing a file.
	"""
	
	statements: typing.Sequence[Statement]
