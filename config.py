'''
Global configuration file
'''
mongo = {
  'host': 'localhost', # '10.244.138.56'
  'port': 27017,
}

redis = {
  'host': 'redbis.wind.io',
  'port': 6379,
}

#pollenc_tcp = {
#  'interface': '0.0.0.0',
#  'port': 2323,
#}

pollenc_tcp = {
          'interface': 'ec2-54-89-253-204.compute-1.amazonaws.com',
          'port': 5140,
}


riemann = {
  'host': 'redbis.wind.io',
  'clienthost': 'passage.wind.io'
}

redisQueues = {
        'arm-none-eabi-gcc': 'POLLEN_CLC_ARM_NONE_EABI_GCC_1_0',
        'avr-gcc': 'POLLEN_CLC_AVR_GCC_1_0',
        'localhost-gcc': 'POLLEN_CLC_LOCALHOST_1_0'
}

