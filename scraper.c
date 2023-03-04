// started with https://www.educative.io/edpresso/how-to-implement-tcp-sockets-in-c
// and the example in https://www.man7.org/linux/man-pages/man3/getaddrinfo.3.html

#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <arpa/inet.h>

#include <netdb.h> // For getaddrinfo
#include <unistd.h> // for close
#include <stdlib.h> // for exit
int main(void)
{
    int socket_desc;
    struct sockaddr_in server_addr;
    char server_message[2000], client_message[2000];
    char address[100];

    struct addrinfo *result;
    
    // Clean buffers:
    memset(server_message,'\0',sizeof(server_message));
    memset(client_message,'\0',sizeof(client_message));
    
    // Create socket:
    socket_desc = socket(AF_INET, SOCK_STREAM, 0);
    
    if(socket_desc < 0){
        printf("Unable to create socket\n");
        return -1;
    }
    
    printf("Socket created successfully\n");

    struct addrinfo hints;
    memset (&hints, 0, sizeof (hints));
    hints.ai_family = PF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_flags |= AI_CANONNAME;
    
    // get the ip of the page we want to scrape
    int out = getaddrinfo ("www.cs.umanitoba.ca", NULL, &hints, &result);
    // fail gracefully
    if (out != 0) {
        fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(out));
        exit(EXIT_FAILURE);
    }
    
    // ai_addr is a struct sockaddr
    // so, we can just use that sin_addr
    struct sockaddr_in *serverDetails =  (struct sockaddr_in *)result->ai_addr;
    
    // Set port and IP the same as server-side:
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(80);
    //server_addr.sin_addr.s_addr = inet_addr("127.0.0.1");
    server_addr.sin_addr = serverDetails->sin_addr;
    
     // converts to octets
    printf("Convert...\n");
    inet_ntop (server_addr.sin_family, &server_addr.sin_addr, address, 100);
    printf("Connecting to %s\n", address);
    // Send connection request to server:
    if(connect(socket_desc, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0){
        printf("Unable to connect\n");
        exit(EXIT_FAILURE);
    }
    printf("Connected with server successfully\n");
    
    // Get input from the user:
    /* header is:
    GET /~robg/3010/index.html HTTP/1.1
    Host: www.cs.umanitoba.ca
    
    */
    
    char request[] = "GET /~robg/3010/index.html HTTP/1.1\r\nHost: www.cs.umanitoba.ca\r\n\r\n";
    printf("Sending:\n%s\n", request);
    // Send the message to server:
    printf("Sending request, %lu bytes\n", strlen(request));
    if(send(socket_desc, request, strlen(request), 0) < 0){
        printf("Unable to send message\n");
        return -1;
    }
    
    // Receive the server's response:
    if(recv(socket_desc, server_message, sizeof(server_message), 0) < 0){
        printf("Error while receiving server's msg\n");
        return -1;
    }
    
    printf("Server's response: %s\n",server_message);
    
    // Close the socket:
    close(socket_desc);
    
    return 0;
}
