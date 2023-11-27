# dolpa

dolpa is simple, easy to use library made for API-testing.

## Installation

dolpa is available in PyPI.

`python -m pip install dolpa`

## How to use
In a nutshell, dolpa parses your json file which contains
information about your API tests. Your JSON file should
have the following schema:

```
{
  "config": {
    "base_url": "http://localhost:8000",
    "headers": {
      "client-app": "SHM"
    }
  },
  "calls": [
    {
      "resource": "/login",
      "method": "POST",
      "body": {
        "currentUser": "alex.martin",
        "currentState": "healthy"
      },
      "headers": {
        "app-status": "current"
      },
      "saves": {
        "authToken": "$.auth_token"
      },
      "assertions": {
        "responseCheckAssertion": "responseSent==yes"
      }
    },
    {
      "resource": "/users",
      "method": "POST",
      "body": {
        "currentUser": "alex.martin",
        "currentState": "healthy"
      },
      "headers": {
        "app-status": "current"
      },
      "saves": {
        "current_block": "$.currentDepartment.currentBlock",
        "currentFriend": "$.currentDepartment.departmentInfo.employees[2]"
      },
      "assertions": {
        "nameCheck": "$.currentDepartment.departmentInfo.employees[2]==Tammy"
      }
    },
    {
      "resource": "/preference",
      "method": "POST",
      "body": {
        "currentUser": "alex.martin",
        "currentState": "healthy"
      },
      "headers": {
        "app-status": "current"
      },
      "saves": {
        "$.currentDepartment.currentBlock": "current_block"
      },
      "assertions": {
        "nameCheck": "$.workingBlock=={{current_block}}",
        "friendCheck": "$.friend=={{currentFriend}}"
      }
    }
  ]
}
```

`config` can be any valid JSON. Keys of `config` will remain as
global variable that can be accessed using `{{<key>}}` anywhere
in the call definition.

### So how to run API tests then?

You should start by making folder for your API tests where JSON files
containing tests like above are stored. You can have multiple test folders inside
the root test folder. When you run your API tests, it only picks JSON files
for testing inside the root and subsequently, sub-folders.

Here is how you start your tests:
```
from dolpa import run_bulk_api_tests

run_bulk_api_tests('/User/home/test-user/test-folder-path')
```
That's all the code you need to run your tests. 

### But wait... my test-cases are little more complicated than that!

Yeah, it's seldom that simple! 

However, dolpa makes it super easy to handle those kind of situations. Just write your API-tests
JSON files and treat them like each of them are unrelated when you reference them their identifier. You
can build complex API-tests relationship as follows:
```
    test_handler = get_api_test_handler('/Users/home/poweruser/test.json')
    first_call = test_handler.run(1)
    if first_call.response.status_code == 200:
        second_call = test_handler.run(2)
        ...
```
The above code already abstracts away assertions and other details in the JSON file so you don't have
to worry about pesky if/else conditions and can focus on the core-logic of your tests.
Enjoy!