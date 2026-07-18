FROM golang:1.22-alpine AS build
WORKDIR /app
COPY go.mod ./
COPY main.go ./
COPY internal ./internal
RUN CGO_ENABLED=0 go build -o /crawler .

FROM alpine:3.20
WORKDIR /app
COPY --from=build /crawler /usr/local/bin/crawler
COPY corpus ./corpus
ENV RAGFORGE_ADDR=:8080
ENV RAGFORGE_WATCH_DIR=/app/corpus
EXPOSE 8080
CMD ["crawler"]
