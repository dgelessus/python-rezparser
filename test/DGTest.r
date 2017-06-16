# import <CoreServices/CoreServices.r> ignore me

//#include$$format("%s/", "RIncludes")"Types" ".r"; ignore me?"
#include "RIncludes/" "Types" ".r"; ignore me?"

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

#printf("3 / 2 = %d, -3 / 2 = %d, 3 / -2 = %d, -3 / -2 = %d\r", 3 / 2, -3 / 2, 3 / -2, -3 / -2);
#printf("7 %% 5 = %d, -7 %% 5 = %d, 7 %% -5 = %d, -7 %% -5 = %d\r", 7 % 5, -7 % 5, 7 % -5, -7 % -5)
#printf("8 << 2 = %d, 8 << -2 = %d\r", 8 << 2, 8 << -2)
#printf("8 >> 2 = %d, 8 >> -2 = %d\r", 8 >> 2, 8 >> -2)
#printf("Date: %s; Time: %s; Version: %s\r", $$Date, $$Time, $$Version)

#define abc "abc"
#define def "def"
#define abcdef abc def
#define ghi "ghi"
#define abcdefghi abcdef ghi
#define xyz "xyz"
#define xyzabcdefghi xyz abcdefghi
#printf("%s\r", xyzabcdefghi)

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
	bitcount: byte;
	bits: bitstring[$$Byte(bitcount)];
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

type 'what' (2) {
	integer;
};

type 'what' (3) {
	string;
};

type 'what' (4) {
	;;boolean;;boolean;;
};

type 'ever' as 'what' (2);

type 'yarr' {
	wide array [4] {
		byte;
	};
};

type 'ints' {
	integer;
	int;
};

resource 'ever' (2) {
	42;
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
	8,
	123,
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
	16,
	12345,
	$"DeAd",
	;
};

resource '_FOO' (2) {
	#include "TypeID.r"
	{
		0b10001000,
		// Commented out to reduce parser output when testing
		/*
		$$bitfield(stuff_thing[1] + 0, 0, 1),
		$$bitfield(stuff_thing[1] + 1, 0, 1),
		$$bitfield(stuff_thing[1] + 2, 0, 1),
		$$bitfield(stuff_thing[1] + 3, 0, 1),
		$$bitfield(stuff_thing[1] + 4, 0, 1),
		$$bitfield(stuff_thing[1] + 5, 0, 1),
		$$bitfield(stuff_thing[1] + 6, 0, 1),
		$$bitfield(stuff_thing[1] + 7, 0, 1),
		$$bitfield(stuff_thing[1] + 0, 0, 2),
		$$bitfield(stuff_thing[1] + 2, 0, 2),
		$$bitfield(stuff_thing[1] + 4, 0, 2),
		$$bitfield(stuff_thing[1] + 6, 0, 2),
		$$bitfield(stuff_thing[1] + 0, 0, 4),
		$$bitfield(stuff_thing[1] + 4, 0, 4),
		$$bitfield(stuff_thing[1] + 0, 0, 8),
		*/
	},
	"",
	8,
	0b0 + 0B0 + $0 + 0x0 + 0X0,
	$""
};

resource 'blub' (0) {
	"abcdef\t\b\r\n\f\v\?\\\'\"\0B00101010\052\0D042\0X2a\$2a\499";
};

resource 'blub' (1) {
	#if 1
		"one"
	#else
		"zero"
	#endif
	;
};

resource 'yarr' (0) {
	{1, 2, 3, 4};
};

resource 'ints' (1234) {
	1234,
	1234,
};

data 'data' (0) {
	"data";
};

data 'data' (1) {
	$"ABCDEF"
};

data 'wot\?' (0) {};

;
