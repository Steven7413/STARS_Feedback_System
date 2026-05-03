from pyngrok import ngrok
import time
try:
    ngrok.set_auth_token('38OfonLs2VAtzEZh59IMa3UhfPO_6jhT1CsyFs8T77ifAzJGK')
    url = ngrok.connect(5001).public_url
    print(f'TEST_SUCCESS: {url}')
    ngrok.kill()
except Exception as e:
    print(f'TEST_FAILED: {e}')
