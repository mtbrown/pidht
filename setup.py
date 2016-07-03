from distutils.core import setup, Extension

extension_mod = Extension("pidht", sources=["pidhtmodule.c", "dht.c"], libraries=['wiringPi'])

setup(name="pidht", ext_modules=[extension_mod])
