# Soccer Predictor API Setup Summary

## Project Overview
This is a **SoccerPredictor** application that uses machine learning to predict outcomes of Premier League matches. The application focuses on predicting win-or-draw or loss scenarios (corresponding to betting on double chance) and uses neural networks with time series classification.

## What Was Accomplished

### 1. Environment Setup
- ✅ Created Python virtual environment
- ✅ Installed required system packages (python3.13-venv, python3-pip)
- ✅ Updated dependencies to modern, compatible versions

### 2. Dependency Installation
Successfully installed modern versions of:
- **dash** (3.1.1) - Web framework for the visualization interface
- **plotly** (6.2.0) - Interactive plotting library
- **pandas** (2.3.1) - Data manipulation and analysis
- **numpy** (2.3.1) - Numerical computing
- **matplotlib** (3.10.3) - Plotting library
- **scikit-learn** (1.7.1) - Machine learning library
- **PyYAML** (6.0.2) - YAML parser
- **Flask** (3.1.1) - Web server framework

### 3. Code Compatibility Fixes
Fixed multiple compatibility issues with modern Python/Pandas:
- ✅ Updated pandas options (`display.max_colwidth` from `-1` to `None`)
- ✅ Fixed Dash imports (moved from separate modules to main `dash` module)
- ✅ Replaced deprecated pandas `.append()` with `pd.concat()`
- ✅ Fixed pandas Series `.iloc[0]` usage to prevent FutureWarnings
- ✅ Updated Dash server method from `app.run_server()` to `app.run()`

### 4. Web Application Running
- ✅ **Successfully started the Dash web application**
- ✅ **Server is running on 0.0.0.0:8050** (accessible from all network interfaces)
- ✅ **Web interface is responding to HTTP requests** (confirmed with curl)
- ✅ Application processes the available model data (`KIIY_2019-11-26T02-13-11_400`)

## Available Data and Results

The application successfully loaded and processed prediction data showing:

### Test Dataset Results:
- **30 matches** to bet on
- **100% accuracy** (30 wins, 0 losses)
- **1133% net gain**
- **37.8% ROI**

### Prediction Dataset Results:
- **4 matches** to bet on
- **100% accuracy** (4 wins, 0 losses)
- **213% net gain**
- **53.3% ROI**

## API Endpoints Available

The Dash web application provides:

1. **Main Dashboard** - `http://localhost:8050/`
   - Interactive visualization of predictions
   - Match prediction tables
   - Performance statistics
   - Betting recommendations

2. **Interactive Features**:
   - Model performance visualization
   - Betting analysis with configurable odds thresholds
   - Historical prediction accuracy

## How to Access

1. **Local Access**: `http://localhost:8050`
2. **Network Access**: `http://[server-ip]:8050`

The server is configured to accept connections from all network interfaces (`0.0.0.0`).

## Model Information

- **Model Name**: KIIY_2019-11-26T02-13-11_400
- **Training Period**: Data from 2017-2018 Premier League season
- **Prediction Method**: Neural network time series classification
- **Target**: Win-or-draw vs Loss predictions for betting scenarios

## Technical Architecture

- **Backend**: Python with pandas, numpy, scikit-learn
- **Web Framework**: Dash (built on Flask)
- **Visualization**: Plotly for interactive charts
- **Data Processing**: Pandas for data manipulation and analysis
- **Model Storage**: Pickle files with prediction data

## Next Steps

The APIs are now running and connected. Users can:
1. Access the web interface at http://localhost:8050
2. View interactive prediction visualizations
3. Analyze betting recommendations
4. Review model performance metrics
5. Explore historical prediction accuracy

The application demonstrates sophisticated sports betting analytics with machine learning predictions and provides a comprehensive web interface for data exploration.