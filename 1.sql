CREATE TABLE miscs (day_margin integer, candle_thread_running boolean, 

CREATE TABLE trd_portfolio (token integer, Market VARCHAR(255), Segment VARCHAR(255), Symbol VARCHAR(255), max_quantity integer, Direction VARCHAR(255), Orderid integer, Target_order integer, Target_order_id, Positions integer, Tradable_quantity integer, LTP integer, Per_Unit_Cost integer, Quantity_multiplier integer, buy_brokerage integer, sell_brokerage integer, stt_ctt integer, buy_tran integer, sell_tran integer, gst integer, stamp integer, margin_multiplier integer, kite_exchange VARCHAR(255), buffer_quantity integer, round_value integer, Trade VARCHAR(255), tick_size integer, start_time, end_time, lower_circuit_limit integer, upper_circuit_limit integer, Target_amount integer, Options_lot_size integer

CREATE TABLE RBLBANK_ohlc_final_1min (Symbol VARCHAR(255), Time VARCHAR(255),Open integer,High integer,Low integer,Close integer,TR integer,ATR integer,SMA integer,TMA integer)

CREATE TABLE ICICIBANK_ohlc_final_1min (Symbol VARCHAR(255), Time VARCHAR(255),Open integer,High integer,Low integer,Close integer,TR integer,ATR integer,SMA integer,TMA integer)

SHOW DATABASES;

USE testdb;
SHOW TABLES;

describe icicibank_ohlc_final_1min;

INSERT INTO USDINR20OCTFUT_ohlc_final_1min values ("ICICIBANK", "14:41:00", 172, 172, 172, 172, 0, 0, 0, 0);

select * from RBLBANK_ohlc_final_1min;
select * from RBLBANK_ohlc_final_1min;
select * from USDINR20OCTFUT_ohlc_final_1min;

CREATE TABLE USDINR20OCTFUT_ohlc_final_1min (Symbol VARCHAR(255), Time VARCHAR(255),Open integer,High integer,Low integer,Close integer,TR integer,ATR integer,SMA integer,TMA integer);

INSERT INTO USDINR20OCTFUT_ohlc_final_1min (Symbol, Time, Open, High, Low, Close, TR, ATR, SMA, TMA) values ("USDINR20OCTFUT","2020-10-16 16:08:00",73.3975,73.3975,73.3975,73.3975,0.0,0,0,0)