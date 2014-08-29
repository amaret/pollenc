'''
Global configuration file
'''
mongo = {
  'host': 'localhost', # '10.244.138.56'
  'port': 27017,
}

pollenc_tcp = {
    'interface': 'pcc.amaret.com', 
    'port': 5140,
}

redisQueues = {
        'arm-none-eabi-gcc': 'POLLEN_CLC_ARM_NONE_EABI_GCC_1_0',
        'avr-gcc': 'POLLEN_CLC_AVR_GCC_1_0',
        'localhost-gcc': 'POLLEN_CLC_LOCALHOST_1_0'
}

