# CORS Configuration for Neighbour Approved

## Overview

Cross-Origin Resource Sharing (CORS) is a security mechanism that allows or restricts web applications running at one origin (domain) to make requests for resources from a different origin. This document outlines the CORS configuration for the Neighbour Approved application.

## Development Configuration

For local development, configure the following origins in your `.env` file:

```ini
CORS_ORIGINS=["http://localhost:5173","http://localhost:8000"]
```

Where:

- `http://localhost:5173` - Vue3 development server (default Vite port)
- `http://localhost:8000` - FastAPI backend server

## Why These Settings?

- Vue3 with Vite uses port 5173 by default for development
- FastAPI runs on port 8000 by default
- Including both ensures that:
  - Frontend can make API requests to the backend
  - Backend can handle requests from the development server
  - Swagger UI/ReDoc documentation remains accessible

## Production Considerations

For production deployment, update CORS_ORIGINS to include:

```ini
CORS_ORIGINS=["https://app.neighbourapproved.com","https://api.neighbourapproved.com"]
```

Consider:

- Always use HTTPS in production
- Limit origins to specific domains
- Avoid using wildcards (`*`)
- Include CDN domains if used

## Implementation Details

The CORS configuration is implemented in FastAPI using the CORSMiddleware:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Common Issues

1. "No 'Access-Control-Allow-Origin' header" error
   - Check if the origin is included in CORS_ORIGINS
   - Verify the protocol (http/https) matches exactly

2. Preflight request failures
   - Ensure OPTIONS requests are handled correctly
   - Check if all required headers are allowed

## Security Best Practices

1. Always specify exact origins rather than using wildcards
2. Only include necessary domains in the configuration
3. Use environment-specific settings
4. Regularly review and update allowed origins
5. Consider implementing rate limiting

## Testing CORS Configuration

Test your CORS setup using:

```bash
# Test preflight request
curl -X OPTIONS http://localhost:8000/api/v1/health \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: GET" \
  -v

# Test actual request
curl http://localhost:8000/api/v1/health \
  -H "Origin: http://localhost:5173" \
  -v
```

## Debugging Tips

1. Use browser developer tools (Network tab) to inspect CORS headers
2. Check server logs for CORS-related messages
3. Verify environment variables are loaded correctly
4. Test with curl to isolate browser-specific issues

## Additional Resources

- [FastAPI CORS Guide](https://fastapi.tiangolo.com/tutorial/cors/)
- [MDN CORS Documentation](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [Vue3 Development Server Configuration](https://vitejs.dev/config/server-options.html)
