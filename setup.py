'''
skype-chatsync-reader: Parser and GUI viewer of chatsync/*.dat files from the Skype profile directory

Note that "python setup.py test" invokes pytest on the package. With appropriately
configured setup.cfg, this will check both xxx_test modules and docstrings.

Copyright 2015, Konstantin Tretyakov.
Licensed under MIT.
'''
import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

# This is a plug-in for setuptools that will invoke py.test
# when you run python setup.py test
class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest  # import here, because outside the required eggs aren't loaded yet
        sys.exit(pytest.main(self.test_args))


version = "0.1"

setup(name="skype-chatsync-reader",
      version=version,
      description="Parser and GUI viewer of chatsync/*.dat files from the Skype profile directory",
      long_description=open("README.rst").read(),
      classifiers=[ # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 7 - Inactive',
        'Programming Language :: Python',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Communications :: Chat',
        'Topic :: Utilities',
      ],
      keywords="skype file-format wx log-viewer", # Separate with spaces
      author="Konstantin Tretyakov",
      author_email="kt@ut.ee",
      url="http://github.com/konstantint/skype-chatsync-reader",
      license="MIT",
      packages=find_packages(exclude=['examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      tests_require=['pytest'],
      cmdclass={'test': PyTest},
      
      # TODO: List of packages that this one depends upon:   
      install_requires=[],
      # TODO: List executable scripts, provided by the package (this is just an example)
      entry_points={
        'console_scripts': 
            ['skype-chatsync-viewer=skype_chatsync_reader.gui:main']
      }
)
