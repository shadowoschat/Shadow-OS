from Backend.AuthDB import verify_user

user = verify_user('Shadow@123', '379037@')
if user:
    print('LOGIN_OK')
    print(user['username'])
    print(user['email'])
    print(user['role'])
    print(user['first_name'])
    print(user['last_name'])
else:
    print('LOGIN_FAIL')
