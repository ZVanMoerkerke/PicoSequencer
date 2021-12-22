# PicoSequencer
A modular sequencer based on Pi Pico &amp; EuroPi
By Zeno Van Moerkerke / Keurslager Kurt

For now it is 'only' a trigger sequencer, but I sincerely hope to build this into an Elektron style complex sequencer with CV out, conditional triggers, microtiming,..

So what can it do right now?

- Build a trigger sequence of arbitrary length in Thonny. Eg [1, 0, 0, 0] will be a trigger on every quarter note. Each ',' indicates the next sixteenth step. A '1' indicates a trigger and a '0' a pause.
- Technically you can send the triggers to a total amount of 30 pins. If you work with EuroPi, it only makes sense to use six pins of course.
- To use for example the two first pins for a trigger sequence, you fill in the 'allSequences' variable like this:
[
this is the first pin's sequence
[1, 0, 0, 0]

,
this is the second pin's:
[0, 0, 1, 0]
]

So the 'allSequences' variable is effectively a so-called 'nested' list: a list of list. The first list corresponds to the first pin, second to second etc..

- Sequences loop automatically. If you choose sequences of different lengths, they will start to drift apart: cool!
- You can also drop in values BETWEEN 0 and 1 to use probabilities. A value of 0.5 will for example have a 50% chance to generate a trigger at that moment.
- - Variable clock, set with analog input 1 (you can change this if you want to use something else). I rescaled the value to 0-5V now, so you can change this according to your setup. Or disable the analog input line and just set the bpm in the script.
