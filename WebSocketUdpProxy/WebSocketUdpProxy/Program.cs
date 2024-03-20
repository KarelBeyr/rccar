namespace WebSocketUdpProxy;

class Program
{
    static async Task Main(string[] args)
    {
        var cts = new CancellationTokenSource();
        Console.CancelKeyPress += (sender, e) => {
            e.Cancel = true;
            cts.Cancel();
        };

        try
        {
            UdpServer udpServer = new UdpServer(12000);
            WebSocketServer wsServer = new WebSocketServer(12001);

            // Set references to each other
            udpServer.SetWebSocketServer(wsServer);
            wsServer.SetUdpServer(udpServer);

            var udpTask = udpServer.StartAsync(cts.Token);
            var wsTask = wsServer.StartAsync(cts.Token);

            // Keep the application running until cancellation is requested
            await Task.Delay(Timeout.Infinite, cts.Token);
        }
        catch (OperationCanceledException)
        {
            Console.WriteLine("Operation canceled.");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"An error occurred: {ex.Message}");
        }
        finally
        {
            // Cleanup logic if needed
            Console.WriteLine("Application is shutting down.");
        }
    }
}