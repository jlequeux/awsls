import setuptools
import pkg_resources
import pathlib

with pathlib.Path('requirements.txt').open() as requirements_txt:
    install_requires = [
        str(requirement)
        for requirement
        in pkg_resources.parse_requirements(requirements_txt)
    ]

setuptools.setup(
   name='awsls',
   version='1.0',
   author='jlequeux',
   author_email='jlequeux@gmail.com',
   packages=setuptools.find_packages(),
   license='LICENSE.txt',
   description='List AWS resources from multiple regions',
   long_description=open('README.md').read(),
   install_requires=install_requires,
   entry_points = '''
        [console_scripts]
        awsls=awsls.awsls:cli
    '''
)