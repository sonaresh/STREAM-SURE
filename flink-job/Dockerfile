FROM maven:3.9.11-eclipse-temurin-17 AS build
WORKDIR /src
COPY pom.xml .
COPY src ./src
RUN mvn -q -DskipTests package
FROM flink:1.20.2-scala_2.12-java17
COPY --from=build /src/target/streamsure-flink-job-1.4.0.jar /opt/flink/usrlib/streamsure-flink-job.jar
