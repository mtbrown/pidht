from distutils.core import setup, Extension

extension_mod = Extension(
    name='pidht.driver',
    sources=['driver/driver.c', 'driver/dht.c'],
    libraries=['wiringPi'])

setup(name='pidht', py_modules=['pidht.parse'], ext_modules=[extension_mod])
