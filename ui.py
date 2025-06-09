from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QComboBox, QLineEdit, QPushButton, QTableWidget, 
                           QTableWidgetItem, QHeaderView, QMessageBox, QApplication,
                           QGroupBox, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import config
import random
import websocket
import json
import threading
import time
from market_impact_models import AlmgrenChrissModel, AlmgrenChrissParameters, SlippageModel, MakerTakerModel
from performance_monitor import PerformanceMonitor

class WebSocketThread(QThread):
    data_received = pyqtSignal(dict)
    status_update = pyqtSignal(str)
    order_book_received = pyqtSignal(dict)
    
    def __init__(self, url, quantity=100):
        super().__init__()
        self.url = url
        self.quantity = quantity
        self.ws = None
        self.running = False
        self.last_update_time = time.time()
        
        # Initialize models
        self.slippage_model = SlippageModel()
        self.maker_taker_model = MakerTakerModel()
        
        # Initialize performance monitor
        self.performance_monitor = PerformanceMonitor()
        
        # Initialize Almgren-Chriss model with default parameters
        self.ac_params = AlmgrenChrissParameters(
            permanent_impact=0.15,
            temporary_impact=0.2,
            temporary_decay=0.6,
            risk_aversion=1.5,
            volatility=0.03,
            initial_price=0.0  # Will be updated with real price
        )
        self.ac_model = AlmgrenChrissModel(self.ac_params)
        
    def update_quantity(self, quantity):
        """Update the quantity for calculations."""
        try:
            self.quantity = float(quantity)
        except ValueError:
            self.quantity = 100  # Default to 100 if invalid input
        
    def calculate_slippage(self, order_book):
        """Calculate slippage using regression models."""
        try:
            if not order_book['asks'] or not order_book['bids']:
                return 0.0
            
            # Get predictions from both models
            linear_pred, quantile_pred = self.slippage_model.predict(order_book)
            
            # Use the more conservative estimate
            return max(linear_pred, quantile_pred)
            
        except Exception as e:
            print(f"Error calculating slippage: {str(e)}")
            return 0.0
    
    def calculate_fees(self, order_type, quantity, fee_tier):
        """Calculate trading fees based on fee tier and order type."""
        try:
            # Get fee rates from config
            fee_rates = config.FEE_TIERS.get("OKX", {}).get(fee_tier, {})
            if not fee_rates:
                return 0.0
            
            # Use maker fee for limit orders, taker fee for market orders
            fee_rate = fee_rates['maker'] if order_type == 'Limit' else fee_rates['taker']
            return float(quantity) * fee_rate
            
        except Exception as e:
            print(f"Error calculating fees: {str(e)}")
            return 0.0
    
    def calculate_market_impact(self, order_book, quantity):
        """Calculate market impact using Almgren-Chriss model."""
        try:
            if not order_book['asks'] or not order_book['bids']:
                return 0.0
            
            # Update initial price in model
            mid_price = (float(order_book['asks'][0][0]) + float(order_book['bids'][0][0])) / 2
            self.ac_params.initial_price = mid_price
            self.ac_model = AlmgrenChrissModel(self.ac_params)
            
            # Calculate optimal execution strategy
            strategy = self.ac_model.optimal_execution_strategy(
                total_quantity=float(quantity),
                time_horizon=1.0,  # 1 day
                num_periods=4      # 4 periods
            )
            
            return strategy['expected_shortfall_bps'] / 10000  # Convert to decimal
            
        except Exception as e:
            print(f"Error calculating market impact: {str(e)}")
            return 0.0
    
    def calculate_net_cost(self, slippage, fees, market_impact, quantity):
        """Calculate total cost including all components."""
        try:
            # Convert percentages to decimals
            slippage_decimal = slippage / 100
            market_impact_decimal = market_impact / 100
            
            # Calculate total cost
            total_cost = (slippage_decimal + market_impact_decimal) * float(quantity) + float(fees)
            return total_cost
            
        except Exception as e:
            print(f"Error calculating net cost: {str(e)}")
            return 0.0
    
    def calculate_maker_taker(self, order_book):
        """Calculate maker/taker proportion using logistic regression."""
        try:
            if not order_book['asks'] or not order_book['bids']:
                return 0.5  # Default to 50/50
            
            # Get prediction from model
            maker_proportion = self.maker_taker_model.predict(order_book)
            return maker_proportion * 100  # Convert to percentage
            
        except Exception as e:
            print(f"Error calculating maker/taker proportion: {str(e)}")
            return 50.0  # Default to 50/50
    
    def calculate_latency(self):
        """Calculate latency since last update."""
        current_time = time.time()
        latency = (current_time - self.last_update_time) * 1000  # Convert to milliseconds
        self.last_update_time = current_time
        return latency
    
    def run(self):
        self.running = True
        self.status_update.emit("Connecting to WebSocket...")
        self.ws = websocket.WebSocketApp(
            self.url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        self.ws.run_forever()
    
    def on_message(self, ws, message):
        try:
            # Start performance measurement
            self.performance_monitor.start_measurement()
            
            data = json.loads(message)
            print(f"Received WebSocket message: {data}")
            
            # GoQuant format: expects top-level asks and bids
            if 'asks' in data and 'bids' in data:
                if not data['asks'] or not data['bids']:
                    print("Skipping update - empty asks or bids")
                    return
                
                print(f"Processing order book update: {data}")
                
                # Record data processing start
                self.performance_monitor.record_data_processing()
                
                # Emit order book for UI table update
                self.order_book_received.emit(data)
                
                # Calculate metrics using current quantity
                slippage = self.calculate_slippage(data)
                fees = self.calculate_fees('Market', self.quantity, 'Tier 1 (0.08%/0.1%)')
                market_impact = self.calculate_market_impact(data, self.quantity)
                net_cost = self.calculate_net_cost(slippage, fees, market_impact, self.quantity)
                maker_taker = self.calculate_maker_taker(data)
                latency = self.calculate_latency()
                
                # Record UI update start
                self.performance_monitor.record_ui_update()
                
                try:
                    # Get latency metrics with error handling
                    stats = self.performance_monitor.get_statistics()
                    data_processing_latency = stats.get('data_processing', {}).get('mean', 0) * 1000  # Convert to ms
                    ui_update_latency = stats.get('ui_update', {}).get('mean', 0) * 1000  # Convert to ms
                except Exception as e:
                    print(f"Error getting latency metrics: {str(e)}")
                    data_processing_latency = 0
                    ui_update_latency = 0
                
                # Emit data for UI update
                self.data_received.emit({
                    'slippage': f"{slippage:.2f}%",
                    'fees': f"${fees:.2f}",
                    'market_impact': f"{market_impact:.2f}%",
                    'net_cost': f"${net_cost:.2f}",
                    'maker_taker': f"{maker_taker:.2f}%",
                    'latency': f"{latency:.0f}ms",
                    'data_processing_latency': f"{data_processing_latency:.0f}ms",
                    'ui_update_latency': f"{ui_update_latency:.0f}ms"
                })
                
                # End performance measurement
                self.performance_monitor.end_measurement()
                
                # Log performance statistics periodically
                if len(self.performance_monitor.metrics_history) % 100 == 0:
                    self.performance_monitor.log_statistics()
                
                print("Emitted data signal for UI update")
            else:
                print(f"Unexpected message format: {data}")
                
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            self.status_update.emit(f"Error: {str(e)}")
    
    def on_error(self, ws, error):
        print(f"WebSocket error: {error}")
        self.status_update.emit(f"WebSocket error: {str(error)}")
    
    def on_close(self, ws, close_status_code, close_msg):
        print(f"WebSocket connection closed: {close_status_code} - {close_msg}")
        self.status_update.emit("WebSocket connection closed")
    
    def on_open(self, ws):
        print("WebSocket connection established")
        self.status_update.emit("Connected to WebSocket")
        
    def stop(self):
        self.running = False
        if self.ws:
            self.ws.close()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Crypto Trade Simulator")
        self.setMinimumSize(1200, 800)
        
        # Initialize WebSocket thread
        self.ws_thread = None
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Create left panel for controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMaximumWidth(400)
        
        # Create right panel for output table
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        
        # Create input controls group
        input_group = QGroupBox("Input Controls")
        input_layout = QGridLayout()
        
        # Data Source
        input_layout.addWidget(QLabel("Data Source:"), 0, 0)
        self.data_source_combo = QComboBox()
        self.data_source_combo.addItems(["WebSocket"])
        input_layout.addWidget(self.data_source_combo, 0, 1)
        
        # WebSocket URL
        input_layout.addWidget(QLabel("WebSocket URL:"), 1, 0)
        self.ws_url_input = QLineEdit()
        self.ws_url_input.setText("wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/BTC-USDT-SWAP")
        input_layout.addWidget(self.ws_url_input, 1, 1)
        
        # Exchange
        input_layout.addWidget(QLabel("Exchange:"), 2, 0)
        self.exchange_combo = QComboBox()
        self.exchange_combo.addItems(["OKX"])
        input_layout.addWidget(self.exchange_combo, 2, 1)
        
        # Asset
        input_layout.addWidget(QLabel("Asset:"), 3, 0)
        self.asset_combo = QComboBox()
        self.asset_combo.addItems(["BTC-USDT-SWAP"])
        input_layout.addWidget(self.asset_combo, 3, 1)
        
        # Order Type
        input_layout.addWidget(QLabel("Order Type:"), 4, 0)
        self.order_type_combo = QComboBox()
        self.order_type_combo.addItems(["Market"])
        input_layout.addWidget(self.order_type_combo, 4, 1)
        
        # Quantity
        input_layout.addWidget(QLabel("Quantity (USD):"), 5, 0)
        self.quantity_input = QLineEdit()
        self.quantity_input.setText("1")
        self.quantity_input.textChanged.connect(self.on_quantity_changed)  # Connect signal
        input_layout.addWidget(self.quantity_input, 5, 1)
        
        # Volatility
        input_layout.addWidget(QLabel("Volatility (%):"), 6, 0)
        self.volatility_input = QLineEdit()
        self.volatility_input.setText("3.0")
        input_layout.addWidget(self.volatility_input, 6, 1)
        
        # Fee Tier
        input_layout.addWidget(QLabel("Fee Tier:"), 7, 0)
        self.fee_tier_combo = QComboBox()
        self.fee_tier_combo.addItems(["Tier 1 (0.1%)"])
        input_layout.addWidget(self.fee_tier_combo, 7, 1)
        
        # Status Label
        self.status_label = QLabel("Not connected")
        self.status_label.setStyleSheet("color: red;")
        input_layout.addWidget(self.status_label, 8, 0, 1, 2)
        
        input_group.setLayout(input_layout)
        left_layout.addWidget(input_group)
        
        # Add connect/disconnect buttons
        button_layout = QHBoxLayout()
        self.connect_button = QPushButton("Connect")
        self.connect_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.setStyleSheet("background-color: #f44336; color: white;")
        self.disconnect_button.setEnabled(False)
        
        button_layout.addWidget(self.connect_button)
        button_layout.addWidget(self.disconnect_button)
        left_layout.addLayout(button_layout)
        
        # Add stretch to push everything up
        left_layout.addStretch()
        
        # Create order book table
        order_book_group = QGroupBox("Order Book")
        order_book_layout = QVBoxLayout()
        self.order_book_table = QTableWidget()
        self.order_book_table.setColumnCount(3)
        self.order_book_table.setHorizontalHeaderLabels(["Price", "Size", "Total"])
        self.order_book_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        order_book_layout.addWidget(self.order_book_table)
        order_book_group.setLayout(order_book_layout)
        right_layout.addWidget(order_book_group)
        
        # Create output table
        output_group = QGroupBox("Metrics")
        output_layout = QVBoxLayout()
        self.output_table = QTableWidget()
        self.output_table.setColumnCount(2)
        self.output_table.setHorizontalHeaderLabels(["Parameter", "Value"])
        self.output_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        # Add output parameters
        output_params = [
            "Expected Slippage",
            "Expected Fees",
            "Expected Market Impact",
            "Net Cost",
            "Maker/Taker Proportion",
            "Internal Latency",
            "Data Processing Latency",
            "UI Update Latency"
        ]
        
        self.output_table.setRowCount(len(output_params))
        for i, param in enumerate(output_params):
            self.output_table.setItem(i, 0, QTableWidgetItem(param))
            self.output_table.setItem(i, 1, QTableWidgetItem("--"))
            
        output_layout.addWidget(self.output_table)
        output_group.setLayout(output_layout)
        right_layout.addWidget(output_group)
        
        # Connect signals
        self.connect_button.clicked.connect(self.on_connect)
        self.disconnect_button.clicked.connect(self.on_disconnect)
        
        # Initialize state
        self.is_connected = False
        self.last_update_time = time.time()
        
    def on_connect(self):
        try:
            # Create and start WebSocket thread
            self.ws_thread = WebSocketThread(self.ws_url_input.text(), self.quantity_input.text())
            self.ws_thread.data_received.connect(self.update_outputs)
            self.ws_thread.status_update.connect(self.update_status)
            self.ws_thread.order_book_received.connect(self.update_order_book)
            self.ws_thread.start()
            
            self.is_connected = True
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect: {str(e)}")
            self.update_status(f"Connection error: {str(e)}")
        
    def on_disconnect(self):
        if self.ws_thread:
            self.ws_thread.stop()
            self.ws_thread.wait()
            self.ws_thread = None
            
        self.is_connected = False
        self.connect_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)
        self.update_status("Disconnected")
        
        # Reset output values to --
        for i in range(self.output_table.rowCount()):
            self.output_table.setItem(i, 1, QTableWidgetItem("--"))
            
    def update_status(self, message):
        self.status_label.setText(message)
        if "error" in message.lower():
            self.status_label.setStyleSheet("color: red;")
        elif "connected" in message.lower():
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setStyleSheet("color: blue;")
            
    def update_outputs(self, data):
        if not data:
            return
            
        try:
            # Update output table with new data
            self.output_table.setItem(0, 1, QTableWidgetItem(f"{data['slippage']}%"))
            self.output_table.setItem(1, 1, QTableWidgetItem(f"${data['fees']}"))
            self.output_table.setItem(2, 1, QTableWidgetItem(f"{data['market_impact']}%"))
            self.output_table.setItem(3, 1, QTableWidgetItem(f"${data['net_cost']}"))
            self.output_table.setItem(4, 1, QTableWidgetItem(f"{data['maker_taker']}%"))
            self.output_table.setItem(5, 1, QTableWidgetItem(f"{data['latency']}ms"))
            self.output_table.setItem(6, 1, QTableWidgetItem(f"{data['data_processing_latency']}ms"))
            self.output_table.setItem(7, 1, QTableWidgetItem(f"{data['ui_update_latency']}ms"))
        except Exception as e:
            print(f"Error updating outputs: {str(e)}")
            
    def on_quantity_changed(self, text):
        """Handle quantity input changes."""
        if self.ws_thread and self.is_connected:
            try:
                quantity = float(text)
                self.ws_thread.update_quantity(quantity)
            except ValueError:
                # Invalid input, ignore
                pass
            
    def update_order_book(self, data):
        if not data or 'bids' not in data or 'asks' not in data:
            return
            
        # Update order book table
        self.order_book_table.setRowCount(0)
        
        # Add asks (sell orders)
        for price, size in data['asks']:
            price_f = float(price)
            size_f = float(size)
            row = self.order_book_table.rowCount()
            self.order_book_table.insertRow(row)
            self.order_book_table.setItem(row, 0, QTableWidgetItem(f"{price_f:.2f}"))
            self.order_book_table.setItem(row, 1, QTableWidgetItem(f"{size_f:.4f}"))
            self.order_book_table.setItem(row, 2, QTableWidgetItem(f"{price_f * size_f:.2f}"))
            
        # Add bids (buy orders)
        for price, size in data['bids']:
            price_f = float(price)
            size_f = float(size)
            row = self.order_book_table.rowCount()
            self.order_book_table.insertRow(row)
            self.order_book_table.setItem(row, 0, QTableWidgetItem(f"{price_f:.2f}"))
            self.order_book_table.setItem(row, 1, QTableWidgetItem(f"{size_f:.4f}"))
            self.order_book_table.setItem(row, 2, QTableWidgetItem(f"{price_f * size_f:.2f}"))
            
    def update_ui(self):
        # This method will be called periodically to update the UI
        pass 