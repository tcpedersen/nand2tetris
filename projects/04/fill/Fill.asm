// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// Put your code here.

(QUERY)
    @KBD
    D = M

    @PAINTBLACK
    D;JNE

    @PAINTWHITE
    0;JMP

(PAINTBLACK)
    @overwrite
    M = -1

    @PAINT
    0;JMP

(PAINTWHITE)
    @overwrite
    M = 0

    @PAINT
    0;JMP

(PAINT)
    @SCREEN
    D = A

    @address
    M = D

    (LOOP)
        // Determine if loop should be terminated.
        @KBD
        D = A

        @address
        D = D - M

        @QUERY
        D;JLE

        // Paint it black/white.
        @overwrite
        D = M

        @address
        A = M
        M = D

        // Advance address
        @address
        M = M + 1

        // Perform next iteration of loop.
        @LOOP
        0;JMP

