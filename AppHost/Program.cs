using Azure.Provisioning.AppContainers;

var builder = DistributedApplication.CreateBuilder(args);

var logs = builder.AddAzureLogAnalyticsWorkspace("farming-logs");
builder.AddAzureContainerAppEnvironment("farming-env")
    .WithAzureLogAnalyticsWorkspace(logs)
    .WithDashboard(false);
var insights = builder.AddAzureApplicationInsights("farming-insights")
    .WithLogAnalyticsWorkspace(logs);

var app = builder.AddDockerfile("this-week-farming", "..")
    .WithReference(insights)
    .WithHttpEndpoint(targetPort: 8000, name: "http")
    .WithExternalHttpEndpoints()
    .PublishAsAzureContainerApp((_, containerApp) =>
    {
        containerApp.Template.Scale.MinReplicas = 1;
        containerApp.Template.Scale.MaxReplicas = 1;
        var container = containerApp.Template.Containers[0].Value!;
        container.Resources.Cpu = 0.5;
        container.Resources.Memory = "1Gi";
        container.Probes.Add(new ContainerAppProbe
        {
            ProbeType = ContainerAppProbeType.Liveness,
            HttpGet = new ContainerAppHttpRequestInfo { Path = "/healthz", Port = 8000 },
            InitialDelaySeconds = 10,
            PeriodSeconds = 30
        });
        container.Probes.Add(new ContainerAppProbe
        {
            ProbeType = ContainerAppProbeType.Readiness,
            HttpGet = new ContainerAppHttpRequestInfo { Path = "/api/guidance", Port = 8000 },
            PeriodSeconds = 10
        });
    });

// Optional on the first deployment. Set via a secret parameter on subsequent deploys.
if (!string.IsNullOrEmpty(builder.Configuration["Parameters:copilot-token"]))
    app.WithEnvironment("COPILOT_GITHUB_TOKEN", builder.AddParameter("copilot-token", secret: true));

builder.Build().Run();
