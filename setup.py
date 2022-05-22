from setuptools import setup

setup(name='tap-appfigures',
      version='0.0.1',
      description='Singer.io tap for scraping data from Appfigures',
      author='Kelly Mondor',
      url='https://singer.io',
      classifiers=['Programming Language :: Python :: 3 :: Only'],
      py_modules=['tap_appfigures'],
      install_requires=[
          'backoff==1.8.0',
          'requests==2.20.1',
          'singer-python==5.12.1'
      ],
      entry_points='''
          [console_scripts]
          tap-appfigures=tap_appfigures:main
      ''',
      packages=['tap_appfigures', 'tap_appfigures.streams'],
      package_data={
          "schemas": ["tap_appfigures/schemas/*.json"]
      },
      include_package_data=True,
    )
