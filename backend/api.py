import http.client

conn = http.client.HTTPSConnection("linkedin-data-api.p.rapidapi.com")

headers = {
    'x-rapidapi-key': "62a5c8782amsh604db4ac1914deap1e6c8bjsnf1e007ce6232",
    'x-rapidapi-host': "linkedin-data-api.p.rapidapi.com"
}

conn.request("GET", "/get-company-by-domain?domain=apple.com", headers=headers)

res = conn.getresponse()
data = res.read()

print(data.decode("utf-8"))