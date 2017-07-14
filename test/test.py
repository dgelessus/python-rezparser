import sys

import rezparser.lexer
import rezparser.parser
import rezparser.eval
import rezparser.preprocessor
import rezparser.ast

def pretty_print_ast(obj, *, current_depth=0):
	indent = "\t"*current_depth
	if isinstance(obj, list):
		if obj:
			print("[")
			for element in obj:
				print(indent + "\t", end="")
				pretty_print_ast(element, current_depth=current_depth+1)
				print(",")
			print(indent + "]", end="")
		else:
			print("[]", end="")
	elif isinstance(obj, rezparser.ast.Node):
		print(type(obj).__qualname__ + "(", end="")
		
		names = []
		for tp in reversed(type(obj).__mro__):
			try:
				anns = tp.__dict__["__annotations__"]
			except KeyError:
				pass
			else:
				names.extend(anns)
		
		for name in names:
			try:
				attr = getattr(obj, name)
			except AttributeError:
				continue
			
			print(name + "=", end="")
			pretty_print_ast(attr, current_depth=current_depth)
			if name != names[-1]:
				print(", ", end="")
		
		print(")", end="")
	else:
		print(repr(obj), end="")

def main():
	with open(sys.argv[1], "r") as f:
		text = f.read()
	
	lexer = rezparser.lexer.RezLexer(filename=sys.argv[1], debug=True)
	parser = rezparser.parser.RezParser(debug=True)
	evaluator = rezparser.eval.Evaluator()
	preprocessor = rezparser.preprocessor.RezPreprocessor(
		lexer=lexer,
		parser=parser,
		evaluator=evaluator,
		include_path=["."],
		sys_include_path=["/System/Library/Frameworks"],
		print_func=print,
	)
	
	pretty_print_ast(parser.parse_file(text, preprocessor, debug=True, tracking=True))


if __name__ == "__main__":
	main()
