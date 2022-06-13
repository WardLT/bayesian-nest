from setuptools import setup, find_packages

# Open the requirements
with open('requirements.txt') as fp:
    req_list = fp.read().strip().split("\n")

setup(
    name='bayesnest',
    version='0.0.1',
    packages=find_packages(),
    description='Bot that builds a better HVAC model for my house than Nest, hopefully.',
    entry_points={
        'console_scripts': 'bayesnest=bayesnest.app:main'
    },
    install_requires=req_list
)
