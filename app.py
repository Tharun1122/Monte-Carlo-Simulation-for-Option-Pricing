from flask import Flask, render_template, request, jsonify
import yfinance as yf
import numpy as np
from pricing_model import OptionPricingModel

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/get-stock-data', methods=['POST'])
def get_stock_data():
    data = request.json
    ticker = data.get('ticker')
    
    if not ticker:
        return jsonify({"error": "No ticker provided"}), 400
    
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period="1y")
        
        if history.empty:
            return jsonify({"error": "Invalid ticker or no data found"}), 404
        
        current_price = history['Close'].iloc[-1]
        
        # Calculate historical volatility (annualized)
        returns = np.log(history['Close'] / history['Close'].shift(1))
        volatility = np.std(returns) * np.sqrt(252)
        
        return jsonify({
            "current_price": current_price,
            "currency": stock.info.get('currency', 'USD'),
            "volatility": volatility,
            "risk_free_rate": 0.045 # Approximate default
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/simulate', methods=['POST'])
def simulate():
    data = request.json
    try:
        S0 = float(data['S0'])
        K = float(data['K'])
        T = float(data['T'])
        r = float(data['r'])
        sigma = float(data['sigma'])
        q = float(data.get('q', 0.0))
        steps = int(data.get('steps', 252))
        sims = int(data.get('sims', 5000))
        method = data.get('method', 'standard')
        
        model = OptionPricingModel(S0, K, T, r, sigma, q)
        
        bs_results = model.calculate_bs()
        mc_results = model.simulate_mc(num_simulations=sims, num_steps=steps, method=method)
        
        return jsonify({
            "bs": bs_results,
            "mc": mc_results
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/convergence', methods=['POST'])
def convergence():
    data = request.json
    try:
        S0 = float(data['S0'])
        K = float(data['K'])
        T = float(data['T'])
        r = float(data['r'])
        sigma = float(data['sigma'])
        q = float(data.get('q', 0.0))
        method = data.get('method', 'standard')
        
        model = OptionPricingModel(S0, K, T, r, sigma, q)
        results = model.calculate_convergence(method=method)
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
