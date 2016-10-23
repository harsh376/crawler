## Instructions

### Create a virtual environment 

`cd ~/.../backend326`

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

`cd ~/.../backend326`
  
`nosetests`

### Deactivate virtual environment

`deactivate`

## Setup AWS

**Create instance** 

`python deploy.py`

**Configure instance**

`ssh -i <some_key.pem> ubuntu@<public_ip>`

`sudo apt-get install git`

`sudo apt-get update`

`sudo apt-get install python-pip`

`sudo apt-get install python-virtualenv`

`git clone https://github.com/harsh376/frontend326.git`

`cd frontend`

`virtualenv venv`

`source venv/bin/activate`

`pip install -r requirements.txt`
    
**Forward port 80 to 8080**

`cd`

`sudo vim /etc/sysctl.conf`

Uncomment `net.ipv4.ip_forward`

`sudo sysctl -p /etc/sysctl.conf`

`cat /proc/sys/net/ipv4/ip_forward`

`sudo iptables -A PREROUTING -t nat -i eth0 -p tcp --dport 80 -j REDIRECT --to-port 8080`
    
**Start application**

`cd frontend`

`nohup python run.py &`

`exit`
