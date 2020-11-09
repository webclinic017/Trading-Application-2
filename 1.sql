CREATE TABLE miscs (day_margin integer, candle_thread_running boolean);

CREATE TABLE trd_portfolio (token integer, Market VARCHAR(255), Segment VARCHAR(255), Symbol VARCHAR(255), max_quantity integer, Direction VARCHAR(255), Orderid integer, Target_order integer, Target_order_id, Positions integer, Tradable_quantity integer, LTP integer, Per_Unit_Cost integer, Quantity_multiplier integer, buy_brokerage integer, sell_brokerage integer, stt_ctt integer, buy_tran integer, sell_tran integer, gst integer, stamp integer, margin_multiplier integer, kite_exchange VARCHAR(255), buffer_quantity integer, round_value integer, Trade VARCHAR(255), tick_size integer, start_time, end_time, lower_circuit_limit integer, upper_circuit_limit integer, Target_amount integer, Options_lot_size integer)

CREATE TABLE RBLBANK_ohlc_final_1min (Symbol VARCHAR(255), Time VARCHAR(255),Open integer,High integer,Low integer,Close integer,TR integer,ATR integer,SMA integer,TMA integer)

CREATE TABLE ICICIBANK_ohlc_final_1min (Symbol VARCHAR(255), Time VARCHAR(255),Open integer,High integer,Low integer,Close integer,TR integer,ATR integer,SMA integer,TMA integer)

SHOW DATABASES;

USE testdb;
SHOW TABLES;

describe order_updates;

INSERT INTO USDINR20OCTFUT_ohlc_final_1min values ("ICICIBANK", "14:41:00", 172, 172, 172, 172, 0, 0, 0, 0);

select * from RBLBANK_ohlc_final_1min;
select * from RBLBANK_ohlc_final_1min;
select * from usdinr20octfut_ohlc_final_1min;

drop table rblbank_renko_final;

CREATE TABLE RBLBANK_HA_Final (Symbol VARCHAR(255), Time VARCHAR(255),Open decimal(10,4),High decimal(10,4),Low decimal(10,4),Close decimal(10,4),TR decimal(10,4),ATR decimal(10,4),SMA decimal(10,4),TMA decimal(10,4));

INSERT INTO USDINR20OCTFUT_ohlc_final_1min (Symbol, Time, Open, High, Low, Close, TR, ATR, SMA, TMA) values ("USDINR20OCTFUT","2020-10-16 16:08:00",778453.3975,778485.3975,778748.3975,758453.3975,0.0,0,0,0);

alter table usdinr20octfut_renko_final drop ATR;

alter table usdinr20octfut_renko_final add Direction varchar(255) after Close;

create table ORDER_UPDATES (Symbol VARCHAR(255), Ins_Token integer, Ord_Status VARCHAR(255), Trans_type VARCHAR(255), Avg_Price decimal(10,4), Quantity integer);

/*icicibank_ha_final
icicibank_ohlc_final_1min
icicibank_renko_final
rblbank_ha_final
rblbank_ohlc_final_1min
rblbank_renko_final
usdinr20octfut_ha_final
usdinr20octfut_ohlc_final_1min
usdinr20octfut_renko_final*/

select * from rblbank_renko_final;

create table Processed_orders (OrderId integer);

select count(*) from order_updates;

select * from order_updates limit 1;

delete from rblbank_renko_final limit 1;