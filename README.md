When called by a client and given minimum and maximum values, this microservice will return a random number within the given range.


How to REQUEST data
Define the parameters, then form a get request from the server.

import requests
declare low and high values
response = requests.get("http://localhost:5000/random", params={"min": low, "max": high})


How to RECEIVE data
Take the data from the response and interpret it.

data = response.json()
number = data["result"]

```
UML Sequence Diagram 
Client                           RNG_Microservice
+-+                                     |
| |                                     |
| |      GET /random?min=1&max=100     +-+ 
| | ——————————————————————————————————>| | 
| |                                    | | 
| |                              Read min and max
| |                                    | | 
| |                             Validate Parameters
| |                                    | | 
| |                           Generate random number
| |                                    | | 
| |                            Create JSON response
| |                                    | | 
| |             HTTP 200 OK            | | 
| |           {"number": 89}           | | 
| | <- - - - - - - - - - - - - - - - - | | 
| |                                    +-+ 
| |   Read JSON response                |
| |   Extract "number"                  | 
| |                                     |
| |                                     |
+-+                                 
```
