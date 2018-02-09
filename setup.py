# -*- coding: utf-8 -*-
from setuptools import setup

setup(name='pyCAER',
	version='20180208_r0',
	description='python Caer client and NCS api',
	author='Emre Neftci',
	author_email='eneftci@uci.edu',
	url='https://github.com/nmi-lab/pyCAERdynapse',
	packages=['pyCAER','pyCAER.api'],
        package_dir={'' : 'src'},
        install_requires=['numpy'],
     )



