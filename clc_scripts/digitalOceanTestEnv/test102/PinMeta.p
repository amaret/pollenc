from pollen.hardware import PinProtocol

meta { string port, uint8 pin }

module PinMeta implements PinProtocol {

  +{ #include "em_gpio.c"}+
  +{ #include "em_cmu.h" }+

  host uint8 portNum      
  host uint8 pinNum       // temporarily here, using the meta argument wasn't working for me...

  host PinMeta() {
    pinNum = pin
    if   (port == "A") { portNum = 0 }
    elif (port == "B") { portNum = 1 }
    elif (port == "C") { portNum = 2 }
    elif (port == "D") { portNum = 3 }
    elif (port == "E") { portNum = 4 }
    elif (port == "F") { portNum = 5 }
  }

  PinMeta() {

    // This really should only be done once for all pins! Manager Pattern!
    +{ CMU_ClockEnable(cmuClock_HFPER, true) }+
    +{ CMU_ClockEnable(cmuClock_GPIO, true) }+

  }

  public set() { 
    +{ GPIO_PinOutSet(`portNum`, `pinNum`) }+
  } 

  public clear() {
    +{ GPIO_PinOutClear(`portNum`, `pinNum`) }+
  } 
  
  public toggle() {
    +{ GPIO_PinOutToggle(`portNum`, `pinNum`) }+
  }  
  
  public bool get() {
    return +{ GPIO_PinOutGet(`portNum`, `pinNum`) }+ == 1
  }

  public bool isInput() {
    // this method is not implemented for this device! set mode as desired. 
    return false
  }
  
  public bool isOutput() {
    // this method is not implemented for this device! set mode as desired.
    return false
  }
  
  public makeInput() {
    +{ GPIO_PinModeSet(`portNum`, `pinNum`, gpioModeInput, 0) }+
  } 
  
  public makeOutput() {
    +{ GPIO_PinModeSet(`portNum`, `pinNum`, gpioModePushPull, 0) }+
  } 
  
}