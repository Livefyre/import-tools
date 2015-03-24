from setuptools import setup

install_require = ['jsonschema', 'requests']

setup(name='lfvalidator',
      version='0.1',
      description='livefyre import file validator',
      url='https://github.com/Livefyre/integration-tools',
      author='mliao',
      author_email='mliao@livefyre.com',
      license='MIT',
      packages=['lfvalidator'],
      install_require=install_require,
      zip_safe=False)
