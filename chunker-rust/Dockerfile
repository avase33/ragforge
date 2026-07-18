FROM rust:1.79-slim AS build
WORKDIR /app
COPY Cargo.toml ./
COPY src ./src
RUN cargo build --release --bin ragforge-chunker

FROM debian:bookworm-slim
COPY --from=build /app/target/release/ragforge-chunker /usr/local/bin/ragforge-chunker
ENV RAGFORGE_CHUNKER_ADDR=0.0.0.0:8093
EXPOSE 8093
CMD ["ragforge-chunker"]
