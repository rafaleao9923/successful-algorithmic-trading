#!/usr/bin/env python3
from __future__ import annotations

import datetime
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import yfinance as yf

class ContinuousFutures:
    """Handles continuous futures contracts using Yahoo Finance data"""
    
    def __init__(self, symbol: str, rollover_days: int = 5):
        """
        Initialize continuous futures handler
        
        Args:
            symbol: Root symbol for futures contracts (e.g. 'CL' for crude oil)
            rollover_days: Number of days before expiration to start rollover
        """
        self.symbol = symbol
        self.rollover_days = rollover_days
        
    def get_contract_data(self, contract: str) -> pd.DataFrame:
        """
        Get historical data for a specific futures contract
        
        Args:
            contract: Futures contract code (e.g. 'CLF2024')
            
        Returns:
            DataFrame with historical prices
        """
        try:
            # Yahoo Finance uses futures symbols like CL=F, ES=F etc.
            ticker = f"{self.symbol}{contract[-4:]}={contract[-1]}"
            data = yf.Ticker(ticker).history(period="max")
            return data[['Open', 'High', 'Low', 'Close', 'Volume']]
        except Exception as e:
            print(f"Error fetching data for {contract}: {e}")
            return pd.DataFrame()

    def futures_rollover_weights(
        self, 
        start_date: datetime.date,
        expiry_dates: Dict[str, datetime.date],
        contracts: List[str]
    ) -> pd.DataFrame:
        """
        Create rollover weights matrix for continuous futures
        
        Args:
            start_date: Start date for the continuous series
            expiry_dates: Dictionary of contract codes and their expiration dates
            contracts: List of contract codes
            
        Returns:
            DataFrame with rollover weights
        """
        dates = pd.date_range(start_date, expiry_dates[contracts[-1]], freq='B')
        roll_weights = pd.DataFrame(
            np.zeros((len(dates), len(contracts))),
            index=dates, 
            columns=contracts
        )
        
        prev_date = roll_weights.index[0]
        
        for i, (contract, ex_date) in enumerate(expiry_dates.items()):
            if i < len(expiry_dates) - 1:
                # Full weight before rollover period
                roll_weights.loc[prev_date:ex_date - pd.offsets.BDay(), contract] = 1
                
                # Rollover period weights
                roll_rng = pd.date_range(
                    end=ex_date - pd.offsets.BDay(),
                    periods=self.rollover_days + 1,
                    freq='B'
                )
                
                decay_weights = np.linspace(0, 1, self.rollover_days + 1)
                roll_weights.loc[roll_rng, contract] = 1 - decay_weights
                roll_weights.loc[roll_rng, contracts[i+1]] = decay_weights
            else:
                roll_weights.loc[prev_date:, contract] = 1
                
            prev_date = ex_date
            
        return roll_weights

    def create_continuous_series(self, contracts: List[str]) -> pd.Series:
        """
        Create continuous futures series
        
        Args:
            contracts: List of contract codes in order
            
        Returns:
            Continuous futures price series
        """
        # Get expiration dates
        expiry_dates = self._get_expiry_dates(contracts)
        
        # Get data for all contracts
        contract_data = {
            contract: self.get_contract_data(contract)
            for contract in contracts
        }
        
        # Create weights matrix
        weights = self.futures_rollover_weights(
            min(df.index[0] for df in contract_data.values()),
            expiry_dates,
            contracts
        )
        
        # Create continuous series
        prices = pd.concat(
            [df['Close'].rename(contract) for contract, df in contract_data.items()],
            axis=1
        )
        
        return (prices * weights).sum(1).dropna()

    def _get_expiry_dates(self, contracts: List[str]) -> Dict[str, datetime.date]:
        """
        Get expiration dates for contracts
        
        Args:
            contracts: List of contract codes
            
        Returns:
            Dictionary mapping contracts to expiration dates
        """
        # This is a simplified implementation - in practice you would need
        # to get actual expiration dates from the exchange or data provider
        return {
            contract: datetime.date(int(contract[-4:]), self._get_expiry_month(contract[-1]), 15)
            for contract in contracts
        }

    def _get_expiry_month(self, month_code: str) -> int:
        """Map month codes to month numbers"""
        return {'F': 1, 'G': 2, 'H': 3, 'J': 4, 'K': 5, 'M': 6,
                'N': 7, 'Q': 8, 'U': 9, 'V': 10, 'X': 11, 'Z': 12}[month_code]

if __name__ == "__main__":
    # Example usage for crude oil futures
    cf = ContinuousFutures('CL')
    contracts = ['CLF2024', 'CLG2024', 'CLH2024', 'CLJ2024']
    
    continuous_series = cf.create_continuous_series(contracts)
    print(continuous_series.tail())