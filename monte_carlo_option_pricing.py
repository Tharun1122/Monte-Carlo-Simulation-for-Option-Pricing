import numpy as np
import matplotlib.pyplot as plt
import math

def norm_cdf(x):
    """Cumulative distribution function for the standard normal distribution."""
    return 0.5 * (1 + math.erf(x / np.sqrt(2.0)))

class OptionPricing:
    def __init__(self, S0, K, T, r, sigma):
        """
        Initialize the Option Pricing Model.
        
        Parameters:
        S0 (float): Current stock price
        K (float): Strike price
        T (float): Time to maturity (in years)
        r (float): Risk-free interest rate
        sigma (float): Volatility of the underlying stock
        """
        self.S0 = S0
        self.K = K
        self.T = T
        self.r = r
        self.sigma = sigma

    def black_scholes_call(self):
        """Calculate Black-Scholes price for European Call Option."""
        d1 = (np.log(self.S0 / self.K) + (self.r + 0.5 * self.sigma ** 2) * self.T) / (self.sigma * np.sqrt(self.T))
        d2 = (np.log(self.S0 / self.K) + (self.r - 0.5 * self.sigma ** 2) * self.T) / (self.sigma * np.sqrt(self.T))
        call_price = (self.S0 * norm_cdf(d1) - self.K * np.exp(-self.r * self.T) * norm_cdf(d2))
        return call_price

    def black_scholes_put(self):
        """Calculate Black-Scholes price for European Put Option."""
        d1 = (np.log(self.S0 / self.K) + (self.r + 0.5 * self.sigma ** 2) * self.T) / (self.sigma * np.sqrt(self.T))
        d2 = (np.log(self.S0 / self.K) + (self.r - 0.5 * self.sigma ** 2) * self.T) / (self.sigma * np.sqrt(self.T))
        put_price = (self.K * np.exp(-self.r * self.T) * norm_cdf(-d2) - self.S0 * norm_cdf(-d1))
        return put_price

    def monte_carlo_simulation(self, num_simulations, num_steps, option_type='call', plot=False):
        """
        Perform Monte Carlo Simulation to price the option.
        
        Parameters:
        num_simulations (int): Number of simulated paths
        num_steps (int): Number of time steps in the simulation
        option_type (str): 'call' or 'put'
        plot (bool): Whether to plot sample paths
        
        Returns:
        float: Estimated option price
        float: Standard error of the estimate
        """
        dt = self.T / num_steps
        
        if plot:
            # Generate paths
            S = np.zeros((num_steps + 1, num_simulations))
            S[0] = self.S0
            for t in range(1, num_steps + 1):
                Z = np.random.standard_normal(num_simulations)
                S[t] = S[t-1] * np.exp((self.r - 0.5 * self.sigma ** 2) * dt + self.sigma * np.sqrt(dt) * Z)
            
            # Plot first 10 paths
            plt.figure(figsize=(10, 6))
            plt.plot(S[:, :10])
            plt.grid(True)
            plt.xlabel('Time Steps')
            plt.ylabel('Stock Price')
            plt.title(f'Monte Carlo Simulation: 10 Random Stock Price Paths\nS0={self.S0}, K={self.K}, T={self.T}, Vol={self.sigma}')
            # plt.show() # Blocking the script, so we might want to save it or just skip showing if non-interactive.
            # But the plan is to run locally. I'll stick to plt.show() but be aware it might block. 
            # I will save it to a file instead to avoid blocking if the user has no display.
            plt.savefig('mc_simulation_paths.png')
            print("Plot saved to mc_simulation_paths.png")
            
            # Use terminal prices for payoff
            ST = S[-1]
            
        else:
            # Efficient end-point only method:
            Z = np.random.standard_normal(num_simulations)
            ST = self.S0 * np.exp((self.r - 0.5 * self.sigma ** 2) * self.T + self.sigma * np.sqrt(self.T) * Z)

        # Calculate Payoff
        if option_type == 'call':
            payoff = np.maximum(ST - self.K, 0)
        elif option_type == 'put':
            payoff = np.maximum(self.K - ST, 0)
        else:
            raise ValueError("Invalid option type. Use 'call' or 'put'.")

        # Discount back to present value
        option_price = np.exp(-self.r * self.T) * np.mean(payoff)
        std_error = np.exp(-self.r * self.T) * np.std(payoff) / np.sqrt(num_simulations)
        
        return option_price, std_error

if __name__ == "__main__":
    # Parameters
    S0 = 100.0    # Initial stock price
    K = 100.0     # Strike price
    T = 1.0       # Time to maturity (1 year)
    r = 0.05      # Risk-free rate (5%)
    sigma = 0.2   # Volatility (20%)
    
    simulation_count = 100000
    time_steps = 252 # Daily steps

    print(f"Pricing European Options with S0={S0}, K={K}, T={T}, r={r}, sigma={sigma}")
    print("-" * 60)

    model = OptionPricing(S0, K, T, r, sigma)

    # 1. Analytical Black-Scholes Prices
    bs_call = model.black_scholes_call()
    bs_put = model.black_scholes_put()
    
    print(f"{'Method':<20} | {'Option Type':<10} | {'Price':<10} | {'Std Error':<10}")
    print("-" * 60)
    print(f"{'Black-Scholes':<20} | {'Call':<10} | {bs_call:.4f}     | {'N/A':<10}")
    print(f"{'Black-Scholes':<20} | {'Put':<10}  | {bs_put:.4f}     | {'N/A':<10}")

    # 2. Monte Carlo Simulation
    mc_call, mc_call_sem = model.monte_carlo_simulation(simulation_count, time_steps, 'call')
    mc_put, mc_put_sem = model.monte_carlo_simulation(simulation_count, time_steps, 'put')

    print(f"{'Monte Carlo':<20} | {'Call':<10} | {mc_call:.4f}     | {mc_call_sem:.4f}")
    print(f"{'Monte Carlo':<20} | {'Put':<10}  | {mc_put:.4f}     | {mc_put_sem:.4f}")
    print("-" * 60)
    
    # Visualization (Show graph for Call option simulation)
    print("\nGenerating plot for simulated paths...")
    model.monte_carlo_simulation(100, time_steps, 'call', plot=True)
