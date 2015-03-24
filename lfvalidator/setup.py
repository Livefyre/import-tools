from setuptools import setup

install_requires = ['jsonschema', 'requests']

setup(name='lfvalidator',
      version='0.1',
      description='livefyre import file validator',
      url='https://github.com/Livefyre/integration-tools',
      author='mliao',
      author_email='mliao@livefyre.com',
      license='MIT',
      packages=['lfvalidator'],
      install_requires=install_requires,
      zip_safe=False)
