#  ecr_exporter
#  ---------------
#  A Prometheus exporter for AWS ECR
#
#  Author:  Tim Birkett <tim.birkettdev@devopsmakers.com>
#  Website: https://github.com/devopsmakers/python-grafannotate
#  License: MIT License (see LICENSE file)

import codecs
from setuptools import find_packages, setup

dependencies = [
    'boto3==1.17.95',
    'prometheus-client==0.11.0',
    'cachetools==4.2.2',
    'python-json-logger==2.0.1'
]

setup(
    name='ecr_exporter',
    version='0.0.1',
    url='https://github.com/aws-exporters/ecr',
    license='MIT',
    author='Tim Birkett',
    author_email='tim.birkett@devopsmakers.com',
    description='A Prometheus exporter for AWS ECR',
    long_description=codecs.open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=dependencies,
    entry_points={
        'console_scripts': [
            'ecr_exporter = ecr_exporter.server:run',
        ],
    },
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 4 - Beta',
        'Topic :: Utilities',
        'Topic :: System :: Monitoring',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
    ]
)