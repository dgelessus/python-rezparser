//# import <Carbon.r> ignore me

#include$$format("%s/", "RIncludes")"Types" ".r"; ignore me?"

#define thing 13
#ifndef thing ignore me?"
	#define thing 42
#elif sysheap == 0x40
	#define thing 1
#else ignore me
	#define thing 0
#endif ignore me

//#define hash #

//hash define define hash define

//define hello "bye"

//#define typeid #define foo

#undef foo
#undef foo ignore me

//typeid "bar"

enum numbers {
	zero,
	one,
	two,
};

#printf("%d %d %d %d\r", thing, zero, one, two); type 'blub' {wstring;};

#if DeFined zero
	#printf("zero is defined\r")
#else
	#printf("zero is not defined\r")
#endif

#undef zero

#if defined(zero)
	#printf("zero is still defined\r")
#else
	#printf("zero is not defined anymore\r")
#endif

#if defined defined
	#printf("defined is defined\r")
#else
	#printf("defined is not defined\r")
#endif

enum {
	expr = 1 + 2 + 3,
};

#printf("expr: %d\r", expr / 2)

type '_FOO' {
	start: integer = start;
	integer = end;
	typecode: literal longint;
	id: integer;
	name: wstring;
	attributes: hex unsigned byte;
	stuff_length: unsigned integer = $$countof(stuff);
	stuff: wide array stuff {
		stuff_thing: hex unsigned byte;
		unsigned integer = stuff_thing[$$ArrayIndex(stuff)];
	};
	text: cstring;
	hext: hex string dead = $"dead", beef = $"beef",;
	end:
};

type 'swit' {
	switch {
		case foo:
			key byte = 0;
		
		case bar:
			key byte = 1;
	};
};

resource 'swit' (0) {
	foo {},;
};

resource 'None' (0) {
	;
};

resource '_FOO' (0, "", SysHeap, nonpreload) {
	#include "TypeID.r"
	{
		thing + 0,
		typecode,
		id,
		name,
		attributes,
		stuff_length,
		stuff,
	},
	$$read("hello.txt") $$read("hello.txt"),
	$"deadbeef"
};

resource '_FOO' (1, "name") {
	#include "TypeID.r"
	{},
	#printf("%x %d %s %x\r", $$type, $$id, $$name, $$attributes)
	#if $$id == 0
		"id is 0",
	#else
		"id is not 0",
	#endif
	$"DeAd",
	;
};

resource 'blub' (0) {
	"abcdef";
};

resource 'blub' (1) {
	#if 1
		"one"
	#else
		"zero"
	#endif
	;
};

data 'data' (0) {
	"data";
};

data 'data' (1) {
	$"ABCDEF"
};

;
