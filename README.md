[![Build Status](https://travis-ci.org/harsh376/backend326.svg?branch=master)](https://travis-ci.org/harsh376/backend326)

## Instructions

### Setup virtualenv

1. `cd ~/.../backend326`

2. `virtualenv -p <SOME_PYTHON_PATH> venv`
   
    or
    
    `virtualenv -p /usr/bin/python2.7 venv`

    [http://docs.python-guide.org/en/latest/dev/virtualenvs/]
    
3. Activate virtualenv

    `source venv/bin/activate`

4. Install dependencies in virtualenv

    `pip install -r requirements.txt`
    
5. Deactivate virtualenv

    `deactivate`

### Running the crawler

1. Activate the virtualenv

2. `python crawler.py`


### Running the tests

1. Activate the virtualenv
  
2. `nosetests -v`


### Deploy frontend app on EC2 instance

1. Add AWS credentials in `~/.aws/credentials` in the form:

    ``` 
    
        [csc326]
        
        aws_access_key_id = ####
        
        aws_secret_access_key = #####
    ```

2. `cd ~/.../backend326`

3. Activate virtualenv

4. `python deploy.py`
