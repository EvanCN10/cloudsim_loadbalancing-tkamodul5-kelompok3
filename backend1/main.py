from flask import Flask, jsonify, request
import socket
import hashlib

app = Flask(__name__)

products = [
    {"id": 1, "name": "Laptop", "price": 12000000},
    {"id": 2, "name": "Mouse", "price": 150000},
    {"id": 3, "name": "Keyboard", "price": 350000}
]

@app.route('/')
def home():
    return jsonify({
        "message": "Server 1 - TokoKita",
        "hostname": socket.gethostname()
    })

@app.route('/products')
def get_products():
    return jsonify(products)

@app.route('/catalogue')
def catalogue():
    return jsonify({
        "server": "Server 1 - TokoKita",
        "hostname": socket.gethostname(),
        "products": products
    })

@app.route('/checkout', methods=['POST'])
def checkout():
    # Simulasi beban CPU berat — hash iteratif
    result = "start"
    for i in range(100000):
        result = hashlib.sha256(f"{result}{i}".encode()).hexdigest()

    return jsonify({
        "server": "Server 1 - TokoKita",
        "hostname": socket.gethostname(),
        "status": "success",
        "message": "Checkout berhasil diproses",
        "order_id": result[:8]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)