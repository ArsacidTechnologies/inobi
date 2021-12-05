from oauth2client import crypt, client

from ..config import GOOGLE_CLIENT_IDS


tag = '@verify.google:'


ID_KEY = 'sub'


def verify(token, return_full_info=True, client_ids=GOOGLE_CLIENT_IDS):
    try:
        e = None
        idinfo = None
        for client_id in client_ids:
            try:
                idinfo = client.verify_id_token(token, client_id)
                break
            except Exception as e_:
                e = e_
                continue
        else:
            raise e

        if idinfo['aud'] not in client_ids:
            raise crypt.AppIdentityError('Wrong audience')

        if idinfo['iss'] not in [
                'https://securetoken.google.com/inobi-a4760',
                'accounts.google.com',
                'https://accounts.google.com']:
            raise crypt.AppIdentityError('Wrong Issuer')

    except crypt.AppIdentityError as e:
        print('\t', e, type(e))
        return False

    if return_full_info:
        return idinfo

    return idinfo[ID_KEY]


TEST_TOKEN = 'eyJhbGciOiJSUzI1NiIsImtpZCI6IjE0ZGUxYTBmNWY0NWJkNGY4MWJjN2UyZWZlMWI3MDk1ZTM1Y2RkMjYifQ.eyJhenAiOiI3NjUzNDU4NjEwOTAtOGVvOGNtbXM2aTdxMmkyamx0Z2w4c2VrazQ1N3IyZ28uYXBwcy5nb29nbGV1c2VyY29udGVudC5jb20iLCJhdWQiOiI3NjUzNDU4NjEwOTAtOGVvOGNtbXM2aTdxMmkyamx0Z2w4c2VrazQ1N3IyZ28uYXBwcy5nb29nbGV1c2VyY29udGVudC5jb20iLCJzdWIiOiIxMDY0Njk1NzA2NzUxMTcxNDM3OTMiLCJlbWFpbCI6Imlyc2FsYWJkQGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJhdF9oYXNoIjoib1oyMmZPMmVMeGJVYU9Ka0dEZ2p3QSIsImlzcyI6Imh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbSIsImlhdCI6MTQ5OTA2MTgzOSwiZXhwIjoxNDk5MDY1NDM5LCJuYW1lIjoiQWJkdWxsYWggLi4uIiwicGljdHVyZSI6Imh0dHBzOi8vbGg1Lmdvb2dsZXVzZXJjb250ZW50LmNvbS8tY3d5VFFQcG1OS2MvQUFBQUFBQUFBQUkvQUFBQUFBQUFBQUEvQUk2eUdYd1pUZnJyWHJ1cTVzQzFmS2ExeC1TZ1ljZ2tXdy9zOTYtYy9waG90by5qcGciLCJnaXZlbl9uYW1lIjoiQWJkdWxsYWgiLCJmYW1pbHlfbmFtZSI6Ii4uLiIsImxvY2FsZSI6InJ1In0.gUhdJyA_6rPxUjEk6nXLv4eFq_EQFqF9fqOf5WeoxuF37vIjQKPuNhOlQeOPFVoi8MXQcmvZtALSIKNREux2f3yIw15xrsq_Es_ZxhOrNDQBydGoPfAhH0wm2wcq2OxvI8_yUsWikGk36AGsAyCp1WAb49S1B09R-L3HIgyZC2JNMa4X6AVnMd7Nq9EZihJSzzyre0onLLZFrX9xkWLD5LN-EOD6YDK4iXK6DdugQApxUkI7yf5mqC-1xJgsL3Sg1BCeXoEBzHDsu6Iw4fyyZyCLU6buxGYNHVHTLWR-f8qmJU1mkYHgfMrlsGIr2bTPwpIxfYCgy5UJemVmvLvwoA'


def main():
    id = verify(TEST_TOKEN)
    print(id)

if __name__ == '__main__':
    main()
