FROM python:3-slim

ARG WORKDIR=/opt/krilog
RUN mkdir -p ${WORKDIR}
WORKDIR ${WORKDIR}

ENV LOG_DIR=${WORKDIR}/logs
ENV DATA_DIR=${WORKDIR}/data

COPY requirements.txt ${WORKDIR}/
RUN python3 -m pip install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install uvicorn
COPY . ${WORKDIR}
EXPOSE 8000
# RUN python manage.py collectstatic --noinput

ENTRYPOINT ["python3"]

# CMD ["manage.py", "runserver", "0.0.0.0:8000"]
# CMD ["-m", "uvicorn", "krilog.asgi:application"]
CMD ["-m", "gunicorn", "krilog.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
