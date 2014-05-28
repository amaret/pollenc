package blink.avr

module Blink0 {

  +{ #include <avr/io.h> }+

  pollen.run() {  
    +{PORTB}+ &= ~(1 << 5)                 # Clear the pin
    +{DDRB}+ |= (1 << 5)                   # Make pin output
    
    while (true) {
      +{PORTB}+ ^= (1 << 5)                # toggle the pin
      delay(1000)
    }
  }

  
  !-- Helper method --!
  delay(uint16 ms) {
    for (; ms > 0; --ms) {
      for (uint16 us = 3000; us > 0; --us) {
        +{ asm ("nop") }+                              
      }
    }
  }

  
}
