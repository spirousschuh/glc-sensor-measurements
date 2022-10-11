import io
import os
import re
import setuptools


def read(filename):
    filename = os.path.join(os.path.dirname(__file__), filename)
    text_type = type(u"")
    with io.open(filename, mode="r", encoding='utf-8') as fd:
        return re.sub(
            text_type(r':[a-z]+:`~?(.*?)`'),
            text_type(r'``\1``'),
            fd.read()
        )


setuptools.setup(
    name="glc_sensor_measurements",
    version="0.1.0",
    url="https://git.tu-berlin.de/bvt-htbd/kiwi/tf3/glc_sensor_measurements",
    license='MIT',

    author="Christoph Lange",
    author_email="christoph.lange@tu-berlin.de",
    description="Track and measure the values coming out of the glucose sensor"
                " via the USB port.",
    long_description=read("README.rst"),
    long_description_content_type='test/x-rst',
    packages=setuptools.find_packages(exclude=('tests')),
    install_requires=['click', 'pyserial', 'grpcio', 'grpcio-tools'],
    entry_points={
        'console_scripts': [
            'measure='
            'glc_sensor_measurements.cli:measure'
        ],
    },
)
