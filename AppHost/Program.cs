var builder = DistributedApplication.CreateBuilder(args);

builder.AddDockerfile("this-week-farming", "..")
    .WithHttpEndpoint(targetPort: 8000, name: "http")
    .WithExternalHttpEndpoints();

builder.Build().Run();
