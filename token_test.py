import requests
url = "http://localhost:8000/me"
headers = { 
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwMTA2MzQ0MzA0NCIsImV4cCI6MTc0NzYyNzYxMX0.cKRVJYSeGu_cdCvwJPRwJPwmMZyb3l7JPuW_cEiN3r0"
}
response = requests.get(url, headers=headers)
print(response.status_code)
print(response.json())