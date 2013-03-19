package blink.msp430

module BlinkFastMsp430 {

  +{ #include <msp430g2452.h> }+

  pollen.run() {  
    +{WDTCTL}+ = +{WDTPW}+ | +{WDTHOLD}+    # Stop watchdog timer
    +{P1OUT}+ &= ~(1 << 0)                  # Clear the pin
    +{P1DIR}+ |= (1 << 0)                   # Make pin output
    
    while (true) {
      +{P1OUT}+ ^= (1 << 0)                 # toggle the pin
      delay(200)
    }
  }

  
  !-- Helper method --!
  delay(uint16 ms) {
    for (; ms > 0; --ms) {
      for (uint16 us = 200; us > 0; --us) {
        +{ asm ("nop") }+                              
      }
    }
  }
  
}
