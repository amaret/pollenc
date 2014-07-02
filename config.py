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

pollenc_tcp = {
  'interface': '0.0.0.0',
  'port': 2323,
}

riemann = {
  'host': 'redbis.wind.io',
  'clienthost': 'passage.wind.io'
}

