from setuptools import setup, find_packages

setup(
  name='ispawn',
  version='0.1.0',
  author='Julien FOURET',
  author_email='your.email@example.com',
  description='Spawn Docker containers with RStudio Server and Jupyter.',
  long_description=open('README.md').read(),
  long_description_content_type='text/markdown',
  url='https://github.com/jfouret/ispawn',
  packages=find_packages(),
  install_requires=[
      'jinja2',
  ],
  entry_points={
      'console_scripts': [
          'ispawn = ispawn.main:main',
      ],
  },
  package_data={
      'ispawn': ['templates/*.j2'],
  },
  include_package_data=True,
  classifiers=[
      'Programming Language :: Python :: 3',
      'License :: OSI Approved :: Apache 2 License', 
      'Operating System :: OS Independent',
  ],
  python_requires='>=3.6',
)