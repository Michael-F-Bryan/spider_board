#!/usr/bin/env python3

from setuptools import find_packages, setup

setup(name='spider_board',
      description='A blackboard scraper for Curtin University students',
      author='Michael Bryan',
      packages=find_packages(exclude=['docs', 'scripts']),
      install_requires=[
          'requests',
          'bs4',
      ],
      entry_points={
          'console_scripts': [
              'spider_board = spider_board.__main__:main',
              ]
          },
      license='MIT',
     )


