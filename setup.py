import platform
from setuptools import setup

on_rpi = platform.machine().startswith('arm')

install_requires = ['msl-network>=0.4']
if on_rpi:
    install_requires.append('bluepy')

setup(
    name='smartgadget',
    version='0.1.0.dev0',
    author='Joseph Borbely',
    author_email='joseph.borbely@measurement.govt.nz',
    url='https://github.com/MSLNZ/rpi-smartgadget',
    description='Communicate with a Sensirion SHTxx Smart Gadget',
    long_description=open('README.rst').read().strip(),
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    install_requires=install_requires,
    packages=['smartgadget'],
    entry_points={
        'console_scripts': [
            'smartgadget = smartgadget:start_service_on_rpi',
            'bluez-update = smartgadget.update_bluez:run',
        ],
    },
)
