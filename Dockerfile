FROM python:3.13

WORKDIR /tbotd

COPY requirements.txt ./
RUN pip install --root-user-action=ignore --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./main.py" ]

