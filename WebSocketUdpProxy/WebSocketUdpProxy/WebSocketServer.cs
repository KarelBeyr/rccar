using System.Net;
using System.Net.WebSockets;
using System.Text;

namespace WebSocketUdpProxy;

public class WebSocketServer
{
    private readonly int _port;
    private UdpServer? _udpServer; // Reference to UdpServer
    private WebSocket? _currentWebSocket;
    private readonly string _htmlFilePath = "./index.html";
    CancellationTokenSource _currentConnectionCts = new CancellationTokenSource();

    public WebSocketServer(int port)
    {
        _port = port;
    }

    public void SetUdpServer(UdpServer udpServer)
    {
        _udpServer = udpServer;
    }

    public async Task StartAsync(CancellationToken cancellationToken)
    {
        var httpListener = new HttpListener();
        httpListener.Prefixes.Add($"http://*:{_port}/");
        try
        {
            httpListener.Start();
            Console.WriteLine($"WebSocket server listening on port {_port}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Failed to start WebSocket server: {ex.Message}");
            return;
        }

        Task<HttpListenerContext>? acceptTask = null;

        try
        {
            while (!cancellationToken.IsCancellationRequested)
            {
                if (acceptTask == null)
                {
                    acceptTask = httpListener.GetContextAsync();
                }
                if (acceptTask != await Task.WhenAny(acceptTask, Task.Delay(-1, cancellationToken)))
                {
                    continue; // Global cancellation (CTR+C) requested, get out of while loop
                }

                var context = acceptTask.Result;
                Console.WriteLine("got WS result");
                acceptTask = null; // Reset task for next loop iteration

                if (context.Request.IsWebSocketRequest)
                {
                    if (_currentWebSocket != null && _currentWebSocket.State == WebSocketState.Open)
                    {
                        // Forcefully close the existing WebSocket connection.
                        Console.WriteLine("Closing the existing WebSocket connection.");
                        await _currentWebSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, "New connection established", CancellationToken.None);
                    }

                    Console.WriteLine("Accepting new WebSocket connection.");
                    var webSocketContext = await context.AcceptWebSocketAsync(null);
                    _currentWebSocket = webSocketContext.WebSocket;

                    // Handle the new WebSocket connection in a non-blocking way
                    _ = HandleWebSocketAsync(_currentWebSocket, cancellationToken);
                }
                else
                {
                    await ServeHtmlPage(context, cancellationToken);
                }
            }
        }
        finally
        {
            httpListener.Close();
        }
    }

    async Task ServeHtmlPage(HttpListenerContext context, CancellationToken cancellationToken)
    {
        // Serve the HTML page for non-WebSocket requests
        try
        {
            string content = File.ReadAllText(_htmlFilePath);
            byte[] buffer = Encoding.UTF8.GetBytes(content);
            context.Response.ContentLength64 = buffer.Length;
            context.Response.ContentType = "text/html";
            await context.Response.OutputStream.WriteAsync(buffer, 0, buffer.Length, cancellationToken);
            context.Response.OutputStream.Close();
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Failed to serve HTML page: {ex.Message}");
            context.Response.StatusCode = 500; // Internal Server Error
            context.Response.Close();
        }

    }

    private async Task HandleWebSocketAsync(WebSocket webSocket, CancellationToken cancellationToken)
    {
        byte[] buffer = new byte[1024];
        try
        {
            while (webSocket.State == WebSocketState.Open && !cancellationToken.IsCancellationRequested)
            {
                var result = await webSocket.ReceiveAsync(new ArraySegment<byte>(buffer), cancellationToken);
                if (result.MessageType == WebSocketMessageType.Close || cancellationToken.IsCancellationRequested)
                {
                    await webSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, string.Empty, cancellationToken);
                    break;
                }
                else
                {
                    Console.WriteLine("WR");
                    byte[] receivedData = buffer.Take(result.Count).ToArray();
                    if (receivedData.Length > 1)
                    {
                        switch (receivedData[1]) // Type byte
                        {
                            case 0x02: // Simple latency packet
                                await Send(receivedData);
                                break;
                            case 0x01: // Control packet
                            case 0x03: // E2E latency packet
                                _udpServer?.Send(receivedData);
                                break;
                        }
                    }
                }
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"WebSocket handling error: {ex.Message}");
            // Optionally close the WebSocket if it's still open...
        }
    }

    public async Task Send(byte[] data)
    {
        if (_currentWebSocket != null && _currentWebSocket.State == WebSocketState.Open)
        {
            await _currentWebSocket.SendAsync(new ArraySegment<byte>(data), WebSocketMessageType.Binary, true, CancellationToken.None);
            Console.Write("WS");
        }
        else
        {
            Console.WriteLine("WS server tried to send packet back to WS, but it was not possible");
        }
    }
}