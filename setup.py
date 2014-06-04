try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

VERSION = '0.2'


SETUP_DICT = dict(
    name='smartserver',
    packages=['egauge'],
    version=VERSION,
    author='mandarjog',
    author_email='mandarjog@gmail.com',
    url='https://github.com/PlotWatt/Smartmeters',
    description='smart server config',
    long_description="smart server config",
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
  )

# generate .rst file with documentation
#open(os.path.join(os.path.dirname(__file__), 'documentation.rst'), 'w').write(DOCUMENTATION)

setup(**SETUP_DICT)
