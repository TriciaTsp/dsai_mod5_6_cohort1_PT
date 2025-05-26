#gemini

from flask import Flask, request, render_template, jsonify, url_for
import google.generativeai as genai
from dotenv import load_dotenv
import markdown2
import os
import sqlite3, datetime
from web3 import Web3
import requests

# Load environment variables from .env file
load_dotenv()

api_key = os.getenv('GEMINI_KEY')
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash")

app = Flask(__name__)

@app.route("/", methods=["GET","POST"])
def index():
    return(render_template("index.html"))

@app.route("/gemini", methods=["GET","POST"])
def gemini():
    print("here")
    conn = sqlite3.connect("user.db")
    c = conn.cursor()
    df = c.execute("select * from users")
    r = ""
    username = ""
    for row in c:
        username = username + " | " + str(row)
    c.close()
    conn.close()
    print("username: " + username)
    return(render_template("gemini.html", r=username))

@app.route("/gemini_reply", methods=["GET","POST"])
def gemini_reply():
    q = request.form.get("q")
    print(q)
    r = model.generate_content(q)
    r = markdown2.markdown(r.text)
    return(render_template("gemini_reply.html", r=r))

@app.route("/main", methods=["GET","POST"])
def main():
    if request.method == "POST":
        username = request.form.get("q")
        t = datetime.datetime.now()

        conn = sqlite3.connect("user.db")
        c = conn.cursor()
        c.execute("insert into users values(?, ?)",(username,t))
        conn.commit()

        # Fetch username
        c.execute("SELECT name FROM users ORDER BY timestamp DESC LIMIT 1")
        latest_user = c.fetchone()[0]

        c.close()
        conn.close()
    
    #return(render_template("gemini.html", usernames=latest_user))
    return(render_template("main.html"))

@app.route("/user_log", methods=["GET","POST"])
def user_log():
    t = datetime.datetime.now()

    conn = sqlite3.connect("user.db")
    c = conn.cursor()
    # Fetch all username
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    print("here")
    c.close()
    conn.close()
    
    return(render_template("user_log.html", usernames=users))

@app.route("/delete_log", methods=["GET","POST"])
def delete_log():
    t = datetime.datetime.now()

    conn = sqlite3.connect("user.db")
    c = conn.cursor()
    # Fetch all username
    c.execute("delete from users")
    conn.commit()
    c.close()
    conn.close()
    
    return(render_template("delete_log.html"))

@app.route("/buy_ebook", methods=["GET","POST"])
def buy_ebook():   
    return(render_template("buy_ebook.html"))

@app.route("/paynow", methods=["GET","POST"])
def paynow():
    return(render_template("paynow.html"))

@app.route("/prediction", methods=["GET","POST"])
def prediction():
    return(render_template("prediction.html"))

@app.route("/dbs_price", methods=["POST"])
def dbs_price():
    sgd = float(request.form.get("q"))
    dbs = -50.60094302*sgd + 90.22858515
    return(render_template("prediction_ans.html", r=dbs))

@app.route("/pay_ebook", methods=["GET","POST"])
def pay_ebook():

    contractAddress = Web3.to_checksum_address("0xac6fcf7ad53dcfa8a9b3c4b46071c90cd679ff0f"); #to address
    
    contractABI = [
        {
            "inputs": [],
            "stateMutability": "nonpayable",
            "type": "constructor"
        },
        {
            "inputs": [
                {
                    "internalType": "address",
                    "name": "payer1",
                    "type": "address"
                },
                {
                    "internalType": "address",
                    "name": "payee1",
                    "type": "address"
                },
                {
                    "internalType": "uint256",
                    "name": "amount1",
                    "type": "uint256"
                }
            ],
            "name": "weixin",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "transaction",
            "outputs": [
                {
                    "internalType": "address",
                    "name": "",
                    "type": "address"
                },
                {
                    "internalType": "address",
                    "name": "",
                    "type": "address"
                },
                {
                    "internalType": "uint256",
                    "name": "",
                    "type": "uint256"
                }
            ],
            "stateMutability": "view",
            "type": "function"
        }
    ];
    
    w3 = Web3(Web3.HTTPProvider('https://sepolia.infura.io/v3/927f5571e9ef49ff94e3de129e9f9766'))
    payee = "0xA32ba8347C6ec737D729aF1dFB6854Da3161aF0c";

    if w3.is_connected():
        print("Connected to Sepolia!")
        contract = w3.eth.contract(address=contractAddress, abi=contractABI)
        payer_address = request.form.get('payer')
        amount = convertAmt(w3)
        print("payer: " + str(payer_address))
        print(amount)
        payer_address = w3.to_checksum_address(payer_address)
        receipt = send_contract_tx(w3, contract.functions.weixin(payer_address, payee, amount), payer_address, private_key)
        print("Tx mined at:", receipt.transactionHash.hex())

        return(render_template("download.html"))
    else:
        print("Failed to connect.")
        return(render_template("index.html"))


