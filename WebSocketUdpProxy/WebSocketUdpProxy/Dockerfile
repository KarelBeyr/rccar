# Use the .NET 7 SDK to build the application
FROM mcr.microsoft.com/dotnet/sdk:7.0 AS build-env
WORKDIR /app

# Copy the CSPROJ file and restore any dependencies (via NUGET)
COPY *.csproj ./
RUN dotnet restore

# Copy the rest of the project files and build the release
COPY . ./
RUN dotnet publish -c Release -o out

# Generate the runtime image using .NET 7
FROM mcr.microsoft.com/dotnet/runtime:7.0
WORKDIR /app
COPY --from=build-env /app/out .
ENTRYPOINT ["dotnet", "WebSocketUdpProxy.dll"]