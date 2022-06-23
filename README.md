# oobir

# Install
Build the virtual and enable dependencies:

`make && source ./venv/bin/activate`

`make run`

# Docker
`docker build -t oobir .`

`docker run -d --name oobir -p 8000:8000 oobir`

`docker-compose up -d`

`python3 tests/data_load.py`


# Test
`curl http://127.0.0.1:8000/`

# Documentation:

http://127.0.0.1:8000/docs#/