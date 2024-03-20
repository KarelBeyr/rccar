using System.Net;
using System.Net.WebSockets;

namespace WebSocketUdpProxy;

public class WebSocketServer
{
    private readonly int _port;
    private UdpServer _udpServer; // Reference to UdpServer
    private WebSocket _currentWebSocket;

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
        HttpListener httpListener;
        try
        {
            httpListener = new HttpListener();
            httpListener.Prefixes.Add($"http://*:{_port}/");
            httpListener.Start();
            Console.WriteLine($"WebSocket server listening on port {_port}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Failed to start WebSocket server: {ex.Message}");
            return;
        }

        while (!cancellationToken.IsCancellationRequested)
        {
            var context = await httpListener.GetContextAsync();
            if (context.Request.IsWebSocketRequest)
            {
                var webSocketContext = await context.AcceptWebSocketAsync(null);
                _currentWebSocket = webSocketContext.WebSocket;
                Console.WriteLine("WebSocket client connected.");

                // Handle WebSocket communication in a loop
                byte[] buffer = new byte[1024];
                while (_currentWebSocket.State == WebSocketState.Open)
                {
                    var result = await _currentWebSocket.ReceiveAsync(new ArraySegment<byte>(buffer), cancellationToken);
                    if (result.MessageType == WebSocketMessageType.Close)
                    {
                        await _currentWebSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, string.Empty, cancellationToken);
                    }
                    else
                    {
                        // Process received packet
                        byte[] receivedData = buffer.Take(result.Count).ToArray();
                        // Determine action based on packet type
                        if (receivedData.Length > 1)
                        {
                            switch (receivedData[1]) // Type byte
                            {
                                case 0x02: // Simple latency packet
                                           // Echo back to WebSocket client
                                    await SendToWebSocketClientAsync(receivedData); // webSocket.SendAsync(new ArraySegment<byte>(receivedData, 0, result.Count), WebSocketMessageType.Binary, true, cancellationToken);
                                    break;
                                case 0x01: // Control packet
                                case 0x03: // E2E latency packet
                                           // Forward to UDP client
                                    _udpServer.Send(receivedData);
                                    break;
                            }
                        }
                    }
                }
            }
            else
            {
                context.Response.StatusCode = 400;
                context.Response.Close();
            }
        }
    }

    public async Task SendToWebSocketClientAsync(byte[] data)
    {
        if (_currentWebSocket != null && _currentWebSocket.State == WebSocketState.Open)
        {
            Console.WriteLine("WS server sending packet back to WS");
            await _currentWebSocket.SendAsync(new ArraySegment<byte>(data), WebSocketMessageType.Binary, true, CancellationToken.None);
        } else
        {
            Console.WriteLine("WS server tried to send packet back to WS, but it was not possible");
        }
    }
}