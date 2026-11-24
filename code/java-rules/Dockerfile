FROM eclipse-temurin:17-jdk AS build
WORKDIR /src
COPY src ./src
RUN mkdir classes && javac --release 17 -d classes $(find src -name '*.java') && jar --create --file rules.jar --main-class edu.tiet.scms.RulesServer -C classes .
FROM eclipse-temurin:17-jre
WORKDIR /app
COPY --from=build /src/rules.jar .
ENTRYPOINT ["java", "-jar", "rules.jar"]
