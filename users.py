import requests
import tokens

def check_user_follows(access_token, user_id):
    url = "https://api.spotify.com/v1/me/following/contains?type=user&ids=" + str(user_id)
    response = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )
    if str(response) != "<Response [200]>":
        print("error in check_user_follows : " + str(response))
        return None
    json_resp = response.json()
    return json_resp[0]