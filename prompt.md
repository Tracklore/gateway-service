  I need you to update the gateway service to properly route requests to the messaging service, ensuring it
  aligns with the actual endpoints implemented in the messaging service. The messaging service has these
  specific REST API endpoints:

  Messaging Service Endpoints (from messaging service README):
   1. GET /api/v1/messaging/conversations - Fetch all conversations for a user
   2. POST /api/v1/messaging/conversations - Create a new conversation
   3. GET /api/v1/messaging/conversations/{conversation_id} - Get a specific conversation
   4. PUT /api/v1/messaging/conversations/{conversation_id} - Update a conversation
   5. DELETE /api/v1/messaging/conversations/{conversation_id} - Delete a conversation
   6. GET /api/v1/messaging/conversations/{conversation_id}/messages - Get messages for a conversation
   7. WebSocket: WS /api/v1/messaging/ws/{conversation_id} - Connect to a conversation's WebSocket

  Current Gateway Implementation:
  The gateway service currently has a generic route for messaging:

   1 @router.api_route("/messaging/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
   2 async def messaging_proxy(request: Request, path: str, current_user: dict = Depends(
     get_current_user)):
   3     """Proxy requests to messaging service with authentication"""
   4     return await _proxy_request(request, "messaging", path)

  Requirements for Update:

   1. REST API Routes:
      - Create specific route handlers for each messaging endpoint
      - Ensure proper authentication is applied to all routes
      - Handle all HTTP methods (GET, POST, PUT, DELETE) for the conversation and message management endpoints

   2. WebSocket Support:
      - The gateway needs to support WebSocket connections to the messaging service
      - WebSocket connections should be handled through the path: /api/v1/messaging/ws/{conversation_id}
      - WebSocket connections should NOT require traditional JWT authentication checks (since WebSockets don't
         use headers the same way as HTTP requests)
      - Need to implement a WebSocket proxy that can forward WebSocket connections to the messaging service

   3. Authentication Considerations:
      - REST API endpoints need to verify JWT tokens
      - WebSocket connections may need a different authentication approach (e.g., token in URL or initial
        message)
      - For WebSockets, consider implementing token validation during connection establishment

   4. Code Changes Required:

     a) Update app/api/routes.py to add:
         - Specific REST API route handlers for messaging service endpoints
         - WebSocket route handler for real-time messaging
         - Proper dependency injection for authentication where needed

     b) You may need to create a WebSocket dependency in app/dependencies/ to handle WebSocket
  authentication

   5. Architecture:
      - Keep the existing generic proxy function _proxy_request
      - Create new specific route handlers that call the appropriate proxy function
      - For WebSocket connections, you'll need a different proxy approach (using fastapi.WebSocket)

   6. Error Handling:
      - Implement proper error handling for WebSocket connections
      - Maintain existing error handling patterns for REST API calls

  Here's an example structure for the WebSocket route:

   1 @router.websocket("/api/v1/messaging/ws/{conversation_id}")
   2 async def websocket_messaging_proxy(websocket: WebSocket, conversation_id: str):
   3     # WebSocket authentication (could be handled via token in URL query params)
   4     await websocket.accept()
   5     # Implement WebSocket connection forwarding to messaging service
   6     # Use appropriate async libraries to forward messages between client and messaging service

  Please implement these updates to the gateway service to properly handle both REST API and WebSocket
  connections to the messaging service, ensuring all authentication and routing is properly implemented
  according to Tracklore's architecture.
