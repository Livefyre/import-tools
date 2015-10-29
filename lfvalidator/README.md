lfvalidator
=========
lfvalidator is a package which contains import file validators of multiple types. It is intended to be run each time a customer gives us data to import. All of the validator are available for download in the executables folder.

Usage
-----
All validators are run on the command line. All of the validators will create a file called validator_results.txt in the current directory, which contains all of the errors listed by line number found during validation.

## Interactive Comments Validator
```
./validator file.txt
```
This will produce an output file in the current directory:
- fixed_file.txt : Sanitized version of the input file. For DE's, this is the file that should be imported.

## Users Validator
```
./users_validator comments_file.txt users_file.txt
```
This will produce an output file in the current directory:
- fixed_users_file.txt : A sanitized users file, which only contains users that are in the comments file. Users which are not in the comments file will not be in this file.

If you'd like to import all users (and not filter out the ones that are not in the comments file), you can do this: 
```
./users_validator comments_file.txt users_file.txt True
```
This will produce a fixed_users_file.txt which contains ALL of the users in the original users file, even if the users are not contained in the comments file.

## Archive Import Validator
```
./archive_validator file.txt
```
This will produce several output files:
- fixed_file.txt: Contains the archive content which needs to be run with the archive importer.
- collections_only_file.txt: Contains the collections file which contains the archive comment counts. This can be run by DEs with the interactive comment importer.


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
