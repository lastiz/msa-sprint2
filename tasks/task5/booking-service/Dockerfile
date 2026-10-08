FROM golang:1.26-alpine AS build
WORKDIR /src
COPY main.go .
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /booking-service main.go

FROM scratch
COPY --from=build /booking-service /booking-service
USER 65532:65532
EXPOSE 8080
ENTRYPOINT ["/booking-service"]
