using System.Net;
using System.Net.Sockets;

namespace WebSocketUdpProxy;

public class UdpServer
{
    private readonly int _port;
    private UdpClient _udpClient;
    private IPEndPoint _remoteEndPoint;

    private WebSocketServer _wsServer; // Reference to WebSocketServer

    public UdpServer(int port)
    {
        _port = port;
    }

    public void SetWebSocketServer(WebSocketServer wsServer)
    {
        _wsServer = wsServer;
    }

    public async Task StartAsync(CancellationToken cancellationToken)
    {
        _udpClient = new UdpClient(_port);
        Console.WriteLine($"UDP server listening on port {_port}");

        while (!cancellationToken.IsCancellationRequested)
        {
            var receivedResult = await _udpClient.ReceiveAsync();
            _remoteEndPoint = receivedResult.RemoteEndPoint;
            Console.WriteLine("UDP packet received");

            // Optionally, process or forward the received packet
            _wsServer?.SendToWebSocketClientAsync(receivedResult.Buffer);
        }
    }

    public void Send(byte[] data)
    {
        if (_remoteEndPoint != null)
        {
            _udpClient.Send(data, data.Length, _remoteEndPoint);
            Console.WriteLine("Packet sent to UDP client");
        }
    }
}