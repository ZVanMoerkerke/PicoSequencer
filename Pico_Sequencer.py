#trying to make a complex sequencer using one of the pico state machines for synchronous triggering.
#right now you can enter a sequence for eg the first pin [1 0 0 0] which will sequence the trigger.
#sequences can have different lengths.
#set the bpm with the analog voltage in (i use a pot for this).

#todo:
#oled, pot & switch manipulation & setting of sequence
#retriggers
#conditional triggering

#imports
from europi import *
from machine import Pin
from time import sleep
from rp2 import PIO, StateMachine, asm_pio
import sys
import random
random.seed()

#fill in sequences of choice here

allSequences= [

[1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.8, 0,
1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0.8, 0,
1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0.8, 0,
1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0.8, 0]

,

[0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,1,0, 0,0,0,0, 1,0,0,0,
0,0,0,0, 1,0,0,1, 0,0,0,0, 1,0,0,0, 1,1,0,0, 1,0,0,1, 0,0,0,1, 1,1,0,1]

,

[0.5, 0.5, 0.5, 0.5]

,

[1, 0, 0, 0, 0, 0,
1, 0, 0, 0, 0, 0,
1, 0, 0, 0, 1, 0,
1, 0, 0, 0, 0, 0]

,

[1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1,0,0,0]
]

trig_length = 5 #set trigger length in ms
bpm = 120 #initialize bpm

clock_min = 10
clock_max = 240 #adjust these to taste



###

#initializing some values for first cycle

step = 0 #initialize step. Keeps track of where the sequencer is
lengths = [len(i) for i in allSequences]
individualSteps = [step%i for i in lengths]
flag = 1 #initialize interrupt flag
trig_waitcycles = int(trig_length*1000/2) #calculate trig length in clock cycles
pio_waitcycles = 0 #initialize this value




#some functions to make life easier

def set_clock(bpm):
    global trig_length
    global pio_waitcycles
    
    frequency_ms = 1/(bpm*4/60) * 1000 #freq of a sixteenth in ms
    pio_waitcycles = int((1000*frequency_ms - trig_length*1000 +20)/2)  #wait time for pio. Tried to calculate it with ticks, but now its set empirically with scope.

def convert(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    
def sum_digits(digits): 
    return sum(c << i for i, c in enumerate(digits)) 



#the interrupt that calculates whether to trigger pins according to the sequence & the probabilities

def set_sequencer(sm):
    global flag
    global step
    global pio_waitcycles
    global trig_waitcycles
    
    trig = [int(random.random() < allSequences[i][individualSteps[i]]) for i in range(len(allSequences))]     
            
    trig = sum_digits(trig)
    
    sm.put(trig)   
    sm.put(pio_waitcycles)
    sm.put(trig_waitcycles)
    
    step += 1
    flag = 1


#initialize first clock
bpm_old = bpm
set_clock(bpm)

###

#most complicated bit: setting up the state machine. Search about the 'PIO' or check the RP2040 datasheet for more info.
#this part does the sequencing & timing alongside the CPU. That way the sequencer is nice & steady, independent of the main loop
    
@asm_pio(set_init = ([PIO.OUT_LOW]*len(allSequences)),
         out_init=([PIO.OUT_LOW]*len(allSequences)),
         out_shiftdir=PIO.SHIFT_RIGHT,
         in_shiftdir=PIO.SHIFT_LEFT) #in case more pins need to be set/triggered, adjust the '4'

def seq():
    wrap_target()
    
    pull() #pull wait time    1 tick start
    mov(x, osr) #copy wait time to x scratch register    1 tick start
    out(null,32) #discard data    1 tick start
    
    pull()    #1 tick start
    set(y, 0) #clear y    1 tick start
    mov(y, osr) #copy gate time to y scratch register    1 tick start
    out(null,32) #discard data     1 tick start
        
    label("loop") #wait cycle
    
    jmp(x_not_y, "notrig") #check to start trig     1 tick loop
    
    irq(rel(0)) [30]  #start trig, first small delay to get sequence data.   1 tick trig start
    nop() [30]
    nop() [30] #1ms wait for response = 10 ticks
    pull() #seq      1 tick trig start
    out(pins,6) #shift sequence in OSR out to pins     1 tick trig start (pins set at start or end of tick, i suppose end?)
    jmp(x_dec, "loop")     #1 tick trig
    
    label("notrig")
    jmp(x_dec, "loop") #loop if still not zero    1 tick loop
    
    set(pins,0) #set pins low when x = 0    1 tick trig
    wrap() #go back to start

###

#here we turn on the statemachine with a frequency of 100MHz. We start output pins at 16. Technically there can be 30 outputs.
    
sm = StateMachine(0, seq, freq=1000000, set_base=Pin(16), out_base=Pin(16))
sm.irq(set_sequencer)
sm.active(1)
sm.put(pio_waitcycles)
sm.put(trig_waitcycles)


#main loop updating oled with bpm, also doing some small calculus to keep the interrupt above as short as possible.

while True:
    bpm = int(convert(ain1.read_voltage(), 0, 5, clock_min, clock_max))
    oled.centre_text(str(bpm))
    oled.show()
    
    if flag ==1 :
        individualSteps = [step%i for i in lengths]
        flag = 0
        
    if bpm != bpm_old:
        set_clock(bpm)
        bpm_old = bpm

    
                  
    
    

    
    