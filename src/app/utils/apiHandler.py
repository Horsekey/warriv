import requests
import json

def apiRequest(method, url, data=None, headers=None):
    """
    Returns JSON response from API request.

    Args:
        method: HTTP method.
        url: URL to request.
        data: Payload of the HTTP request.
        header: Header for the HTTP request.

    Returns:
        JSON of the HTTP response. 

    Raises:
        HTTPError: 401, 403, and 429 HTTP errors.
        RequestException: Ambigious HTTP request failure.
        JSONDecodeError: Failed to decode the repsonse to JSON.
    """

    try:
        response = requests.request(method, url, data=json.dumps(data), headers=headers)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == "401":
            print(f"Error: Unauthorized. Please provide valid credentials: {e}")
        elif e.response.status_code == "403":
            print(f"Error: Forbidden. You don't have permission to access this resource: {e}")
        elif e.response.status_code == "429":
            retry_after = e.response.headers.get("Retry-After")
            if retry_after:
                print(f"Error: Too many requests. Retry after {retry_after} seconds")
                # retry strategy
            else:
                print("Error: Too Many Requests. {e}")
                
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse json data {e}")
        return e
    
    except requests.exceptions.RequestException as e:
        print(f"Error: API request failed {e}")
        return None
    