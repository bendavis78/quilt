from setuptools import setup, find_packages

def read(fname):
    import os
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='quilt', 
    version=__import__('quilt').__version__,
    author='Ben Davis',
    author_email='bendavis78@gmail.com',
    url='http://github.com/bendavis78/quilt/',
    description='A framework for modular add-ons for fabric with a basic configuration management api',
    keywords='fabric quilt',
    classifiers = [],
    packages = find_packages(),
    include_package_data = True,
    install_requires = [
        'jinja2',
        'pushy'
    ]
)
