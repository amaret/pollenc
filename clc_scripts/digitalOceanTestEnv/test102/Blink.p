
import EFM32TG840 as Mcu
from Mcu import PD7

module Blink {

  Blink() {
    PD7.clear()
    PD7.makeOutput()
  }  

  pollen.reset() {
    Mcu.reset()
  }

  pollen.run() {

    while(true) {
      PD7.toggle()
      delay()
    }
  }

  delay() { 
    for (uint16 i = 0; i < 250; ++i) {
      Mcu.wait(1000)
    }
  }

}