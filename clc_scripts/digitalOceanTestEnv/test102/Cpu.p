package efm32

from pollen.hardware import CpuProtocol

module Cpu implements CpuProtocol {

  +{  
      #include "em_chip.h"
      #include "em_device.h"
      #include "em_assert.c"
      #include "em_cmu.c"
      #include "em_system.c"
  }+

  public reset() {   
    +{ CHIP_Init() }+     // EFM32 Chip errata
  }  

  public shutdown() {

  } 

  public setFrequency(uint32 hz) {

  }

  public host setFrequencyOnHost(uint32 hz) {

  }

  public uint32 getFrequency() {

  }

  public host uint32 getFrequencyOnHost() {

  }
     
  public wait(uint16 us)  {
    us += (us / 4)    
    for (; us > 0; us--) {  
      +{ __asm__ __volatile__ ("nop") }+
      +{ __asm__ __volatile__ ("nop") }+
      +{ __asm__ __volatile__ ("nop") }+
      +{ __asm__ __volatile__ ("nop") }+
      +{ __asm__ __volatile__ ("nop") }+
      +{ __asm__ __volatile__ ("nop") }+
      +{ __asm__ __volatile__ ("nop") }+
      +{ __asm__ __volatile__ ("nop") }+
      +{ __asm__ __volatile__ ("nop") }+
      +{ __asm__ __volatile__ ("nop") }+
      +{ __asm__ __volatile__ ("nop") }+
      +{ __asm__ __volatile__ ("nop") }+
      +{ __asm__ __volatile__ ("nop") }+
      +{ __asm__ __volatile__ ("nop") }+
      +{ __asm__ __volatile__ ("nop") }+
    }
  }

  public cycle() {
   +{ __asm__ __volatile__ ("nop") }+
  }


}
