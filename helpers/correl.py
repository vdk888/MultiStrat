#!/usr/bin/env python3
"""
ETF Similarity Analysis

This script fetches historical price data for multiple ETF groups,
calculates similarity metrics (correlation, covariance, etc.),
and visualizes the relationships between assets.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram, linkage
import argparse
from datetime import datetime, timedelta

# Define ETF groups
ETF_GROUPS = {
    "Major US Equity Market Indices": [
        "SPY", "QQQ", "DIA", "IWM", "VTI", "RSP", "IJH", 
        "OEF", "VB", "VO", "MAGS", "ESGU"
    ],
    "US Equity Styles": [
        "VUG", "VTV", "SPLV", "SPHQ", "MOAT", "SPMO", "COWZ", 
        "IWO", "IWN", "AVUV", "VOT", "MGK"
    ],
    "US Sector ETFs": [
        "XLF", "XLK", "XLE", "XLV", "XLI", "XLP", "XLY", 
        "XLU", "XLC", "XLRE", "KRE", "SMH", "XOP"
    ]
}

def fetch_etf_data(tickers, period="1y", interval="1d"):
    """Fetch historical price data for the given ETF tickers."""
    print(f"Fetching data for {len(tickers)} ETFs...")
    
    # Download data for all tickers at once
    data = yf.download(
        tickers=tickers,
        period=period,
        interval=interval,
        group_by='ticker',
        auto_adjust=True,
        progress=False
    )
    
    # If only one ticker is provided, restructure the data
    if len(tickers) == 1:
        ticker = tickers[0]
        data = pd.DataFrame({ticker: data['Close']})
        return data
    
    # Extract closing prices for each ticker
    close_prices = pd.DataFrame()
    
    for ticker in tickers:
        if (ticker, 'Close') in data.columns:
            close_prices[ticker] = data[(ticker, 'Close')]
    
    # Check if we have data
    if close_prices.empty:
        raise ValueError("No data was fetched. Check your tickers and internet connection.")
    
    # Handle missing values
    close_prices = close_prices.dropna(axis=1, thresh=int(0.7 * len(close_prices)))  # Keep columns with at least 70% data
    close_prices = close_prices.fillna(method='ffill')  # Forward fill remaining NA values
    
    print(f"Successfully fetched data for {close_prices.shape[1]} ETFs")
    return close_prices

def calculate_returns(prices_df, method='pct_change'):
    """Calculate returns from price data."""
    if method == 'pct_change':
        returns = prices_df.pct_change().dropna()
    elif method == 'log':
        returns = np.log(prices_df / prices_df.shift(1)).dropna()
    else:
        raise ValueError("Method must be either 'pct_change' or 'log'")
    
    return returns

def calculate_similarity_metrics(returns_df):
    """Calculate similarity metrics between ETFs based on returns."""
    metrics = {}
    
    # Correlation matrix
    metrics['correlation'] = returns_df.corr()
    
    # Covariance matrix
    metrics['covariance'] = returns_df.cov()
    
    # Normalized euclidean distance matrix
    returns_normalized = (returns_df - returns_df.mean()) / returns_df.std()
    dist_matrix = euclidean_distances(returns_normalized.T)
    metrics['distance'] = pd.DataFrame(
        dist_matrix, 
        index=returns_df.columns, 
        columns=returns_df.columns
    )
    
    # Beta relative to SPY (if SPY is in the dataset)
    if 'SPY' in returns_df.columns:
        spy_returns = returns_df['SPY']
        betas = {}
        
        for col in returns_df.columns:
            if col != 'SPY':
                # Calculate beta: Cov(asset, SPY) / Var(SPY)
                cov_with_spy = returns_df[col].cov(spy_returns)
                var_spy = spy_returns.var()
                betas[col] = cov_with_spy / var_spy
        
        metrics['beta_to_spy'] = pd.Series(betas)
    
    return metrics

def cluster_etfs(similarity_matrix, n_clusters=None):
    """Cluster ETFs based on similarity matrix."""
    # Use correlation as similarity, so convert to distance
    if similarity_matrix.min().min() >= -1 and similarity_matrix.max().max() <= 1:
        # This is likely a correlation matrix
        distance_matrix = 1 - similarity_matrix
    else:
        # This is likely already a distance measure
        distance_matrix = similarity_matrix
    
    # Perform hierarchical clustering
    Z = linkage(distance_matrix, method='ward')
    
    # If n_clusters is specified, perform the clustering
    if n_clusters:
        clustering = AgglomerativeClustering(
            n_clusters=n_clusters, 
            linkage='ward'
        )
        clusters = clustering.fit_predict(distance_matrix)
        return Z, clusters
    
    return Z, None

def plot_correlation_heatmap(correlation_matrix, title="ETF Correlation Matrix"):
    """Plot a correlation heatmap."""
    plt.figure(figsize=(14, 12))
    mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))
    cmap = sns.diverging_palette(230, 20, as_cmap=True)
    
    sns.heatmap(
        correlation_matrix, 
        mask=mask,
        cmap=cmap,
        vmax=1, 
        vmin=-1, 
        center=0,
        square=True, 
        linewidths=.5, 
        cbar_kws={"shrink": .5},
        annot=True,
        fmt=".2f",
        annot_kws={"size": 8}
    )
    
    plt.title(title, fontsize=16)
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.yticks(fontsize=10)
    plt.tight_layout()
    
    return plt.gcf()

def plot_dendrogram(linkage_matrix, labels, title="ETF Hierarchical Clustering"):
    """Plot a dendrogram of ETF clusters."""
    plt.figure(figsize=(14, 8))
    
    dendrogram(
        linkage_matrix,
        labels=labels,
        orientation='top',
        distance_sort='descending',
        show_leaf_counts=True,
        leaf_font_size=12
    )
    
    plt.title(title, fontsize=16)
    plt.xlabel('ETFs', fontsize=14)
    plt.ylabel('Distance', fontsize=14)
    plt.xticks(rotation=90)
    plt.tight_layout()
    
    return plt.gcf()

def find_most_similar_pairs(similarity_matrix, top_n=10, metric_name="Correlation"):
    """Find most similar pairs of ETFs based on a similarity metric."""
    # For correlation/covariance, higher values indicate more similarity
    # For distance, lower values indicate more similarity
    is_distance = metric_name.lower() == "distance"
    
    # Create a copy of the matrix to modify
    matrix_copy = similarity_matrix.copy()
    
    # Set diagonal values to NaN to ignore self-correlations
    np.fill_diagonal(matrix_copy.values, np.nan)
    
    pairs = []
    for _ in range(top_n):
        if is_distance:
            # For distance, find minimum value
            min_val = matrix_copy.min().min()
            if np.isnan(min_val):
                break
                
            # Find indices of minimum value
            idx = matrix_copy.stack().idxmin()
            
            # Store the pair
            etf1, etf2 = idx
            value = matrix_copy.loc[etf1, etf2]
            pairs.append((etf1, etf2, value))
            
            # Set the values to NaN to find the next minimum
            matrix_copy.loc[etf1, etf2] = np.nan
            matrix_copy.loc[etf2, etf1] = np.nan
        else:
            # For correlation/covariance, find maximum value
            max_val = matrix_copy.max().max()
            if np.isnan(max_val):
                break
                
            # Find indices of maximum value
            idx = matrix_copy.stack().idxmax()
            
            # Store the pair
            etf1, etf2 = idx
            value = matrix_copy.loc[etf1, etf2]
            pairs.append((etf1, etf2, value))
            
            # Set the values to NaN to find the next maximum
            matrix_copy.loc[etf1, etf2] = np.nan
            matrix_copy.loc[etf2, etf1] = np.nan
    
    return pd.DataFrame(pairs, columns=['ETF1', 'ETF2', metric_name])

def calculate_rolling_correlation(prices_df, window=90):
    """Calculate rolling correlation matrix over time."""
    returns = calculate_returns(prices_df)
    
    # Get all possible pairs of ETFs
    etfs = returns.columns
    etf_pairs = [(etf1, etf2) for i, etf1 in enumerate(etfs) for etf2 in etfs[i+1:]]
    
    # Calculate rolling correlation for each pair
    rolling_corr = pd.DataFrame(index=returns.index[window-1:])
    
    for etf1, etf2 in etf_pairs:
        pair_name = f"{etf1}_{etf2}"
        rolling_corr[pair_name] = returns[etf1].rolling(window=window).corr(returns[etf2])
    
    return rolling_corr, etf_pairs

def find_most_stable_correlations(rolling_corr_df, etf_pairs, top_n=10):
    """Find ETF pairs with the most stable correlations over time."""
    # Calculate standard deviation of rolling correlations
    corr_std = rolling_corr_df.std()
    
    # Create a DataFrame with pair names and their correlation stability
    stability_df = pd.DataFrame({
        'ETF_Pair': corr_std.index,
        'Correlation_StdDev': corr_std.values
    })
    
    # Sort by stability (lower std dev means more stable)
    stability_df = stability_df.sort_values('Correlation_StdDev')
    
    # Get the top N most stable pairs
    top_stable = stability_df.head(top_n)
    
    # Split the pair names into separate columns
    result = pd.DataFrame()
    result['ETF1'] = top_stable['ETF_Pair'].apply(lambda x: x.split('_')[0])
    result['ETF2'] = top_stable['ETF_Pair'].apply(lambda x: x.split('_')[1])
    result['Correlation_StdDev'] = top_stable['Correlation_StdDev']
    
    # Add the average correlation for these pairs
    result['Avg_Correlation'] = [
        rolling_corr_df[f"{row['ETF1']}_{row['ETF2']}"].mean() 
        for _, row in result.iterrows()
    ]
    
    return result

def main():
    parser = argparse.ArgumentParser(description='Analyze ETF similarity based on price data.')
    parser.add_argument('-p', '--period', default='1y', help='Period to fetch data for (e.g., 1y, 2y, 5y)')
    parser.add_argument('-i', '--interval', default='1d', help='Data interval (e.g., 1d, 1wk)')
    parser.add_argument('-g', '--group', choices=['all', '1', '2', '3'], default='all', 
                        help='ETF group to analyze (all, 1, 2, or 3)')
    parser.add_argument('-t', '--top', type=int, default=10, help='Number of top similar pairs to show')
    parser.add_argument('-c', '--clusters', type=int, default=5, help='Number of clusters for analysis')
    parser.add_argument('-o', '--output', help='Output directory for saving plots and results')
    parser.add_argument('--no-plots', action='store_true', help='Skip generating plots')
    
    args = parser.parse_args()
    
    # Determine which ETFs to analyze
    all_etfs = []
    if args.group == 'all':
        for group_etfs in ETF_GROUPS.values():
            all_etfs.extend(group_etfs)
    elif args.group == '1':
        all_etfs = ETF_GROUPS["Major US Equity Market Indices"]
    elif args.group == '2':
        all_etfs = ETF_GROUPS["US Equity Styles"]
    elif args.group == '3':
        all_etfs = ETF_GROUPS["US Sector ETFs"]
    
    # Remove duplicates while preserving order
    all_etfs = list(dict.fromkeys(all_etfs))
    
    # Fetch price data
    prices = fetch_etf_data(all_etfs, period=args.period, interval=args.interval)
    
    # Calculate returns
    returns = calculate_returns(prices)
    
    # Calculate similarity metrics
    metrics = calculate_similarity_metrics(returns)
    
    # Perform hierarchical clustering based on correlation
    Z, _ = cluster_etfs(metrics['correlation'], n_clusters=args.clusters)
    
    # Display most similar ETF pairs for different metrics
    print("\n=== Most Similar ETF Pairs by Correlation ===")
    corr_pairs = find_most_similar_pairs(metrics['correlation'], top_n=args.top, metric_name="Correlation")
    print(corr_pairs.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    
    print("\n=== Most Similar ETF Pairs by Covariance ===")
    cov_pairs = find_most_similar_pairs(metrics['covariance'], top_n=args.top, metric_name="Covariance")
    print(cov_pairs.to_string(index=False, float_format=lambda x: f"{x:.6f}"))
    
    print("\n=== Most Similar ETF Pairs by Distance ===")
    dist_pairs = find_most_similar_pairs(metrics['distance'], top_n=args.top, metric_name="Distance")
    print(dist_pairs.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    
    # Calculate and display rolling correlation stability
    print("\n=== ETF Pairs with Most Stable Correlations ===")
    rolling_corr, etf_pairs = calculate_rolling_correlation(prices, window=60)
    stable_pairs = find_most_stable_correlations(rolling_corr, etf_pairs, top_n=args.top)
    print(stable_pairs.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    
    # Display beta to SPY if available
    if 'beta_to_spy' in metrics:
        print("\n=== ETF Betas Relative to SPY ===")
        beta_series = metrics['beta_to_spy'].sort_values()
        print(beta_series.to_string(float_format=lambda x: f"{x:.4f}"))
    
    # Generate plots if not disabled
    if not args.no_plots:
        # Correlation heatmap
        corr_fig = plot_correlation_heatmap(metrics['correlation'], "ETF Correlation Matrix")
        
        # Dendrogram
        dend_fig = plot_dendrogram(Z, labels=metrics['correlation'].index, title="ETF Hierarchical Clustering")
        
        # Save plots if output directory is specified
        if args.output:
            import os
            os.makedirs(args.output, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            corr_fig.savefig(os.path.join(args.output, f"correlation_heatmap_{timestamp}.png"), dpi=300)
            dend_fig.savefig(os.path.join(args.output, f"dendrogram_{timestamp}.png"), dpi=300)
            
            # Also save the metric dataframes
            corr_pairs.to_csv(os.path.join(args.output, f"correlation_pairs_{timestamp}.csv"), index=False)
            cov_pairs.to_csv(os.path.join(args.output, f"covariance_pairs_{timestamp}.csv"), index=False)
            dist_pairs.to_csv(os.path.join(args.output, f"distance_pairs_{timestamp}.csv"), index=False)
            stable_pairs.to_csv(os.path.join(args.output, f"stable_pairs_{timestamp}.csv"), index=False)
            
            if 'beta_to_spy' in metrics:
                metrics['beta_to_spy'].to_csv(os.path.join(args.output, f"beta_to_spy_{timestamp}.csv"))
            
            print(f"\nResults saved to {args.output}")
        
        # Show plots
        plt.show()

if __name__ == "__main__":
    main()