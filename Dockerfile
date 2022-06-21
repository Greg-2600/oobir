FROM python:3.9

WORKDIR /code

COPY ./ /code/

RUN make run

CMD ["make run"]
