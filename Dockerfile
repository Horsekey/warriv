FROM python:3

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

# Pass environment context
ARG NODE_ENV=production
ENV NODE_ENV=$NODE_ENV

CMD ["python", "/src/app/bot_runner.py"]