def convertAmt(w3):
        sgdPrice = 0.5;
        ethToSgd = 4000; # example: 1 ETH = 4000 SGD
        ethAmount = sgdPrice / ethToSgd;

        print("ethAmount: "+ str(ethAmount))
        amountInWei = w3.to_wei(ethAmount, 'ether');
        print("weiAmount: "+ str(amountInWei))
        return amountInWei;

def send_contract_tx(w3, contract_function, sender_address, private_key):
    nonce = w3.eth.get_transaction_count(sender_address)
    gas_estimate = contract_function.estimate_gas({'from': sender_address})
    gas_price = w3.eth.gas_price

    txn = contract_function.build_transaction({
        'from': sender_address,
        'nonce': nonce,
        'gas': gas_estimate,
        'gasPrice': gas_price,
    })

    signed_txn = w3.eth.account.sign_transaction(txn, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    return receipt

@app.route('/verify_payment', methods=['POST'])
def verify_payment():
    w3 = Web3(Web3.HTTPProvider('https://sepolia.infura.io/v3/927f5571e9ef49ff94e3de129e9f9766'))
    data = request.get_json()
    tx_hash = data.get('txHash')
    payer = data.get('payer')
    contractAddress = w3.to_checksum_address(data.get('contractAddress'))

    if not tx_hash or not payer:
        return jsonify(success=False, error="Missing txHash or payer"), 400

    try:
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    except Exception as e:
        return jsonify(success=False, error="Transaction not found or timed out"), 400

    # Check status success
    if receipt.status != 1:
        return jsonify(success=False, error="Transaction failed"), 400

    #Simple example: Check transaction 'from' matches payer and to is your contract
    tx = w3.eth.get_transaction(tx_hash)
    if tx['from'].lower() != payer.lower() or tx['to'].lower() != contractAddress.lower():
        return jsonify(success=False, error="Transaction details do not match"), 400
    
    # If all checks pass, return ebook URL
    download_url = url_for('download_page')
    return jsonify(success=True, ebook_url=download_url)

@app.route('/download_page')
def download_page():
    return render_template('download_page.html')

@app.route("/start_telegram",methods=["GET","POST"])
def start_telegram():
    gemini_telegram_token = os.getenv('gemini_telegram_token')
    
    domain_url = os.getenv('WEBHOOK_URL')

    # The following line is used to delete the existing webhook URL for the Telegram bot
    delete_webhook_url = f"https://api.telegram.org/bot{gemini_telegram_token}/deleteWebhook"
    requests.post(delete_webhook_url, json={"url": domain_url, "drop_pending_updates": True})
    
    # Set the webhook URL for the Telegram bot
    set_webhook_url = f"https://api.telegram.org/bot{gemini_telegram_token}/setWebhook?url={domain_url}/telegram"
    print(set_webhook_url)
    webhook_response = requests.post(set_webhook_url, json={"url": domain_url, "drop_pending_updates": True})
    print('webhook:', webhook_response)
    if webhook_response.status_code == 200:
        # set status message
        status = "The telegram bot is running. Please check with the telegram bot. @"
    else:
        status = "Failed to start the telegram bot. Please check the logs."
    
    return render_template("telegram.html", status=status)
           
@app.route("/telegram",methods=["GET","POST"])
def telegram():
    update = request.get_json()
    if "message" in update and "text" in update["message"]:
        # Extract the chat ID and message text from the update
        chat_id = update["message"]["chat"]["id"]
        text = update["message"]["text"]
        if text == "/start":
            r_text = "Welcome to the Gemini Telegram Bot! You can ask me any finance-related questions."
        else:
            # Process the message and generate a response
            system_prompt = "You are a financial expert.  Answer ONLY questions related to finance, economics, investing, and financial markets. If the question is not related to finance, state that you cannot answer it."
            prompt = f"{system_prompt}\n\nUser Query: {text}"
            r = genmini_client.models.generate_content(
                model=genmini_model,
                contents=prompt
            )
            r_text = r.text
        
        # Send the response back to the user
        send_message_url = f"https://api.telegram.org/bot{gemini_telegram_token}/sendMessage"
        requests.post(send_message_url, data={"chat_id": chat_id, "text": r_text})
    return('ok', 200)
    
if __name__ == "__main__":
    app.run()
