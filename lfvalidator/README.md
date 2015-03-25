lfvalidator
=========
lfvalidator is a package which contains an import file validator and its components. It is intended to be run each time a customer gives us data to import.

Usage
-----
The validator executable is run on the command line:
```
./validator file.txt
```
This will produce several output files:
- validator_results.txt : Contains all of the errors caught by the validator, listed by line number
- fixed_file.txt : Sanitized version of the input file. For DE's, this is the file that should be imported.
- sanitize_results.txt : Output file of any errors that occured while the sanitized file was created.
- receipt.txt : md5 hash of the validated file.

Making the executable
---------------------
If you would like to contribute to the import validator, you can do so by pulling down this repo, and then installing.
```
python setup.py install
```
This will install the lfvalidator in path, so you can now import the package in python. You'll also need to pull down the pyinstaller repo which is used to create the executable: https://github.com/pyinstaller/pyinstaller.

The functionality of the validator is all contained in the lfvalidator/validator.py file. If you want to test local changes made to this file, you can run it as a standalone script.
```
python validator.py file.txt
```
Once you have made your changes and want to create a new executable, you can use pyinstaller to do so. You'll need to run the pyinstaller.py file inside of the dir where you cloned pyinstaller on the validator.py file that you were modifying.
```
python ~/path_to_pyinstaller/pyinstaller/pyinstaller.py -F validator.py
```
This will create a executable in your current directory, under dist/validator. If you are happy with the results of your new executable, please commit all changes to source files as well as the validator executable to this repo.
