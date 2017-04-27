import sys

import rezparser.lexer
import rezparser.parser

def main():
	with open(sys.argv[1], "r") as f:
		text = f.read()
	
	lexer = rezparser.lexer.RezLexer(debug=True)
	parser = rezparser.parser.RezParser(lexer, debug=True)
	
	print(parser.parse_file(text, debug=True, tracking=True))


if __name__ == "__main__":
	main()
