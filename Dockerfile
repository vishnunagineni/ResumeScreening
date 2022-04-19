FROM python:alpine
RUN apk add build-base
COPY . /app
COPY ./nltk_data /root/
WORKDIR /app
RUN pip install -r requirements.txt
RUN [ "python3", "-c", "import nltk; nltk.download('stopwords')" ]
RUN cp -r /root/nltk_data /usr/local/share/nltk_data
EXPOSE 5001
ENTRYPOINT [ "python" ]
CMD [ "app.py" ]