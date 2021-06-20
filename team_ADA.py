class Strategy():
    # option setting needed
    def __setitem__(self, key, value):
        self.options[key] = value

    # option setting needed
    def __getitem__(self, key):
        return self.options.get(key, '')

    def __init__(self):
        # strategy property needed
        self.subscribedBooks = {
            'Binance': {
                'pairs': ['ADA-USDT'],
            },
        }

        # seconds for broker to call trade()
        # do not set the frequency below 60 sec.
        # 10 * 60 for 10 mins
        self.period = 30 * 60 # target at 30 minutes kline
        self.options = {}
        self.fee = 0.001
        self.money = 142500

        # Strategy paramters
        self.buy_part = 0.08

        # Buy linked list: [price, amount]
        self.buyin = []

        # trend record: record the slope of history 
        self.his_slope = []

        # History average
        self.his_avg = []

        # Last slope valley and peak: the marked index of self.his_slope
        self.last_valley = 0
        self.last_peak = 0
        self.sell_pair = []
	
    # Return the min buyin price of index
    def min_buyin(self):
        min_index = 0
        min_value = 100000000000 # Ceiling number
        for i in range(len(self.buyin)-1):
            if (self.buyin[i][0] < min_value):
                min_value = self.buyin[i][0]
                min_index = i
        
        return int(min_index)
            


    # called every self.period
    def trade(self, information):
        # for single pair strategy, user can choose which exchange/pair to use when launch, get current exchange/pair from information
        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        
        #pd_row = information['candles'][exchange][pair][0]

        # Calculate average price: (high + low) / 2
        average = (information['candles'][exchange][pair][0]['high'] + information['candles'][exchange][pair][0]['low']) / 2
        self.his_avg.append(average)

        # Slope: (Avg2- Avg1) / Avg1
        if (len(self.his_avg) < 2):
            return []
        else:
            slope = (self.his_avg[-1] - self.his_avg[-2]) / self.his_avg[-2]
            self.his_slope.append(slope)
            # Log("Slope: " +  str(slope))
            len_slope = len(self.his_slope)
            # If price is decreasing
            if (slope < 0):
                # Check if there is a temporally valley of slope
                if (self.last_valley != 0):
                    # If the valley is the last kline
                    if (self.last_valley == (len_slope - 2)):
                        
                        # Slope drops more strongly
                        #Log("self.last_valley: " + str(self.last_valley))
                        if (slope <= self.his_slope[self.last_valley]):
                            # Update new last_valley's index & do nothing
                            self.last_valley = (len_slope - 1)
                            return []
                        # Slope drop slower <- It's time to buy some ????
                        # TOFIX: THERE MANY A TEMP SLOWDOWN BUT KEEP DROPPING 
                        else:
                            # BUY in some crypto
                            #print(pd_row['Open time'], ': Buy crpyto at $', pd_row['Open'])
                            # Buy at Close price
                            #Log("BUY SOME ADA !!!!!!!!")
                            # If there's no money to buy

                            buyin_price = information['candles'][exchange][pair][0]['close']
                            buyin_amount = float(self.money * self.buy_part / information['candles'][exchange][pair][0]['close'])
                            #Log("BUY: buyin_price: " + str(buyin_price) + 'buyin_amount: ' + str(buyin_amount))
                            self.buyin.append( [ information['candles'][exchange][pair][0]['close'] , buyin_amount ] )

                            
                            return [
                                {
                                    'exchange': exchange,
                                    'amount': float(buyin_amount),
                                    'price': -1,
                                    'type': 'MARKET',
                                    'pair': pair,
                                }
                            ]
                    
                    # Climb up a peak and then drop
                    else:
                        self.last_valley = (len_slope - 1)
                        
                        """
                        if (slope <= self.his_slope[self.last_valley]):
                            # Update new last_valley's index & do nothing
                            self.last_valley = len(self.his_slope) - 1
                            return []
                        else:
                        """
                        return []                       
                        
                # Update last_valley and not do any operations   
                else:
                    self.last_valley = (len_slope - 1)
                    return []
                
            # If price is increasing 
            elif (slope > 0):
                if (self.last_peak != 0):
                    if (self.last_peak == (len_slope - 2)):
                        if (slope >= self.his_slope[self.last_peak]):
                            self.last_peak = len_slope - 1
                            return []
                        else:
                            # SELL some crypto
                            #print(pd_row['Open time'], ': Sell crypto at $', pd_row['Open'])
                            if (len(self.buyin) < 1):
                                return []
                            # Only sell when the price is higher than the buyin price
                            sell_price = information['candles'][exchange][pair][0]['close']
                            min_index = self.min_buyin()
                            #Log("min_index: " + str(min_index))
                            min_value = self.buyin[min_index][0]
                            min_amount = self.buyin[min_index][1]
                            #Log("SELL: min_value: " + str(min_value) + " min_amount: " + str(min_amount))

                            if (sell_price > (min_value*1.003)):
                                #Log('SELL SOME ADA!!!!')
                                self.sell_pair.append([sell_price, min_value])
                                self.buyin.remove([min_value, min_amount])
                                return [
                                    {
                                        'exchange': exchange,
                                        'amount': (-1) * min_amount ,
                                        'price': -1,
                                        'type': 'MARKET',
                                        'pair': pair,
                                    }
                                ]
                            
                            else:
                                return []
                    
                    # Drop and climb up again
                    else:
                        self.last_peak = len_slope - 1
                        return []
                else:
                    self.last_peak = len_slope - 1
                    return []
                        
                        
                        
            
            
            # If price is not moving.
            else:
                # remove this element and do nothing
                del self.his_slope[-1]
                return []
    
    def on_order_state_change(self, order):
        Log("on order state change message: " + str(order) + " order price: " + str(order["price"]))
