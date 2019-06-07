from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(name='cissflux',
    version=1.2,
    description='Extract sensor values from BOSCH CISS and save them to InfluxDB',
    long_description=readme(),
    url='https://github.com/shantanoo-desai/cissflux',
    author='Shantanoo Desai',
    author_email='shantanoo.desai@gmail.com',
    license='MIT',
    packages=['cissflux'],
    scripts=['bin/cissflux'],
    install_requires=[
        'pyserial',
        'influxdb'
    ],
    include_data_package=True,
    zip_safe=False
)