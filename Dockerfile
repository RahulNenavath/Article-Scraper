FROM public.ecr.aws/lambda/python:3.7

COPY requirements.txt .

RUN /var/lang/bin/python3.7 -m pip install --upgrade pip

RUN pip install --upgrade -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY src/ .

COPY src/app.py ${LAMBDA_TASK_ROOT}

CMD ["app.handler"]