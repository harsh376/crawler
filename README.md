## Instructions

### Create a virtual environment 

`cd ~/.../project`

`virtualenv -p <SOME_PYTHON_PATH> venv`

`virtualenv -p /usr/bin/python2.7 venv`

[http://docs.python-guide.org/en/latest/dev/virtualenvs/]

### Activate virtual environment

`source venv/bin/activate`

### Install dependencies

`pip install -r requirements.txt`

### Running the app

`python crawler.py`

### Running the tests

`cd ~/.../project`
  
`nosetests`

### Deactivate virtual environment

`deactivate`
