from setuptools import setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
  name = 'code_diff',
  packages = ['code_diff'], 
  version = '0.1.0', 
  license='MIT',     
  description = 'Fast AST based code differencing in Python',
  long_description = long_description,
  long_description_content_type="text/markdown",
  author = 'Cedric Richter',                   
  author_email = 'cedricr.upb@gmail.com',    
  url = 'https://github.com/cedricrupb/code_diff',  
  download_url = 'https://github.com/cedricrupb/code_diff/archive/refs/tags/v0.1.0.tar.gz', 
  keywords = ['code', 'differencing', 'AST', 'program', 'language processing'], 
  install_requires=[          
          'code-tokenize',
          'apted'
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',    
    'Intended Audience :: Developers',  
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3', 
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
  ],
)