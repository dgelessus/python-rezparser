import sys

import rezparser.lexer
import rezparser.parser
import rezparser.eval
import rezparser.preprocessor

def main():
	with open(sys.argv[1], "r") as f:
		text = f.read()
	
	lexer = rezparser.lexer.RezLexer(debug=True)
	parser = rezparser.parser.RezParser(debug=True)
	evaluator = rezparser.eval.Evaluator()
	preprocessor = rezparser.preprocessor.RezPreprocessor(lexer=lexer, parser=parser, evaluator=evaluator)
	
	print(parser.parse_file(text, preprocessor, debug=True, tracking=True))


if __name__ == "__main__":
	main()
