import numpy as np
import math

# Reusing the logic from the initial script but making it pure for import

def norm_cdf(x):
    """Cumulative distribution function for the standard normal distribution."""
    return 0.5 * (1 + math.erf(x / np.sqrt(2.0)))

class OptionPricingModel:
    def __init__(self, S0, K, T, r, sigma, q=0.0):
        self.S0 = float(S0)
        self.K = float(K)
        self.T = float(T)
        self.r = float(r)
        self.sigma = float(sigma)
        self.q = float(q)

    def calculate_bs(self):
        """Returns dictionary with Black-Scholes Call and Put prices."""
        # Adjusted for dividend yield q
        d1 = (np.log(self.S0 / self.K) + (self.r - self.q + 0.5 * self.sigma ** 2) * self.T) / (self.sigma * np.sqrt(self.T))
        d2 = d1 - self.sigma * np.sqrt(self.T)
        
        call_price = (self.S0 * np.exp(-self.q * self.T) * norm_cdf(d1) - self.K * np.exp(-self.r * self.T) * norm_cdf(d2))
        put_price = (self.K * np.exp(-self.r * self.T) * norm_cdf(-d2) - self.S0 * np.exp(-self.q * self.T) * norm_cdf(-d1))
        
        return {
            "call_price": call_price,
            "put_price": put_price
        }

    def simulate_mc(self, num_simulations=10000, num_steps=252, method='standard'):
        """
        Returns dictionary with MC Call/Put prices, StdErrors, and Sample Paths.
        Methods: 'standard', 'antithetic', 'control_variate'
        """
        dt = self.T / num_steps
        discount_factor = np.exp(-self.r * self.T)
        
        # Helper to get terminal prices
        def generate_paths(sims, antithetic=False):
            if antithetic:
                # Generate half the normal random variables
                half_sims = sims // 2
                Z = np.random.standard_normal((num_steps, half_sims))
                Z = np.concatenate((Z, -Z), axis=1) # Antithetic pairs
            else:
                Z = np.random.standard_normal((num_steps, sims))
            
            # Full path generation for plotting (first 20)
            S = np.zeros((num_steps + 1, sims))
            S[0] = self.S0
            
            # Vectorized path generation
            # log S_t = log S_{t-1} + (r - q - 0.5*sigma^2)*dt + sigma*sqrt(dt)*Z
            drift = (self.r - self.q - 0.5 * self.sigma ** 2) * dt
            diffusion = self.sigma * np.sqrt(dt) * Z
            
            # Accumulate increments
            log_returns = np.cumsum(drift + diffusion, axis=0)
            S[1:] = self.S0 * np.exp(log_returns)
            
            return S

        # Run Simulation
        S = generate_paths(num_simulations, antithetic=(method=='antithetic'))
        ST = S[-1]
        
        # Payoffs
        call_payoff = np.maximum(ST - self.K, 0)
        put_payoff = np.maximum(self.K - ST, 0)
        
        if method == 'control_variate':
            # Control Variate: Use underlying stock S_T as control (martingale under risk-neutral)
            # Expected[S_T] = S0 * exp((r-q)T)
            # CV = Payoff - beta * (S_T - E[S_T])
            
            exp_ST = self.S0 * np.exp((self.r - self.q) * self.T)
            cov_call = np.cov(call_payoff, ST)[0, 1]
            var_ST = np.var(ST)
            beta_call = cov_call / var_ST if var_ST > 0 else 0
            
            cov_put = np.cov(put_payoff, ST)[0, 1]
            beta_put = cov_put / var_ST if var_ST > 0 else 0
            
            call_p = call_payoff - beta_call * (ST - exp_ST)
            put_p = put_payoff - beta_put * (ST - exp_ST)
            
            mc_call = discount_factor * np.mean(call_p)
            mc_call_err = discount_factor * np.std(call_p) / np.sqrt(num_simulations)
            
            mc_put = discount_factor * np.mean(put_p)
            mc_put_err = discount_factor * np.std(put_p) / np.sqrt(num_simulations)
        
        else:
            # Standard & Antithetic (variance reduction comes from Z, -Z correlation in Payoff)
            mc_call = discount_factor * np.mean(call_payoff)
            mc_call_err = discount_factor * np.std(call_payoff) / np.sqrt(num_simulations)
            
            mc_put = discount_factor * np.mean(put_payoff)
            mc_put_err = discount_factor * np.std(put_payoff) / np.sqrt(num_simulations)
        
        # Sample paths (subset)
        sample_paths = S[:, :20].T.tolist()
        
        return {
            "call_price": mc_call,
            "call_stderr": mc_call_err,
            "put_price": mc_put,
            "put_stderr": mc_put_err,
            "paths": sample_paths,
            "steps": list(range(num_steps + 1))
        }

    def calculate_convergence(self, method='standard'):
        """
        Calculate prices for increasing number of simulations to show convergence.
        """
        # Range of simulation counts: 100 to 10000
        sim_counts = np.linspace(100, 10000, 20, dtype=int)
        call_prices = []
        
        # Analytical Price for baseline
        bs_price = self.calculate_bs()['call_price']
        
        for n in sim_counts:
            # Quick run (less steps for speed in loop, or keep 252)
            res = self.simulate_mc(num_simulations=int(n), num_steps=100, method=method)
            call_prices.append(res['call_price'])
            
        return {
            "x": sim_counts.tolist(),
            "y": call_prices,
            "bs_line": [bs_price] * len(sim_counts)
        }
