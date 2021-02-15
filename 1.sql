CREATE TABLE miscs (day_margin integer, candle_thread_running boolean);

CREATE TABLE trd_portfolio (token integer, Market VARCHAR(255), Segment VARCHAR(255), Symbol VARCHAR(255), max_quantity integer, Direction VARCHAR(255), Orderid integer, Target_order varchar(10), Target_order_id integer, Positions integer, Tradable_quantity integer, LTP decimal(10, 4), Per_Unit_Cost decimal(10, 4), Quantity_multiplier decimal(10, 4), buy_brokerage decimal(10, 4), sell_brokerage decimal(10, 4), stt_ctt decimal(10, 4), buy_tran decimal(10, 4), sell_tran decimal(10, 4), gst decimal(10, 4), stamp decimal(10, 4), margin_multiplier decimal(10, 4), kite_exchange VARCHAR(255), buffer_quantity integer, round_value integer, Trade VARCHAR(255), tick_size decimal(10, 4), start_time VARCHAR(255), end_time VARCHAR(255), lower_circuit_limit decimal(10, 4), upper_circuit_limit decimal(10, 4), Target_amount decimal(10, 4), Options_lot_size integer);

CREATE TABLE RBLBANK_ohlc_final_1min (Symbol VARCHAR(255), Time VARCHAR(255),Open integer,High integer,Low integer,Close integer,TR integer,ATR integer,SMA integer,TMA integer);

CREATE TABLE ICICIBANK_ohlc_final_1min (Symbol VARCHAR(255), Time VARCHAR(255),Open integer,High integer,Low integer,Close integer,TR integer,ATR integer,SMA integer,TMA integer);

SHOW DATABASES;

USE testdb;
SHOW TABLES;

describe icicibank_renko_final;



INSERT INTO trd_portfolio (OHLC_Thread_Running) values ("NO");

select * from icicibank_ohlc_final_1min order by time desc limit 20 ;
select * from icicibank_renko_final order by time desc limit 20;
select * from order_updates;

delete from rblbank_renko_final;

drop table rblbank_renko_final;

CREATE TABLE RBLBANK_HA_Final (Symbol VARCHAR(255), Time VARCHAR(255),Open decimal(10,4),High decimal(10,4),Low decimal(10,4),Close decimal(10,4),TR decimal(10,4),ATR decimal(10,4),SMA decimal(10,4),TMA decimal(10,4));

INSERT INTO USDINR20OCTFUT_ohlc_final_1min (Symbol, Time, Open, High, Low, Close, TR, ATR, SMA, TMA) values ("USDINR20OCTFUT","2020-10-16 16:08:00",778453.3975,778485.3975,778748.3975,758453.3975,0.0,0,0,0);

alter table usdinr20octfut_renko_final drop ATR;
alter table icicibank_renko_final modify column TMA float;
alter table rblbank_renko_final add Time varchar(20) after TMA;

create table ORDER_UPDATES (Symbol VARCHAR(255), Ins_Token integer, Ord_Status VARCHAR(255), Trans_type VARCHAR(255), Avg_Price decimal(10,4), Quantity integer);

/*icicibank_ha_final
icicibank_ohlc_final_1min
icicibank_renko_final
miscs
order_updates
processed_orders
rblbank_ha_final
rblbank_ohlc_final_1min
rblbank_renko_final
trd_portfolio
usdinr20octfut_ha_final
usdinr20octfut_ohlc_final_1min
usdinr20octfut_renko_final
 */

select * from icicibank_ha_final order by time desc limit 1;

create table Processed_orders (OrderId integer);

select count(*) from order_updates;

select * from icicibank_ohlc_final_1min;

delete from icicibank_renko_final;

insert into trd_portfolio values (1270529, "NSE", "Equity", "ICICIBANK", 100, "", 0, "", 0, 0, 0, 0, 1050, 1, 0.0003, 0.0003, 0.00025, 0.0000325, 0.0000325, 0.18, 0.00003, 5, "kite.EXCHANGE_NSE", 5, 2, "YES", .05, "9, 29, 10", "15, 15, 10", 0, 0, 0, 0);

update trd_portfolio set OHLC_Thread_Running = "NO";

INSERT INTO RBLBANK_ohlc_final_1min values ("RBLBANK","2020-12-23 10:59:00",216.35,216.45,216.1,216.25,0.35,0,0,0);

show variables like '%timeout%';

SET @@GLOBAL.net_write_timeout=300;

select * from order_updates;