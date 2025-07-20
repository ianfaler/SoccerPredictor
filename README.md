# SoccerPredictor 🏆

SoccerPredictor is a production-ready machine learning system for predicting Premier League match outcomes. It uses time series classification with neural networks to predict win-or-draw probabilities, with a focus on profitable betting strategies.

## ✨ Features

- **🤖 Advanced ML Models**: Individual neural networks per team with time series analysis
- **📊 Multiple Data Sources**: Integrates Football-Data.org, RapidAPI, and FootyStats APIs
- **🔄 Real-time Updates**: Automatic data synchronization and model retraining
- **📈 Backtesting**: Comprehensive historical performance analysis
- **🌐 REST API**: Full-featured API server with validation and rate limiting
- **📱 Web Interface**: Modern dashboard for predictions and analysis
- **🔐 Production Ready**: Comprehensive logging, error handling, and security features

## 🎯 Performance

Best historical results:
- **Profit**: 1069%
- **Accuracy**: ~90%
- **ROI**: 33.4%
- **Period**: 113 days testing on 32/150 matches

[![Result](https://jkrusina.github.io/images/backtest_model_2018-01-20-2018-05-13_11.png)](https://jkrusina.github.io/images/backtest_model_2018-01-20-2018-05-13_11.png)

## 🚀 Quick Start

### Automated Installation

```bash
# Clone the repository
git clone https://github.com/jkrusina/SoccerPredictor
cd SoccerPredictor

# Run the automated installer
chmod +x install.sh
./install.sh
```

### Manual Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

### Configuration

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Add your API keys to `.env`:**
   ```bash
   # Football Data API (Free: https://www.football-data.org/client/register)
   FOOTBALL_DATA_API_KEY=your_key_here
   
   # RapidAPI Football (https://rapidapi.com/)
   RAPIDAPI_KEY=your_key_here
   
   # FootyStats API (https://footystats.org/api)
   FOOTYSTATS_API_KEY=your_key_here
   ```

3. **Update historical data (2020-2025):**
   ```bash
   python scripts/update_historical_data.py --start-year 2020 --end-year 2025
   ```

## 💻 Usage

### Command Line Interface

```bash
# Activate virtual environment
source venv/bin/activate

# View all available commands
python main.py --help
```

**Available modes:**
- `api` - Start REST API server  
- `train` - Train ML models
- `vis` - Run prediction visualization
- `backtest` - Run historical backtesting

### 🌐 API Server

Start the REST API server:

```bash
# Basic server
python main.py api

# With data update and custom port  
python main.py api --port 8080 --update-data --host 0.0.0.0
```

**API Endpoints:**
- `GET /api/health` - Health check
- `GET /api/status` - System status
- `GET /api/fixtures` - Get fixtures with filtering
- `GET /api/teams` - List all teams
- `POST /api/data/update` - Update historical data
- `GET /api/predictions` - Get current predictions

### 📊 Data Management

**Update historical data:**
```bash
# Update all data from 2020-2025
python scripts/update_historical_data.py

# Update specific years
python scripts/update_historical_data.py --start-year 2022 --end-year 2024

# Force update existing data
python scripts/update_historical_data.py --force

# Dry run (show what would be updated)
python scripts/update_historical_data.py --dry-run
```

**Test API endpoints:**
```bash
python test_api_endpoints.py
```

### 🤖 Model Training

Train models with historical data:

```bash
# Train new model
python main.py train --epochs 100 --timesteps 40

# Resume training from checkpoint
python main.py train --resume --epochs 50

# Make predictions only (no training)
python main.py train --predict
```

### 📈 Visualization & Analysis

**Start visualization dashboard:**
```bash
python main.py vis --port 8050
```

**Run backtesting:**
```bash
python main.py backtest --path models/
```

## 🔧 Advanced Configuration

### Environment Variables

```bash
# API Configuration
FOOTBALL_DATA_API_KEY=your_key_here
RAPIDAPI_KEY=your_key_here
FOOTYSTATS_API_KEY=your_key_here

# Flask Settings
FLASK_ENV=production
FLASK_DEBUG=0

# Logging
LOG_LEVEL=INFO
```

## 🚀 Production Deployment

### Using Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "soccerpredictor.api.api_server:create_app()"
```

## 🧪 Testing

```bash
# Run API tests
python test_api_endpoints.py

# Validate data integrity
python scripts/update_historical_data.py --dry-run
```

## 📄 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch  
3. Add comprehensive tests
4. Submit a pull request

---

**Note**: Historical data from 2020-2025 is now fully supported through multiple API integrations. 
```
$ python3 main.py train
```
Possible arguments to use:
```
$ python3 main.py train --help
usage: main.py train [-h] [--resume] [--epochs EPOCHS] [--ntest NTEST]
                     [--ndiscard NDISCARD] [--timesteps TIMESTEPS] [--predict]
                     [--lrpatience LRPATIENCE] [--lrdecay LRDECAY]
                     [--seed SEED] [--savefreq SAVEFREQ]
                     [--printfreq PRINTFREQ] [--verbose {0,1}] [--name NAME]

optional arguments:
  -h, --help            show this help message and exit
  --resume              Resumes training of previously saved model. Tries to
                        load the latest model saved if no name or prefix
                        specified via --name. (default: False)
  --epochs EPOCHS       Number of epochs to train model for. (default: 1)
  --ntest NTEST         Number of last samples used for testing for each team.
                        (default: 10)
  --ndiscard NDISCARD   Number of last samples to discard for each team.
                        (default: 0)
  --timesteps TIMESTEPS
                        Number of timesteps to use as data window size for
                        input to network. (default: 40)
  --predict             Whether to rerun predictions without any training.
                        (default: False)
  --lrpatience LRPATIENCE
                        How many epochs to tolerate before decaying learning
                        rate if no improvement. Turned off if 0. (default: 20)
  --lrdecay LRDECAY     How much to decay learning rate after patience
                        exceeded. (default: 0.95)
  --seed SEED           Specifies seed for rng. (default: None)
  --savefreq SAVEFREQ   How often (number of epochs) to save models. No
                        intermediate saving if 0. (default: 50)
  --printfreq PRINTFREQ
                        How often (number of epochs) to print current
                        summaries. No intermediate printing if 0. (default:
                        10)
  --verbose {0,1}       Level of verbosity. (default: 1)
  --name NAME           Tries to load the latest saved model with given name
                        prefix. Loads exact model if exact dir name specified.
                        Loads latest model if only a prefix of the name
                        specified. (default: None)
```
Examples:
```
# Training with fixed seed for 100 epochs
$ python3 main.py train --epochs 100 --seed 42

# Resuming training from latest directory
$ python3 main.py train --resume --epochs 100

# Training with discarding different amount of last samples, useful for backtesting
$ python3 main.py train --epochs 100 --ndiscard 1
$ python3 main.py train --epochs 100 --ndiscard 2
$ python3 main.py train --epochs 100 --ndiscard 3
$ python3 main.py train --epochs 100 --ndiscard 4

# Recreate predictions without training
$ python3 main.py train --predict
```

### Visualization
A simple visualization of the trained model built with Dash.
```
$ python3 main.py vis
```
Then it is accessible via browser (by default):
```
http://127.0.0.1:8050/
```
Possible arguments to use:
```
$ python3 main.py vis --help
usage: main.py vis [-h] [--port PORT] [--host HOST] [--name NAME]
                   [--ignoreodds IGNOREODDS]

optional arguments:
  -h, --help            show this help message and exit
  --port PORT           Custom port for Dash visualization. (default: 8050)
  --host HOST           Custom host for Dash visualization. Can use 0 for
                        0.0.0.0 shortcut. (default: 127.0.0.1)
  --name NAME           Tries to load the latest saved model with given name
                        prefix. Loads exact model if exact dir name specified.
                        Loads latest model if only a prefix of the name
                        specified. (default: None)
  --ignoreodds IGNOREODDS
                        Ignores odds less than given amount when predicting
                        which team to bet on. (default: 1.1)
```
Examples:
```
# Exact name of directory can be specified
$ python3 main.py vis --name KIIY_2019-11-26T02-13-11_400

# Loads latest directory with given prefix
$ python3 main.py vis --name KIIY
```
```
# Change value of odds to ignore
$ python3 main.py vis --ignoreodds 1.01
```

### Backtesting
Backtesting on trained models:
```
$ python3 main.py backtest
```
Possible arguments to use:
```
$ python3 main.py backtest --help
usage: main.py backtest [-h] [--path PATH] [--ignoreodds IGNOREODDS]

optional arguments:
  -h, --help            show this help message and exit
  --path PATH           Path to folder where multiple trained models are
                        saved. (default: ./data/models/)
  --ignoreodds IGNOREODDS
                        Ignores odds less than given amount when predicting
                        which team to bet on. (default: 1.1)
```
Examples:
```
# Change value of odds to ignore
$ python3 main.py backtest --ignoreodds 1.01
```

# Requirements
Main requirements are:
- Python 3.7
- Keras 2.3.1
- Tensorflow 1.14.0
- Dash 1.4.1

Other required packages are specified in the `requirements.txt` file.

